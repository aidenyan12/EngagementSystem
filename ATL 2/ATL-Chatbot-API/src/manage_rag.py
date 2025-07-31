#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
RAG Management Script for ATL Chatbot

This script provides easy management of the RAG system for the ATL chatbot.
"""
import sys
import os
import argparse

# Add src to path
sys.path.append(os.path.dirname(__file__))

def update_rag():
    """Update RAG data from the ATL website"""
    try:
        from rag_system import update_rag_data
        update_rag_data()
    except ImportError:
        print("RAG system not available. Install required dependencies:")
        print("pip install requests beautifulsoup4 lxml")
    except Exception as e:
        print(f"Error updating RAG data: {e}")

def update_rag_with_urls(urls):
    """Update RAG data with additional URLs"""
    try:
        from rag_system import update_rag_data_with_urls
        url_list = urls.split(',') if isinstance(urls, str) else urls
        update_rag_data_with_urls(url_list)
    except ImportError:
        print("RAG system not available. Install required dependencies:")
        print("pip install requests beautifulsoup4 lxml")
    except Exception as e:
        print(f"Error updating RAG data with URLs: {e}")

def update_rag_from_config(config_path=None):
    """Update RAG data using configuration file"""
    try:
        from rag_system import update_rag_data_from_config
        update_rag_data_from_config(config_path)
    except ImportError:
        print("RAG system not available. Install required dependencies:")
        print("pip install requests beautifulsoup4 lxml")
    except Exception as e:
        print(f"Error updating RAG data from config: {e}")

def check_status():
    """Check RAG system status"""
    try:
        from rag_system import InformationManager
        info_manager = InformationManager()
        metadata = info_manager.load_metadata()
        print("=== RAG SYSTEM STATUS ===")
        if metadata:
            print(f"Last updated: {metadata.get('last_updated', 'Unknown')}")
            print(f"Pages scraped: {metadata.get('total_pages_scraped', 0)}")
            print(f"Chunks created: {metadata.get('total_chunks_created', 0)}")
            print(f"Source URL: {metadata.get('source_url', 'Unknown')}")
            chunks = info_manager.load_chunks()
            print(f"Available chunks: {len(chunks)}")
        else:
            print("No RAG data found. Run 'python src/manage_rag.py update' to initialize.")
    except ImportError:
        print("RAG system not available. Install required dependencies:")
        print("pip install requests beautifulsoup4 lxml")
    except Exception as e:
        print(f"Error checking status: {e}")

def test_retrieval():
    """Test RAG retrieval with sample queries"""
    try:
        from rag_system import InformationManager, RAGRetriever
        info_manager = InformationManager()
        retriever = RAGRetriever(info_manager)
        test_queries = [
            "What facilities are available at ATL?",
            "Tell me about the XR Space",
            "What equipment can I use?",
            "How do I book a room?",
            "What events are happening?"
        ]
        print("=== RAG RETRIEVAL TEST ===")
        for query in test_queries:
            print(f"\nQuery: {query}")
            results = retriever.search(query, top_k=2)
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  Result {i}: {result['title']}")
                    print(f"    URL: {result['url']}")
                    print(f"    Content preview: {result['content'][:100]}...")
            else:
                print("  No results found")
    except ImportError:
        print("RAG system not available. Install required dependencies:")
        print("pip install requests beautifulsoup4 lxml")
    except Exception as e:
        print(f"Error testing retrieval: {e}")

def main():
    parser = argparse.ArgumentParser(description="RAG Management for ATL Chatbot")
    parser.add_argument("command", choices=["update", "update-urls", "update-config", "status", "test"], 
                        help="Command to execute")
    parser.add_argument("--urls", type=str, 
                        help="Comma-separated list of additional URLs to scrape")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to URL configuration file")
    
    args = parser.parse_args()
    
    if args.command == "update":
        update_rag()
    elif args.command == "update-urls":
        if not args.urls:
            print("Error: --urls argument required for update-urls command")
            parser.print_help()
            return
        update_rag_with_urls(args.urls)
    elif args.command == "update-config":
        update_rag_from_config(args.config)
    elif args.command == "status":
        check_status()
    elif args.command == "test":
        test_retrieval()
    else:
        print(f"Unknown command: {args.command}")
        parser.print_help()

if __name__ == "__main__":
    main() 