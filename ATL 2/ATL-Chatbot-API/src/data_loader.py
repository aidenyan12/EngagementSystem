#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Loader Module for ATL Chatbot

This module handles all data loading operations including:
- Base information loading
- FAQ data loading  
- Website data loading
- RAG system integration
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Import RAG system
try:
    from rag_system import InformationManager, RAGRetriever
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    print("RAG system not available. Install required dependencies: pip install requests beautifulsoup4 lxml")

logger = logging.getLogger("data_loader")

class InformationFeed:
    """Enhanced feed method to provide accurate base information to the model with RAG integration"""
    
    def __init__(self):
        self.reload_all_data()
        # Initialize RAG system if available
        self.rag_available = RAG_AVAILABLE
        if self.rag_available:
            try:
                self.info_manager = InformationManager()
                self.rag_retriever = RAGRetriever(self.info_manager)
                print("RAG system initialized successfully")
            except Exception as e:
                print(f"RAG system initialization failed: {e}")
                self.rag_available = False
        else:
            self.rag_retriever = None
    
    def reload_all_data(self):
        """Reload all base info, FAQ, website data, and reset semantic search checkpoints."""
        # Remove Chinese data loading
        self.base_info_en = self._load_base_information('Arts_Tech_Lab_en.json')
        self.faq_data = self._load_faq_data()
        self.website_data = self._load_website_data()
        # Reset MiniLM checkpoint/embeddings
        global _MINILM_FACILITY_EMBS, _MINILM_FACILITY_ALIASES
        _MINILM_FACILITY_EMBS = None
        _MINILM_FACILITY_ALIASES = None
        print("[INFO] All data and semantic search checkpoints reloaded.")
    
    def _load_base_information(self, filename) -> Dict[str, Any]:
        """Load accurate base information about ATL including pricing and rental details"""
        base_info = {
            "facilities": {},
            "general_info": {},
            "contact_info": {},
            "equipment": {},
            "software": {},
            "pricing": {},
            "special_programs": {},
            "events": {},
            "internships": []
        }
        
        # Load from source data (English only)
        atl_path = os.path.join(BASE_DIR, "data", "source_data", filename)
        print(f"[DEBUG] Checking for base info file at: {atl_path}")
        if os.path.exists(atl_path):
            try:
                with open(atl_path, 'r', encoding='utf-8') as f:
                    atl_data = json.load(f)
                    # English only
                    atl_info = atl_data.get("The University of Hong Kong Arts Technology Lab", {})
                    facilities_key = "ATL Facilities"
                    name_key = "Name"
                    area_key = "Area"
                    capacity_key = "Capacity"
                    features_key = "Features"
                    equipment_key = "Equipment"
                    hardware_key = "Hardware"
                    software_key = "Virtual Simulation Media Software"
                    pricing_key = "Fees"
                    reservation_rate_key = "Reservation Rate"
                    description_key = "Description"
                    permit_key = "Permit"
                    
                    # Extract general information
                    overview = atl_info.get("Overview", {})
                    base_info["general_info"] = {
                        "name": overview.get("Name", "ARTS TECHNOLOGY LAB"),
                        "full_name": overview.get("Name", "ARTS TECHNOLOGY LAB"),
                        "english_name": overview.get("Name", "ARTS TECHNOLOGY LAB"),
                        "affiliation": overview.get("Affiliation", "Faculty of Arts, University of Hong Kong"),
                        "positioning": overview.get("Positioning", "An innovative platform for cross-border integration of art and technology"),
                        "function": overview.get("Function", "Support academic research, creativity and knowledge sharing"),
                        "location": "The University of Hong Kong"
                    }
                    # Extract facility information with detailed pricing
                    for facility in atl_info.get(facilities_key, []):
                        name = facility.get(name_key, "")
                        facility_info = {
                            "area": facility.get(area_key, ""),
                            "capacity": facility.get(capacity_key, ""),
                            "features": facility.get(features_key, []),
                            "equipment": facility.get(equipment_key, []),
                            "hardware": facility.get(hardware_key, []),
                            "software": facility.get(software_key, []),
                            "description": facility.get(description_key, ""),
                            "pricing": facility.get(pricing_key, {}),
                            "permit": facility.get(permit_key, ""),
                            "reservation_rate": facility.get(reservation_rate_key, "")
                        }
                        if name:
                            base_info["facilities"][name] = facility_info
                    
                    # Extract equipment information
                    equipment_info = atl_info.get("Equipment", {})
                    if isinstance(equipment_info, dict):
                        base_info["equipment"].update(equipment_info)
                    
                    # Extract software information
                    software_info = atl_info.get("Software", {})
                    if isinstance(software_info, dict):
                        base_info["software"].update(software_info)
                    
                    # Extract contact information
                    contact_info = atl_info.get("Contact", {})
                    if isinstance(contact_info, dict):
                        base_info["contact_info"].update(contact_info)
                    
                    # Extract special programs
                    programs_info = atl_info.get("Special Programs", {})
                    if isinstance(programs_info, dict):
                        base_info["special_programs"].update(programs_info)
                    
                    # Extract events
                    events_info = atl_info.get("Events", {})
                    if isinstance(events_info, dict):
                        base_info["events"].update(events_info)
                    
                    # Extract internships
                    internships_info = atl_info.get("Internships", [])
                    if isinstance(internships_info, list):
                        base_info["internships"] = internships_info
                        
            except json.JSONDecodeError as e:
                logger.error(f"Error loading {filename}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading {filename}: {e}")
        else:
            logger.error(f"Base info file does not exist: {atl_path}")
        
        return base_info
    
    def _load_faq_data(self) -> List[Dict[str, str]]:
        """Load FAQ data for common questions and organize by subtopics"""
        faq_data = []
        self.subtopics = {
            "facilities": [],
            "pricing": [],
            "equipment": [],
            "software": [],
            "staff": [],
            "internships": [],
            "events": [],
            "policies": [],
            "tools": [],
            "general": [],
        }
        
        # Load from website conversations
        web_path = os.path.join(BASE_DIR, "data", "source_data", "website_conversations.json")
        if os.path.exists(web_path):
            try:
                with open(web_path, 'r', encoding='utf-8') as f:
                    web_data = json.load(f)
                    faq_data = web_data.get("conversations", [])
                    # Organize by subtopics
                    for item in faq_data:
                        if "conversations" in item and len(item["conversations"]) >= 2:
                            q = item["conversations"][0]["content"].lower()
                            a = item["conversations"][1]["content"].lower()
                            # Heuristic subtopic assignment
                            if any(k in q for k in ["facility", "room", "space", "lounge", "xr", "meeting", "research", "seasonal"]):
                                self.subtopics["facilities"].append(item)
                            elif any(k in q for k in ["price", "cost", "fee", "rental", "charge", "rate", "pricing", "收費", "租金", "預約", "費用"]):
                                self.subtopics["pricing"].append(item)
                            elif any(k in q for k in ["equipment", "hardware", "device", "machine", "projector", "gpu", "workstation"]):
                                self.subtopics["equipment"].append(item)
                            elif any(k in q for k in ["software", "program", "application", "tool", "unreal", "unity", "touchdesigner"]):
                                self.subtopics["software"].append(item)
                            elif any(k in q for k in ["staff", "team", "dr.", "mr.", "engineer", "coordinator", "practitioner", "aiden", "jenny", "kal", "lawrence"]):
                                self.subtopics["staff"].append(item)
                            elif any(k in q for k in ["intern", "internship", "position", "job", "apply"]):
                                self.subtopics["internships"].append(item)
                            elif any(k in q for k in ["event", "activity", "lecture", "workshop", "series", "exhibition", "presentation"]):
                                self.subtopics["events"].append(item)
                            elif any(k in q for k in ["policy", "requirement", "responsibility", "neutral", "reservation", "rule", "guideline", "clean", "damage", "safety", "emergency"]):
                                self.subtopics["policies"].append(item)
                            elif any(k in q for k in ["tool", "ai", "ollama", "chatgpt", "notion", "perplexity", "dall", "canva", "designer", "slidesgo", "slidesai", "synthesia", "natural readers", "atlhpc", "hpc", "gpu", "server"]):
                                self.subtopics["tools"].append(item)
                            else:
                                self.subtopics["general"].append(item)
            except Exception as e:
                logger.error(f"Error loading FAQ data: {e}")
        
        # Also parse website_info.js for more subtopics
        web_info_path = os.path.join(BASE_DIR, "data", "source_data", "website_info.js")
        if os.path.exists(web_info_path):
            try:
                with open(web_info_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extract JSON-like part
                    json_start = content.find('{')
                    json_str = content[json_start:]
                    web_info = json.loads(json_str)
                    for item in web_info.get("conversations", []):
                        if "conversations" in item and len(item["conversations"]) >= 2:
                            q = item["conversations"][0]["content"].lower()
                            a = item["conversations"][1]["content"].lower()
                            # Use same heuristics as above
                            if any(k in q for k in ["facility", "room", "space", "lounge", "xr", "meeting", "research", "seasonal"]):
                                self.subtopics["facilities"].append(item)
                            elif any(k in q for k in ["price", "cost", "fee", "rental", "charge", "rate", "pricing", "收費", "租金", "預約", "費用"]):
                                self.subtopics["pricing"].append(item)
                            elif any(k in q for k in ["equipment", "hardware", "device", "machine", "projector", "gpu", "workstation"]):
                                self.subtopics["equipment"].append(item)
                            elif any(k in q for k in ["software", "program", "application", "tool", "unreal", "unity", "touchdesigner"]):
                                self.subtopics["software"].append(item)
                            elif any(k in q for k in ["staff", "team", "dr.", "mr.", "engineer", "coordinator", "practitioner", "aiden", "jenny", "kal", "lawrence"]):
                                self.subtopics["staff"].append(item)
                            elif any(k in q for k in ["intern", "internship", "position", "job", "apply"]):
                                self.subtopics["internships"].append(item)
                            elif any(k in q for k in ["event", "activity", "lecture", "workshop", "series", "exhibition", "presentation"]):
                                self.subtopics["events"].append(item)
                            elif any(k in q for k in ["policy", "requirement", "responsibility", "neutral", "reservation", "rule", "guideline", "clean", "damage", "safety", "emergency"]):
                                self.subtopics["policies"].append(item)
                            elif any(k in q for k in ["tool", "ai", "ollama", "chatgpt", "notion", "perplexity", "dall", "canva", "designer", "slidesgo", "slidesai", "synthesia", "natural readers", "atlhpc", "hpc", "gpu", "server"]):
                                self.subtopics["tools"].append(item)
                            else:
                                self.subtopics["general"].append(item)
            except Exception as e:
                logger.error(f"Error loading website info data: {e}")
        
        return faq_data
    
    def _load_website_data(self) -> Dict[str, Any]:
        """Load website data from JSON files"""
        website_data = {}
        
        website_path = os.path.join(BASE_DIR, "data", "rag_data", "website_data.json")
        if os.path.exists(website_path):
            try:
                with open(website_path, 'r', encoding='utf-8') as f:
                    website_data = json.load(f)
            except json.JSONDecodeError as e:
                logger.error(f"Error loading website_data.json: {e}")
            except Exception as e:
                logger.error(f"Unexpected error loading website_data.json: {e}")
        
        return website_data
    
    def get_context_for_question(self, question: str) -> str:
        """Get comprehensive context information for a specific question with RAG integration and detailed subtopic Q&A. Always include full facility details if a facility is detected."""
        question_lower = question.lower()
        base_info = self.get_base_info('english')
        context_parts = []

        # Add general ATL information
        context_parts.append("=== ARTS TECHNOLOGY LAB (ATL) INFORMATION ===")
        context_parts.append(f"Name: {base_info['general_info']['name']} ({base_info['general_info']['full_name']})")
        context_parts.append(f"English Name: {base_info['general_info']['english_name']}")
        context_parts.append(f"Affiliation: {base_info['general_info']['affiliation']}")
        context_parts.append(f"Positioning: {base_info['general_info']['positioning']}")
        context_parts.append(f"Function: {base_info['general_info']['function']}")
        context_parts.append(f"Location: {base_info['general_info']['location']}")

        # Add RAG retrieved information if available (limit to 1 chunk for speed)
        if self.rag_available and self.rag_retriever:
            try:
                rag_context = self.rag_retriever.get_context_for_query(question, max_chunks=1)
                if rag_context:
                    context_parts.append(f"\n{rag_context}")
            except Exception as e:
                logger.error(f"Error using RAG system: {e}")

        # Subtopic keyword mapping
        subtopic_keywords = {
            "facilities": ["facility", "facilities", "space", "room", "lounge", "xr", "meeting", "research", "seasonal"],
            "pricing": ["price", "cost", "fee", "rental", "charge", "rate", "pricing", "收費", "租金", "預約", "費用"],
            "equipment": ["equipment", "hardware", "device", "machine", "projector", "gpu", "workstation"],
            "software": ["software", "program", "application", "tool", "unreal", "unity", "touchdesigner"],
            "staff": ["staff", "team", "dr.", "mr.", "engineer", "coordinator", "practitioner", "aiden", "jenny", "kal", "lawrence"],
            "internships": ["intern", "internship", "position", "job", "apply"],
            "events": ["event", "activity", "lecture", "workshop", "series", "exhibition", "presentation"],
            "policies": ["policy", "requirement", "responsibility", "neutral", "reservation", "rule", "guideline", "clean", "damage", "safety", "emergency"],
            "tools": ["tool", "ai", "ollama", "chatgpt", "notion", "perplexity", "dall", "canva", "designer", "slidesgo", "slidesai", "synthesia", "natural readers", "atlhpc", "hpc", "gpu", "server"],
        }

        # Detect relevant subtopics
        matched_subtopics = []
        for subtopic, keywords in subtopic_keywords.items():
            if any(k in question_lower for k in keywords):
                matched_subtopics.append(subtopic)

        # If no subtopic matched, treat as general/broad
        if not matched_subtopics:
            matched_subtopics = ["general"]

        # For broad/general questions, provide a brief overview instead of full subtopic list
        if matched_subtopics == ["general"]:
            context_parts.append("\n=== GENERAL INFORMATION ===")
            context_parts.append("ATL offers facilities, equipment, software, staff support, internships, events, policies, and AI tools.")
            context_parts.append("Ask about specific topics for detailed information.")

        # Always include full facility details if a facility is detected
        # --- New: Direct, substring, and fuzzy match on facility keys ---
        def find_facility_key(facilities_dict, target_name):
            for key in facilities_dict.keys():
                if key.lower() == target_name.lower():
                    return key
            for key in facilities_dict.keys():
                if target_name.lower() in key.lower() or key.lower() in target_name.lower():
                    return key
            import difflib
            keys_lower = [k.lower() for k in facilities_dict.keys()]
            match = difflib.get_close_matches(target_name.lower(), keys_lower, n=1, cutoff=0.5)
            if match:
                idx = keys_lower.index(match[0])
                return list(facilities_dict.keys())[idx]
            return None

        # Try to extract a facility name from the question
        facilities = base_info.get("facilities", {})
        fallback_info = self.base_info_en if base_info != self.base_info_en else {}
        facilities_other = fallback_info.get("facilities", {})
        found_facility_key = None
        for key in facilities.keys():
            if key.lower() in question_lower or question_lower in key.lower():
                found_facility_key = key
                break
        if not found_facility_key:
            for key in facilities_other.keys():
                if key.lower() in question_lower or question_lower in key.lower():
                    found_facility_key = key
                    break
        if not found_facility_key:
            # Fuzzy match as last resort
            import difflib
            keys_lower = [k.lower() for k in facilities.keys()]
            match = difflib.get_close_matches(question_lower, keys_lower, n=1, cutoff=0.5)
            if match:
                idx = keys_lower.index(match[0])
                found_facility_key = list(facilities.keys())[idx]
        if not found_facility_key:
            keys_lower = [k.lower() for k in facilities_other.keys()]
            match = difflib.get_close_matches(question_lower, keys_lower, n=1, cutoff=0.5)
            if match:
                idx = keys_lower.index(match[0])
                found_facility_key = list(facilities_other.keys())[idx]
        if found_facility_key:
            # Add full facility details
            facility_info = facilities.get(found_facility_key) or facilities_other.get(found_facility_key)
            context_parts.append(f"\n=== FULL DETAILS FOR {found_facility_key.upper()} ===")
            for k, v in facility_info.items():
                context_parts.append(f"{k}: {v}")

        # For each matched subtopic, pull the most relevant Q&A (limit to 2 per subtopic for speed)
        for subtopic in matched_subtopics:
            if hasattr(self, 'subtopics') and self.subtopics.get(subtopic):
                context_parts.append(f"\n=== {subtopic.upper()} Q&A ===")
                # Find most relevant Q&A by keyword overlap
                qas = self.subtopics[subtopic]
                scored = []
                for item in qas:
                    q = item["conversations"][0]["content"].lower()
                    score = sum(1 for k in question_lower.split() if k in q)
                    scored.append((score, item))
                # Sort by score descending, fallback to order
                scored.sort(key=lambda x: -x[0])
                for _, item in scored[:2]:  # Reduced from 3 to 2
                    context_parts.append(f"Q: {item['conversations'][0]['content']}")
                    context_parts.append(f"A: {item['conversations'][1]['content']}")

        relevant_contexts = []
        
        # Check base information
        
        # Check facilities
        for facility_name, facility_info in base_info.get("facilities", {}).items():
            if any(keyword in question_lower for keyword in [facility_name.lower(), "facility", "room", "space"]):
                context = f"**{facility_name}**:\n"
                if facility_info.get("description"):
                    context += f"Description: {facility_info['description']}\n"
                if facility_info.get("area"):
                    context += f"Area: {facility_info['area']}\n"
                if facility_info.get("capacity"):
                    context += f"Capacity: {facility_info['capacity']}\n"
                if facility_info.get("features"):
                    context += f"Features: {', '.join(facility_info['features'])}\n"
                if facility_info.get("equipment"):
                    context += f"Equipment: {', '.join(facility_info['equipment'])}\n"
                if facility_info.get("pricing"):
                    pricing = facility_info['pricing']
                    if isinstance(pricing, dict):
                        context += "Pricing:\n"
                        for rate_type, price in pricing.items():
                            context += f"  - {rate_type}: {price}\n"
                relevant_contexts.append(context)
        
        # Check for pricing-specific requests
        if any(keyword in question_lower for keyword in ["price", "cost", "fee", "rent", "rental", "booking", "reservation"]):
            pricing_context = "**ATL Pricing Information**:\n"
            for facility_name, facility_info in base_info.get("facilities", {}).items():
                if facility_info.get("pricing"):
                    pricing_context += f"\n{facility_name}:\n"
                    pricing = facility_info['pricing']
                    if isinstance(pricing, dict):
                        for rate_type, price in pricing.items():
                            pricing_context += f"  - {rate_type}: {price}\n"
            relevant_contexts.append(pricing_context)
        
        # FAQ data is now handled through subtopics system above
        
        # Add relevant contexts to context_parts
        if relevant_contexts:
            context_parts.extend(relevant_contexts)
        
        # Add instruction for the model
        context_parts.append(f"\n=== INSTRUCTIONS ===")
        context_parts.append("Based on the above information, provide accurate and helpful responses.")
        context_parts.append("If the information is not available in the context above, clearly state that you don't have that specific information. If you need further assistance, please contact ATL staff.")

        return "\n".join(context_parts)
    

    
    def get_base_info(self, lang='english'):
        """Get base information in specified language"""
        # Always return English data
        return self.base_info_en

# Global variables for MiniLM embeddings
_MINILM_FACILITY_EMBS = None
_MINILM_FACILITY_ALIASES = None

def reload_chatbot_data(info_feed):
    """Reload all chatbot data"""
    info_feed.reload_all_data() 