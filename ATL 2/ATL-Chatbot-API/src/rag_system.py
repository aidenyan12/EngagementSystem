#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
RAG System for ATL Chatbot

This module provides Retrieval-Augmented Generation capabilities by:
1. Scraping information from the ATL website
2. Storing information in a vector database
3. Providing retrieval capabilities for the chatbot
"""

import os
import sys
import json
import time
import logging
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
from datetime import datetime
from datetime import datetime

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logger = logging.getLogger("rag_system")

class WebScraper:
    """Scrape information from the ATL website"""
    
    def __init__(self, base_url: str = "https://www.atlab.hku.hk/"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Add SSL handling for problematic certificates
        self.session.verify = True  # Try with verification first
    
    def scrape_page(self, url: str) -> Dict[str, Any]:
        """Scrape a single page and extract structured information"""
        try:
            # First try with SSL verification
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            page_info = {
                'url': url,
                'title': self._extract_title(soup),
                'content': self._extract_content(soup),
                'metadata': self._extract_metadata(soup),
                'scraped_at': datetime.now().isoformat()
            }
            
            return page_info
            
        except requests.exceptions.SSLError as ssl_e:
            logger.warning(f"SSL Error for {url}, trying without verification: {ssl_e}")
            try:
                # Retry without SSL verification for problematic certificates
                response = self.session.get(url, timeout=10, verify=False)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                page_info = {
                    'url': url,
                    'title': self._extract_title(soup),
                    'content': self._extract_content(soup),
                    'metadata': self._extract_metadata(soup),
                    'scraped_at': datetime.now().isoformat(),
                    'ssl_warning': 'Scraped without SSL verification'
                }
                return page_info
            except Exception as retry_e:
                logger.error(f"Error scraping {url} even without SSL verification: {retry_e}")
                return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from the page"""
        for script in soup(["script", "style"]):
            script.decompose()
        
        content = ""
        main_selectors = ['main', '.main-content', '.content', '#content', '.page-content']
        
        for selector in main_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                content = main_content.get_text(separator=' ', strip=True)
                break
        
        if not content:
            content = soup.get_text(separator=' ', strip=True)
        
        content = re.sub(r'\s+', ' ', content)
        content = re.sub(r'\n+', '\n', content)
        
        return content.strip()
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from the page"""
        metadata = {}
        
        meta_tags = soup.find_all('meta')
        for meta in meta_tags:
            name = meta.get('name') or meta.get('property')
            content = meta.get('content')
            if name and content:
                metadata[name] = content
        
        headings = []
        for i in range(1, 7):
            for heading in soup.find_all(f'h{i}'):
                headings.append({
                    'level': i,
                    'text': heading.get_text().strip()
                })
        metadata['headings'] = headings
        
        links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text().strip()
            if href and text:
                links.append({
                    'url': urljoin(self.base_url, href),
                    'text': text
                })
        metadata['links'] = links
        
        return metadata
    
    def scrape_site(self, max_pages: int = 30) -> List[Dict[str, Any]]:
        """Scrape multiple pages from the ATL website"""
        scraped_pages = []
        visited_urls = set()
        urls_to_visit = [self.base_url]
        
        while urls_to_visit and len(scraped_pages) < max_pages:
            url = urls_to_visit.pop(0)
            
            if url in visited_urls:
                continue
            
            visited_urls.add(url)
            logger.info(f"Scraping: {url}")
            
            page_info = self.scrape_page(url)
            if page_info:
                scraped_pages.append(page_info)
                
                if 'metadata' in page_info and 'links' in page_info['metadata']:
                    for link in page_info['metadata']['links']:
                        link_url = link['url']
                        if (urlparse(link_url).netloc == urlparse(self.base_url).netloc and 
                            link_url not in visited_urls and 
                            link_url not in urls_to_visit):
                            urls_to_visit.append(link_url)
            
            time.sleep(1)
        
        return scraped_pages

    def scrape_site_with_additional_urls(self, additional_urls: List[str] = None, max_pages: int = 30) -> List[Dict[str, Any]]:
        """Scrape multiple pages including additional specific URLs"""
        scraped_pages = []
        visited_urls = set()
        urls_to_visit = [self.base_url]
        
        # Add additional URLs to the queue
        if additional_urls:
            urls_to_visit.extend(additional_urls)
        
        while urls_to_visit and len(scraped_pages) < max_pages:
            url = urls_to_visit.pop(0)
            
            if url in visited_urls:
                continue
            
            visited_urls.add(url)
            logger.info(f"Scraping: {url}")
            
            page_info = self.scrape_page(url)
            if page_info:
                scraped_pages.append(page_info)
                
                # Only auto-discover links from the base domain
                if urlparse(url).netloc == urlparse(self.base_url).netloc:
                    if 'metadata' in page_info and 'links' in page_info['metadata']:
                        for link in page_info['metadata']['links']:
                            link_url = link['url']
                            if (urlparse(link_url).netloc == urlparse(self.base_url).netloc and 
                                link_url not in visited_urls and 
                                link_url not in urls_to_visit):
                                urls_to_visit.append(link_url)
            
            time.sleep(1)
        
        return scraped_pages

    def load_url_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load URL configuration from JSON file"""
        if config_path is None:
            config_path = os.path.join(BASE_DIR, "data", "rag_urls.json")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"URL config file not found: {config_path}")
            return {}
        except Exception as e:
            logger.error(f"Error loading URL config: {e}")
            return {}
    
    def scrape_from_config(self, config_path: str = None) -> List[Dict[str, Any]]:
        """Scrape URLs based on configuration file"""
        config = self.load_url_config(config_path)
        
        if not config:
            return self.scrape_site()
        
        # Update base URL if specified in config
        if 'base_url' in config:
            self.base_url = config['base_url']
        
        # Get scraping settings
        settings = config.get('scraping_settings', {})
        max_pages = settings.get('max_pages', 30)
        delay = settings.get('delay_seconds', 1)
        
        # Get additional URLs
        additional_urls = config.get('additional_urls', [])
        
        scraped_pages = []
        visited_urls = set()
        urls_to_visit = [self.base_url] + additional_urls
        
        while urls_to_visit and len(scraped_pages) < max_pages:
            url = urls_to_visit.pop(0)
            
            if url in visited_urls:
                continue
            
            visited_urls.add(url)
            logger.info(f"Scraping: {url}")
            
            page_info = self.scrape_page(url)
            if page_info:
                scraped_pages.append(page_info)
                
                # Auto-discover links based on allowed domains
                external_domains = config.get('external_domains', [])
                current_domain = urlparse(url).netloc
                base_domain = urlparse(self.base_url).netloc
                
                if current_domain == base_domain or current_domain in external_domains:
                    if 'metadata' in page_info and 'links' in page_info['metadata']:
                        for link in page_info['metadata']['links']:
                            link_url = link['url']
                            link_domain = urlparse(link_url).netloc
                            
                            if ((link_domain == base_domain or link_domain in external_domains) and 
                                link_url not in visited_urls and 
                                link_url not in urls_to_visit):
                                urls_to_visit.append(link_url)
            
            time.sleep(delay)
        
        return scraped_pages

