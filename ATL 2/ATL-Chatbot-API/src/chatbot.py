#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ATL Chatbot - Central Interface with Enhanced Feed Method (Refactored)

This is the main interface for the Arts Tech Lab Chatbot project.
It uses an enhanced feed method to provide accurate information without fine-tuning.
All functionality has been separated into modules while maintaining exact same behavior.
"""

import os
import sys
import logging
import torch
import argparse
import json
import time
import re
from typing import List, Dict, Any, Optional, Union, Tuple
from transformers import AutoModelForCausalLM, AutoTokenizer
import difflib
from sentence_transformers import SentenceTransformer, util
import random
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from sentence_transformers import SentenceTransformer
import numpy as np
import warnings
import pickle
from datetime import datetime
import shutil

# Set up environment variables for transformers
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_NO_CONSOLE_WARNING"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Add src to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import modular components
from data_loader import InformationFeed
from model_manager import load_model, clear_model_cache, get_model_info
from text_processors import (
    detect_language, is_non_text_input, get_friendly_non_text_response,
    extract_facility_from_question, find_best_facility_match, 
    extract_staff_names_from_text, normalize_facility_name,
    get_category_emoji, get_section_emoji, group_similar_points,
    translate_response
)
from response_generators import (
    generate_lightweight_response, generate_comprehensive_response,
    generate_pricing_response, generate_booking_response, 
    generate_facility_response, generate_staff_response,
    generate_event_response, format_response, extract_enhanced_qa_response,
    generate_section_summary, generate_all_facilities_structured,
    generate_all_equipment_structured, generate_all_software_structured,
    extract_and_structure_context, generate_structured_fallback_response,
    get_all_staff_names, generate_all_facilities_pricing,
    generate_specific_facility_info, generate_specific_facility_pricing
)

# Import terminology standardizer
try:
    from terminology import TerminologyStandardizer
except ImportError:
    # Fallback if terminology module is not available
    class TerminologyStandardizer:
        def standardize_text(self, text, language):
            return text

# Import website links module
try:
    from website_links import add_website_links_to_response, get_website_link_response, website_manager
    WEBSITE_LINKS_AVAILABLE = True
except ImportError:
    WEBSITE_LINKS_AVAILABLE = False
    website_manager = None
    def add_website_links_to_response(response, user_input):
        return response
    def get_website_link_response(user_input):
        return None

# Import RAG system
try:
    from rag_system import InformationManager, RAGRetriever
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("RAG system not available. Install required dependencies: pip install requests beautifulsoup4 lxml")

# Set up basic console logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("chatbot")

# Set up file logging for timing information
timing_logger = logging.getLogger("timing")
timing_logger.setLevel(logging.INFO)

# Create timing log file handler
timing_log_dir = os.path.join(BASE_DIR, "logs")
os.makedirs(timing_log_dir, exist_ok=True)
timing_log_file = os.path.join(timing_log_dir, "timing.log")
timing_file_handler = logging.FileHandler(timing_log_file, encoding='utf-8')
timing_file_handler.setLevel(logging.INFO)
timing_file_formatter = logging.Formatter('%(asctime)s - %(message)s')
timing_file_handler.setFormatter(timing_file_formatter)
timing_logger.addHandler(timing_file_handler)

# Prevent timing logger from propagating to console
timing_logger.propagate = False

# Initialize terminology standardizer
standardizer = TerminologyStandardizer()

# Global model cache
_model_cache = None
_tokenizer_cache = None

# Add at the top, after imports
RESPONSE_LANGUAGE = "english"  # Change to 'chinese' for all Chinese output

def extract_qa_response(qa_sections, detected_intent):
    """Extract response from Q&A sections (fallback function)"""
    if qa_sections:
        qa_text = qa_sections[0]
        if 'A: ' in qa_text:
            answer_parts = []
            lines = qa_text.split('\n')
            for line in lines:
                if line.startswith('A: '):
                    answer_parts.append(line[3:])
            if answer_parts:
                response = ' '.join(answer_parts)
                response += f"\n\nIs there anything specific about {detected_intent} that you'd like to know more about? If you need further assistance, please contact ATL staff."
                return response
            else:
                return f"Based on the available information about {detected_intent}, I can help you with that. Please ask a more specific question for detailed information. If you need further assistance, please contact ATL staff."
        else:
            return f"Based on the available information about {detected_intent}, I can help you with that. Please ask a more specific question for detailed information. If you need further assistance, please contact ATL staff."
    else:
        return f"Based on the available information about {detected_intent}, I can help you with that. Please ask a more specific question for detailed information. If you need further assistance, please contact ATL staff."

def generate_response(model, tokenizer, user_input, thinking_mode=False, info_feed=None, lightweight_mode=False):
    return generate_lightweight_response(model, user_input, info_feed)

def save_conversation(conversation, client_name="anonymous"):
    """Save a conversation to the client_questions directory"""
    import datetime
    
    # Create client_questions directory if it doesn't exist
    client_dir = os.path.join(BASE_DIR, "data", "client_questions")
    os.makedirs(client_dir, exist_ok=True)
    
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{client_name}_{timestamp}.json"
    filepath = os.path.join(client_dir, filename)
    
    # Save conversation data
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump({
            "client": client_name,
            "timestamp": datetime.datetime.now().isoformat(),
            "conversation": conversation
        }, f, ensure_ascii=False, indent=2)
    
    logger.info(f"Conversation saved to {filepath}")
    return filepath

def update_rag_data():
    """Update RAG data by scraping the ATL website"""
    if not RAG_AVAILABLE:
        print("RAG system not available. Install required dependencies: pip install requests beautifulsoup4 lxml")
        return
    
    try:
        from rag_system import update_rag_data as rag_update
        rag_update()
    except Exception as e:
        print(f"Error updating RAG data: {e}")

def get_all_events(info_feed):
    """Extract all events from the available data sources."""
    events_list = []
    
    # Extract from English base info
    base_info = info_feed.get_base_info('english')
    if base_info and "events" in base_info:
        events = base_info["events"]
        if isinstance(events, dict):
            for event_type, event_data in events.items():
                if isinstance(event_data, list):
                    for event in event_data:
                        if isinstance(event, dict):
                            title = event.get('title', event.get('name', ''))
                            date = event.get('date', '')
                            description = event.get('description', '')
                            if title:
                                event_text = f"{title}"
                                if date:
                                    event_text += f" ({date})"
                                if description:
                                    event_text += f": {description}"
                                events_list.append(event_text)
                        elif isinstance(event, str):
                            events_list.append(event)
                elif isinstance(event_data, str):
                    events_list.append(f"{event_type}: {event_data}")
        elif isinstance(events, list):
            events_list.extend(events)
    
    # Extract from FAQ data
    faq_data = info_feed.faq_data
    if faq_data and isinstance(faq_data, dict):
        for category, questions in faq_data.items():
            if 'event' in category.lower() or 'activity' in category.lower():
                if isinstance(questions, list):
                    for item in questions:
                        if isinstance(item, dict):
                            answer = item.get('answer', '')
                            if answer:
                                events_list.append(answer)
    
    # Extract from website data  
    website_data = info_feed.website_data
    if website_data and isinstance(website_data, dict):
        for page_name, content in website_data.items():
            if 'event' in page_name.lower() or 'activity' in page_name.lower():
                if isinstance(content, str):
                    # Extract event information from content
                    lines = content.split('\n')
                    for line in lines:
                        if line.strip() and ('event' in line.lower() or 'workshop' in line.lower() or 'seminar' in line.lower()):
                            events_list.append(line.strip())
    
    # Extract from RAG data if available
    if hasattr(info_feed, 'rag_available') and info_feed.rag_available:
        try:
            if info_feed.rag_retriever:
                # Search for event-related content
                event_chunks = info_feed.rag_retriever.search("events activities workshops seminars", top_k=10)
                for chunk in event_chunks:
                    if chunk and isinstance(chunk, str):
                        # Extract event information from chunk
                        lines = chunk.split('\n')
                        for line in lines:
                            if line.strip() and ('event' in line.lower() or 'workshop' in line.lower() or 'seminar' in line.lower()):
                                events_list.append(line.strip())
        except Exception as e:
            logger.error(f"Error extracting events from RAG: {e}")
    
    # Remove duplicates while preserving order
    unique_events = []
    seen = set()
    
    for event in events_list:
        normalized = event.lower().strip()
        if normalized not in seen and len(normalized) > 5:
            seen.add(normalized)
            unique_events.append(event)
    
    return unique_events

def reload_chatbot_data(info_feed):
    """Reload all chatbot data and semantic search checkpoints."""
    info_feed.reload_all_data()

def interactive_chat():
    print("\n===== Arts Technology Lab Chatbot =====")
    print("Type 'exit', 'quit', or 'q' to end the session")
    print("Type 'help' for a list of available commands.")
    if RAG_AVAILABLE:
        print("Type '/rag-update' to update RAG data from the ATL website")
        print("Type '/rag-status' to check RAG system status")
    print("=========================================\n")
    model, tokenizer = load_model()
    info_feed = InformationFeed()  # Initialize enhanced feed method with RAG
    chat_history = []
    client_name = "anonymous"
    client_input = input("Enter your name (optional, press Enter to remain anonymous): ").strip()
    if client_input:
        client_name = client_input
    print(f"\nHello, {client_name}! I am ATL Assistant, how can I help you today 😊 ?")
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() in ["exit", "quit", "q"]:
                print("\nGoodbye! Thank you for chatting.")
                if chat_history:
                    saved_path = save_conversation(chat_history, client_name)
                    print(f"Conversation saved to {saved_path}")
                break
            if not user_input:
                print("Please enter a question.")
                continue
            
            # Check for non-text input
            if is_non_text_input(user_input):
                print(f"\nAssistant: {get_friendly_non_text_response()}")
                continue
                
            if user_input.lower() == "/context":
                print("\n=== INFORMATION FEED METHOD ===")
                print("I use a comprehensive feed method that provides:")
                print("- ATL facility information (areas, capacities, features)")
                print("- Equipment and software details")
                print("- FAQ data from website conversations")
                print("- General ATL information")
                if RAG_AVAILABLE:
                    print("- RAG: Real-time information from the ATL website")
                print("\nThis ensures accurate responses without requiring fine-tuning.")
                continue
            if RAG_AVAILABLE:
                if user_input.lower() == "/rag-update":
                    print("\nUpdating RAG data from the ATL website...")
                    update_rag_data()
                    try:
                        info_feed.info_manager = InformationManager()
                        info_feed.rag_retriever = RAGRetriever(info_feed.info_manager)
                        print("RAG system updated successfully!")
                    except Exception as e:
                        print(f"Error reinitializing RAG system: {e}")
                    continue
                if user_input.lower() == "/rag-status":
                    print("\n=== RAG SYSTEM STATUS ===")
                    if info_feed.rag_available:
                        try:
                            metadata = info_feed.info_manager.load_metadata()
                            if metadata:
                                print(f"Last updated: {metadata.get('last_updated', 'Unknown')}")
                                print(f"Pages scraped: {metadata.get('total_pages_scraped', 0)}")
                                print(f"Chunks created: {metadata.get('total_chunks_created', 0)}")
                                print(f"Source URL: {metadata.get('source_url', 'Unknown')}")
                            else:
                                print("No RAG data found. Run '/rag-update' to initialize.")
                        except Exception as e:
                            print(f"Error checking RAG status: {e}")
                    else:
                        print("RAG system not available.")
                    continue
            print("Generating response...")
            chat_history.append({"role": "user", "content": user_input})
            response = generate_response(model, tokenizer, user_input, False, info_feed, lightweight_mode=True)
            print(f"\nAssistant: {response}")
            chat_history.append({"role": "assistant", "content": response})
        except KeyboardInterrupt:
            print("\nChat session terminated. Goodbye!")
            if chat_history:
                saved_path = save_conversation(chat_history, client_name)
                print(f"Conversation saved to {saved_path}")
            break
        except Exception as e:
            print(f"\nAn error occurred: {str(e)}")
            logger.error(f"Error in chat session: {e}")

def display_help():
    """Display help information"""
    print("\n===== ATL Chatbot Help =====")
    print("Available commands:")
    print("  chat       - Start interactive chat with the model")
    print("  info       - Display project information")
    print("  help       - Display this help message")
    print()
    print("Chat mode features:")
    print("  /think     - Enable thinking mode (model shows step-by-step reasoning)")
    print("  /nothink   - Disable thinking mode (model provides direct answers)")
    if RAG_AVAILABLE:
        print("  /rag-update - Update RAG data from the ATL website")
        print("  /rag-status - Check RAG system status")
    print("  All conversations are automatically saved to ./data/client_questions/")
    print()
    print("Information Feed Method:")
    print("  The chatbot uses an enhanced feed method that provides accurate ATL information")
    print("  without requiring fine-tuning. It includes:")
    print("  - Facility details (areas, capacities, features)")
    print("  - Equipment and software information")
    print("  - FAQ data from website conversations")
    print("  - General ATL information")
    if RAG_AVAILABLE:
        print("  - RAG: Real-time information from the ATL website")
    print()
    print("Examples:")
    print("  python src/chatbot.py chat")
    print("  python src/chatbot.py info")

def display_info():
    """Display project information"""
    print("\n===== ATL Chatbot Information =====")
    print(f"Project root: {BASE_DIR}")
    print(f"Base model: {os.path.join(BASE_DIR, 'models/qwen_base')}")
    print(f"Data directory: {os.path.join(BASE_DIR, 'data')}")
    
    # Check if model files exist
    base_model_path = os.path.join(BASE_DIR, "models/qwen_base")
    if os.path.exists(base_model_path):
        print("Base model status: Available")
    else:
        print("Base model status: Not found")
        
    # Check source data
    atl_path = os.path.join(BASE_DIR, "data", "source_data", "Arts_Tech_Lab_en.json")
    if os.path.exists(atl_path):
        print("ATL source data: Available")
    else:
        print("ATL source data: Not found")
    
    # Check FAQ data
    web_path = os.path.join(BASE_DIR, "data", "source_data", "website_conversations.json")
    if os.path.exists(web_path):
        print("FAQ data: Available")
    else:
        print("FAQ data: Not found")
    
    # Check RAG system
    if RAG_AVAILABLE:
        print("RAG system: Available")
        rag_data_dir = os.path.join(BASE_DIR, "data", "rag_data")
        if os.path.exists(rag_data_dir):
            print("RAG data directory: Available")
        else:
            print("RAG data directory: Not found (run '/rag-update' in chat to initialize)")
    else:
        print("RAG system: Not available (install dependencies: pip install requests beautifulsoup4 lxml)")
    
    print("\nUsing enhanced feed method with RAG for accurate information delivery.")

if __name__ == "__main__":
    interactive_chat() 