class InformationManager:
    """Manage information storage and retrieval"""
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = os.path.join(BASE_DIR, "data", "rag_data")
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.scraped_data_file = os.path.join(self.data_dir, "scraped_data.json")
        self.chunks_file = os.path.join(self.data_dir, "chunks.json")
        self.metadata_file = os.path.join(self.data_dir, "metadata.json")
    
    def save_scraped_data(self, scraped_pages: List[Dict[str, Any]]):
        """Save scraped data to file"""
        with open(self.scraped_data_file, 'w', encoding='utf-8') as f:
            json.dump(scraped_pages, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(scraped_pages)} scraped pages")
    
    def load_scraped_data(self) -> List[Dict[str, Any]]:
        """Load scraped data from file"""
        if os.path.exists(self.scraped_data_file):
            with open(self.scraped_data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def create_chunks(self, scraped_pages: List[Dict[str, Any]], chunk_size: int = 1000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Create chunks from scraped content for better retrieval"""
        chunks = []
        
        for page in scraped_pages:
            content = page.get('content', '')
            if not content:
                continue
            
            words = content.split()
            for i in range(0, len(words), chunk_size - overlap):
                chunk_words = words[i:i + chunk_size]
                chunk_text = ' '.join(chunk_words)
                
                if len(chunk_text.strip()) > 100:
                    chunk = {
                        'id': f"{page['url']}_{i}",
                        'url': page['url'],
                        'title': page.get('title', ''),
                        'content': chunk_text,
                        'chunk_index': i,
                        'scraped_at': page.get('scraped_at', '')
                    }
                    chunks.append(chunk)
        
        return chunks
    
    def save_chunks(self, chunks: List[Dict[str, Any]]):
        """Save chunks to file"""
        with open(self.chunks_file, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(chunks)} chunks")
    
    def load_chunks(self) -> List[Dict[str, Any]]:
        """Load chunks from file"""
        if os.path.exists(self.chunks_file):
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def get_all_chunks(self) -> List[str]:
        """Get all chunk contents as a list of strings"""
        chunks = self.load_chunks()
        return [chunk.get('content', '') for chunk in chunks if chunk.get('content')]
    
    def save_metadata(self, metadata: Dict[str, Any]):
        """Save metadata about the RAG system"""
        metadata['last_updated'] = datetime.now().isoformat()
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    def load_metadata(self) -> Dict[str, Any]:
        """Load metadata about the RAG system"""
        if os.path.exists(self.metadata_file):
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

class RAGRetriever:
    """Retrieve relevant information for queries"""
    
    def __init__(self, info_manager: InformationManager):
        self.info_manager = info_manager
        self.chunks = self.info_manager.load_chunks()
        self._base_info = self._initialize_base_info()
    
    def _initialize_base_info(self) -> Dict[str, Any]:
        """Initialize base information from chunks"""
        base_info = {
            "facilities": {},
            "staff": {},
            "events": [],
            "equipment": set(),
            "software": set()
        }
        
        # Process chunks to extract base information
        for chunk in self.chunks:
            content = chunk.get('content', '').lower()
            title = chunk.get('title', '').lower()
            
            # Extract facilities
            if any(keyword in content or keyword in title for keyword in ['facility', 'room', 'space', 'lab']):
                # Look for facility names and their descriptions
                facility_matches = re.finditer(r'(?:facility|room|space|lab)[:：\s]+([^\n.]+)', content)
                for match in facility_matches:
                    facility_name = match.group(1).strip().title()
                    if facility_name and len(facility_name) > 3:
                        base_info["facilities"][facility_name] = {
                            "description": "",
                            "equipment": [],
                            "software": []
                        }
            
            # Extract equipment
            equipment_matches = re.finditer(r'(?:equipment|hardware|device)[:：\s]+([^\n.]+)', content)
            for match in equipment_matches:
                equipment = match.group(1).strip()
                if equipment and len(equipment) > 3:
                    base_info["equipment"].add(equipment)
            
            # Extract software
            software_matches = re.finditer(r'(?:software|application|program)[:：\s]+([^\n.]+)', content)
            for match in software_matches:
                software = match.group(1).strip()
                if software and len(software) > 3:
                    base_info["software"].add(software)
        
        # Convert sets to lists for JSON serialization
        base_info["equipment"] = list(base_info["equipment"])
        base_info["software"] = list(base_info["software"])
        
        return base_info
    
    def get_base_info(self) -> Dict[str, Any]:
        """Get base information about facilities, staff, events, etc."""
        return self._base_info
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search for relevant chunks based on query"""
        if not self.chunks:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_chunks = []
        for chunk in self.chunks:
            content_lower = chunk['content'].lower()
            title_lower = chunk['title'].lower()
            
            content_score = sum(1 for word in query_words if word in content_lower)
            title_score = sum(2 for word in query_words if word in title_lower)
            
            total_score = content_score + title_score
            
            if total_score > 0:
                scored_chunks.append({
                    'chunk': chunk,
                    'score': total_score
                })
        
        scored_chunks.sort(key=lambda x: x['score'], reverse=True)
        return [item['chunk'] for item in scored_chunks[:top_k]]
    
    def get_context_for_query(self, query: str, max_chunks: int = 3) -> str:
        """Get formatted context for a query"""
        relevant_chunks = self.search(query, top_k=max_chunks)
        
        if not relevant_chunks:
            return ""
        
        context_parts = ["=== RAG RETRIEVED INFORMATION ==="]
        
        for i, chunk in enumerate(relevant_chunks, 1):
            context_parts.append(f"\n--- Source {i}: {chunk['title']} ---")
            context_parts.append(f"URL: {chunk['url']}")
            context_parts.append(f"Content: {chunk['content'][:500]}...")
        
        return "\n".join(context_parts)

    def get_all_event_titles(self) -> list:
        """Extract all unique event titles from the chunks."""
        event_titles = set()
        for chunk in self.chunks:
            # Heuristic: look for lines with 'Event:', 'Title:', or similar
            lines = chunk.get('content', '').split('\n')
            for line in lines:
                match = re.search(r'(?:Event|Title|活動名稱|活動|展覽)[:：]\s*(.+)', line, re.IGNORECASE)
                if match:
                    title = match.group(1).strip()
                    if 4 < len(title) < 100:
                        event_titles.add(title)
            # Also try to extract from chunk['title'] if it looks like an event
            if chunk.get('title') and any(word in chunk['title'].lower() for word in ['event', 'exhibition', 'lecture', 'workshop', 'series', '活動', '展覽']):
                event_titles.add(chunk['title'].strip())
        return sorted(event_titles)

    def get_event_details(self, event_title: str) -> dict:
        """Extract event details (title, date, description) for a given event title from the chunks."""
        for chunk in self.chunks:
            content = chunk.get('content', '')
            if event_title.lower() in content.lower() or event_title.lower() in chunk.get('title', '').lower():
                # Try to extract date and description
                date_match = re.search(r'(?:Date|日期)[:：]\s*([\w\-\s/]+)', content, re.IGNORECASE)
                desc_match = re.search(r'(?:Description|內容|簡介|描述)[:：]\s*(.+)', content, re.IGNORECASE)
                description = desc_match.group(1).strip() if desc_match else ''
                date = date_match.group(1).strip() if date_match else ''
                return {
                    'title': event_title,
                    'date': date,
                    'description': description
                }
        return None

    def get_staff_role(self, staff_name: str) -> str:
        """Extract staff role for a given staff name from the chunks."""
        for chunk in self.chunks:
            content = chunk.get('content', '')
            # Look for patterns like 'Dr. Kal Ng (Director)' or 'Mr. John Doe (Engineer)'
            match = re.search(rf'(Dr|Mr|Ms)\.\s*{re.escape(staff_name)}\s*\(([^)]+)\)', content)
            if match:
                return match.group(2).strip()
        return None

def update_rag_data():
    """Update RAG data by scraping the ATL website"""
    print("Starting RAG data update...")
    
    scraper = WebScraper()
    info_manager = InformationManager()
    
    print("Scraping ATL website...")
    scraped_pages = scraper.scrape_site(max_pages=30)
    
    if not scraped_pages:
        print("No pages scraped. Check your internet connection.")
        return
    
    info_manager.save_scraped_data(scraped_pages)
    
    print("Creating content chunks...")
    chunks = info_manager.create_chunks(scraped_pages)
    info_manager.save_chunks(chunks)
    
    metadata = {
        'total_pages_scraped': len(scraped_pages),
        'total_chunks_created': len(chunks),
        'source_url': scraper.base_url,
        'chunk_size': 1000,
        'overlap': 200
    }
    info_manager.save_metadata(metadata)
    
    print(f"RAG data update complete!")
    print(f"- Scraped {len(scraped_pages)} pages")
    print(f"- Created {len(chunks)} chunks")
    print(f"- Data saved to {info_manager.data_dir}")

def update_rag_data_with_urls(additional_urls: List[str] = None):
    """Update RAG data by scraping the ATL website plus additional URLs"""
    print("Starting RAG data update with additional URLs...")
    
    scraper = WebScraper()
    info_manager = InformationManager()
    
    if additional_urls:
        print(f"Additional URLs to scrape: {additional_urls}")
        scraped_pages = scraper.scrape_site_with_additional_urls(additional_urls, max_pages=50)
    else:
        print("Scraping ATL website...")
        scraped_pages = scraper.scrape_site(max_pages=30)
    
    if not scraped_pages:
        print("No pages scraped. Check your internet connection.")
        return
    
    info_manager.save_scraped_data(scraped_pages)
    
    print("Creating content chunks...")
    chunks = info_manager.create_chunks(scraped_pages)
    info_manager.save_chunks(chunks)
    
    metadata = {
        'total_pages_scraped': len(scraped_pages),
        'total_chunks_created': len(chunks),
        'source_url': scraper.base_url,
        'additional_urls': additional_urls or [],
        'chunk_size': 1000,
        'overlap': 200
    }
    info_manager.save_metadata(metadata)
    
    print(f"RAG data update complete!")
    print(f"- Scraped {len(scraped_pages)} pages")
    print(f"- Created {len(chunks)} chunks")
    print(f"- Data saved to {info_manager.data_dir}")

def update_rag_data_from_config(config_path: str = None):
    """Update RAG data using URLs from configuration file"""
    print("Starting RAG data update from configuration...")
    
    scraper = WebScraper()
    info_manager = InformationManager()
    
    config = scraper.load_url_config(config_path)
    if config:
        print(f"Loaded configuration with {len(config.get('additional_urls', []))} additional URLs")
    
    scraped_pages = scraper.scrape_from_config(config_path)
    
    if not scraped_pages:
        print("No pages scraped. Check your internet connection and URL configuration.")
        return
    
    info_manager.save_scraped_data(scraped_pages)
    
    print("Creating content chunks...")
    chunks = info_manager.create_chunks(scraped_pages)
    info_manager.save_chunks(chunks)
    
    metadata = {
        'total_pages_scraped': len(scraped_pages),
        'total_chunks_created': len(chunks),
        'source_url': scraper.base_url,
        'config_used': config_path or "data/rag_urls.json",
        'additional_urls': config.get('additional_urls', []),
        'external_domains': config.get('external_domains', []),
        'chunk_size': 1000,
        'overlap': 200
    }
    info_manager.save_metadata(metadata)
    
    print(f"RAG data update complete!")
    print(f"- Scraped {len(scraped_pages)} pages")
    print(f"- Created {len(chunks)} chunks")
    print(f"- Data saved to {info_manager.data_dir}")

if __name__ == "__main__":
    update_rag_data() 