#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Response Generators Module for ATL Chatbot

This module handles all response generation functions including:
- Lightweight response generation
- Comprehensive response generation  
- Specific facility, pricing, booking responses
- Staff and event responses
- Structured response formatting
"""

import logging
import time
import random
import os
import json
from typing import List, Dict, Any, Optional
from datetime import datetime

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

from text_processors import (
    extract_facility_from_question, find_best_facility_match,
    extract_staff_names_from_text, get_friendly_non_text_response
)

logger = logging.getLogger("response_generators")

# Add at the top, after imports
RESPONSE_LANGUAGE = "english"  # Change to 'chinese' for all Chinese output

def organize_events_by_category(event_titles):
    """Organize events into categories with subtitles for better readability"""
    if not event_titles:
        return "No events are currently available. Please check the ATL website for updates! 🎪"
    
    # Categories for organizing events
    ongoing_series = []
    workshop_series = []
    general_events = []
    external_events = []
    
    for title in event_titles:
        title_lower = title.lower()
        clean_title = title.replace(" – Arts Tech Lab", "").strip()
        
        # Check for events with specific dates first (highest priority)
        if "[" in title and "]" in title:
            workshop_series.append(clean_title)
        # Check for external events
        elif "external" in title_lower:
            external_events.append(clean_title)
        # Check for ongoing series (no specific dates) - but exclude those with dates
        elif any(keyword in title_lower for keyword in ["series", "microcredentialing", "transformations"]) and "[" not in title:
            ongoing_series.append(clean_title)
        # Check for workshops and talks without dates
        elif any(keyword in title_lower for keyword in ["workshop", "talk", "development"]):
            workshop_series.append(clean_title)
        # General events category (skip generic "Events" entries)
        elif title_lower not in ["events – arts tech lab", "events"]:
            general_events.append(clean_title)
    
    # Build organized response
    response = "**ATL Events & Programs** 🎪\n\n"
    
    if ongoing_series:
        response += "__🎯 Ongoing Series & Programs__\n"
        for event in ongoing_series:
            response += f"• **{event}**\n"
        response += "\n"
    
    if workshop_series:
        response += "__🛠️ Workshops & Talks__\n"
        for event in workshop_series:
            # Consistent formatting for events with dates
            if "[" in event and "]" in event:
                # Extract date and event name
                date_start = event.find("[")+1
                date_end = event.find("]")
                date_part = event[date_start:date_end]
                event_name = event[date_end+1:].strip()
                response += f"• **[{date_part}] {event_name}**\n"
            else:
                response += f"• **{event}**\n"
        response += "\n"
    
    if general_events:
        response += "__📅 General Events__\n"
        for event in general_events:
            if event.lower() != "events":  # Skip generic "Events" entry
                response += f"• **{event}**\n"
        response += "\n"
    
    if external_events:
        response += "__🌐 External Events__\n"
        # Check if we only have generic external events entries
        has_specific_events = any(event.lower() not in ["external events", "external"] for event in external_events)
        
        if not has_specific_events:
            # Show coming soon message for generic entries
            response += "• (Not yet ready, is coming soon)\n"
        else:
            # Show specific external events
            for event in external_events:
                if event.lower() not in ["external events", "external"]:
                    response += f"• **{event}**\n"
        response += "\n"
    
    response += "_For detailed information about any event, please visit the ATL website or contact us directly!_ ✨"
    
    return response

def generate_lightweight_response(generator, user_input, info_feed=None):
    """Generate a lightweight response using the pipeline"""
    # Start timing
    start_time = time.time()

    # Import here to avoid circular imports
    from text_processors import is_non_text_input, get_friendly_non_text_response

    # Check for non-text input first
    if is_non_text_input(user_input):
        return get_friendly_non_text_response()

    user_lower = user_input.lower().strip()

    # Check for specific website link queries first
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

    if WEBSITE_LINKS_AVAILABLE and website_manager:
        relevant_links = website_manager.find_relevant_links(user_input)
        if relevant_links:
            is_contact_query = any('contact' in link['keywords'] for link in relevant_links)
            # --- FACILITIES ---
            facilities = info_feed.get_base_info().get("facilities", {})
            facility_names = [name.lower() for name in facilities.keys()]
            broad_facility_keywords = ["all facilities", "facilities", "what facilities", "facility", "spaces", "rooms"]
            if any(k in user_lower for k in broad_facility_keywords):
                facility_list = "\n".join(f"• {name}" for name in facilities.keys())
                response = f"Here are the main facilities at ATL:\n\n{facility_list}\n\nLet me know if you'd like more details about any specific facility!"
                response = add_website_links_to_response(response, user_input)
                return response
            # --- EVENTS ---
            if info_feed and hasattr(info_feed, 'rag_retriever') and info_feed.rag_retriever:
                try:
                    event_titles = info_feed.rag_retriever.get_all_event_titles()
                    broad_event_keywords = ["all events", "events", "event", "exhibitions", "workshops", "lectures", "activities"]
                    if any(k in user_lower for k in broad_event_keywords):
                        if event_titles:
                            organized_events = organize_events_by_category(event_titles)
                            response = organized_events
                            response = add_website_links_to_response(response, user_input)
                            return response
                except:
                    pass
            # --- STAFF ---
            if info_feed and hasattr(info_feed, 'rag_retriever') and info_feed.rag_retriever:
                try:
                    staff_names_roles = get_all_staff_names(info_feed)
                    broad_staff_keywords = ["all staff", "staff", "team", "members", "who are working here"]
                    if any(k in user_lower for k in broad_staff_keywords):
                        if staff_names_roles:
                            staff_list_str = "\n".join(f"• {name}" for name in staff_names_roles)
                            response = f"Here are some of the staff members at ATL:\n\n{staff_list_str}\n\nYou can find more details about their roles on the ATL website. 👥"
                            response = add_website_links_to_response(response, user_input)
                            return response
                except:
                    pass
            # --- EQUIPMENT ---
            broad_equipment_keywords = ["all equipment", "equipment", "devices", "hardware", "machines"]
            if any(k in user_lower for k in broad_equipment_keywords):
                equipment_set = set()
                for facility_info in facilities.values():
                    for eq in facility_info.get('equipment', []):
                        equipment_set.add(eq)
                    for hw in facility_info.get('hardware', []):
                        equipment_set.add(hw)
                if equipment_set:
                    equipment_list = "\n".join(f"• {eq}" for eq in sorted(equipment_set))
                    response = f"Here is a list of equipment and hardware available at ATL:\n\n{equipment_list}\n\nLet me know if you'd like more details about any specific equipment!"
                    response = add_website_links_to_response(response, user_input)
                    return response
            # --- SOFTWARE ---
            broad_software_keywords = ["all software", "software", "programs", "applications", "tools"]
            if any(k in user_lower for k in broad_software_keywords):
                software_set = set()
                for facility_info in facilities.values():
                    for sw in facility_info.get('software', []):
                        software_set.add(sw)
                if software_set:
                    software_list = "\n".join(f"• {sw}" for sw in sorted(software_set))
                    response = f"Here is a list of software tools available at ATL:\n\n{software_list}\n\nLet me know if you'd like more details about any specific software!"
                    response = add_website_links_to_response(response, user_input)
                    return response
            # --- PRICING ---
            broad_pricing_keywords = ["all pricing", "pricing", "cost", "fees", "rates"]
            if any(k in user_lower for k in broad_pricing_keywords):
                response = generate_all_facilities_pricing(info_feed, user_input)
                response = add_website_links_to_response(response, user_input)
                return response
            # --- BOOKING ---
            broad_booking_keywords = ["booking", "book", "reserve", "reservation", "schedule", "appointment"]
            if any(k in user_lower for k in broad_booking_keywords):
                response = generate_booking_response(info_feed, user_input)
                response = add_website_links_to_response(response, user_input)
                return response
            # --- INTERNSHIPS ---
            broad_internship_keywords = ["internship", "internships", "intern", "positions", "job opportunities"]
            if any(k in user_lower for k in broad_internship_keywords):
                response = "ATL offers internship opportunities for students interested in arts and technology. You can find more details and application info on the ATL website."
                response = add_website_links_to_response(response, user_input)
                return response
            # --- POLICIES ---
            broad_policy_keywords = ["policies", "policy", "rules", "guidelines", "requirements"]
            if any(k in user_lower for k in broad_policy_keywords):
                response = "ATL has clear policies and guidelines for lab use, booking, and safety. You can find more details on the ATL website."
                response = add_website_links_to_response(response, user_input)
                return response
            # --- TOOLS ---
            broad_tool_keywords = ["ai tools", "tools", "ai", "ollama", "chatgpt", "notion", "perplexity", "dall", "canva", "designer", "slidesgo", "slidesai", "synthesia", "natural readers", "atlhpc", "hpc", "gpu", "server"]
            if any(k in user_lower for k in broad_tool_keywords):
                response = "ATL provides access to a variety of AI tools and creative software. You can find more details and tutorials on the ATL website."
                response = add_website_links_to_response(response, user_input)
                return response
            # Otherwise, for other categories, just append the link after the normal answer
            # (fall through to normal logic, and the link will be appended at the end)
            # If it's a contact query, let the contact logic handle it
            if not is_contact_query:
                # Don't return only the link, let the rest of the function run and append the link at the end
                pass

    # Check for greetings first
    greeting_keywords = [
        "hi", "hello", "hey", "yo", "sup", "what's up", "howdy", "greetings",
        "good morning", "good afternoon", "good evening", "morning", "afternoon", "evening",
        "hola", "bonjour", "ciao", "你好", "嗨", "哈囉", "早安", "午安", "晚安"
    ]
    # Only trigger greeting if the input is exactly a greeting or matches a greeting phrase
    if user_lower in greeting_keywords or any(user_lower.strip() == greeting for greeting in greeting_keywords):
        # Return casual greeting response
        casual_greetings = [
            "Hey there! 👋✨ How can I help you with ATL today? 🚀",
            "Hi! 😊🎨 What would you like to know about the Arts Technology Lab? 💫",
            "Hello! 👋🌟 Ready to explore ATL's amazing facilities? 🏢",
            "Hey! 😄💻 What's on your mind about ATL? 🎯",
            "Hi there! ✨🔧 How can I assist you with Arts Technology Lab info? 📚",
            "Hello! 🎨🚀 Let's talk about ATL - what interests you? 💡",
            "Hey! 🚀🎯 What would you like to discover about ATL today? 🌟"
        ]
        return random.choice(casual_greetings)

    # Check for farewell messages
    farewell_keywords = [
        "bye", "goodbye", "see you", "take care", "later", "farewell", "ciao", "adios",
        "good night", "goodbye for now", "catch you later", "peace out"
    ]
    if user_lower in farewell_keywords or any(user_lower.strip() == farewell for farewell in farewell_keywords):
        # Return casual farewell response
        casual_farewells = [
            "Goodbye! 👋✨ Have a great day! 🌟",
            "See you later! 😊🎨 Take care! 🚀",
            "Farewell! 👋💫 Hope to chat again soon! 🎯",
            "Bye for now! 😄💻 Enjoy your time at ATL! 🎉",
            "Catch you later! ✨🔧 Stay creative! 📚",
            "Adios! 🎨🚀 Keep exploring the arts and tech world! 💡",
            "Peace out! 🚀🎯 Until next time, take care! 🌟"
        ]
        return random.choice(casual_farewells)
    
    # Check for appreciation messages
    appreciation_keywords = [
        "thank you", "thanks", "appreciate", "grateful", "cheers", "much appreciated",
        "thanks a lot", "thank you so much", "thank you very much", "many thanks"
    ]
    if user_lower in appreciation_keywords or any(user_lower.strip() == appreciation for appreciation in appreciation_keywords):
        # Return casual appreciation response
        casual_appreciations = [
            "You're welcome! 😊✨ I'm glad I could help! 🚀",
            "No problem! 🎨💫 Happy to assist you with ATL info! 💻",
            "Anytime! 👋🌟 If you have more questions, just ask! 🎯",
            "My pleasure! 😄💻 Enjoy exploring ATL's amazing facilities! 🎉",
            "Glad to help! ✨🔧 If you need anything else, let me know! 📚",
            "You're very welcome! 🎨🚀 Keep being creative and curious! 💡",
            "Happy to assist! 🚀🎯 Have a fantastic day at ATL! 🌟"
        ]
        return random.choice(casual_appreciations)
    
    # Check for contact-related queries
    contact_keywords = [
        "contact", "how do i contact", "how can i contact", "how do i reach", "how can i reach", "reach staff", "contact staff", "contact you", "contact info", "contact information", "email", "phone", "call", "reach you", "get in touch", "how do i get in touch", "how can i get in touch", "who can i contact", "ways to contact", "how to contact"
    ]
    if any(k in user_lower for k in contact_keywords):
        sections = [{
            "subtitle": "Contact Information",
            "points": [
                ("Phone Number", "(+852) 3917 5801"),
                ("Email Address", "atlab@hku.hk")
            ],
            "paragraph": "Feel free to reach out to us for any questions about ATL facilities, booking, or services! 📞✨"
        }]
        return format_response("Arts Tech Lab Contact Information", sections)

    # --- NEW: Route to facility info if input matches any facility name ---
    facilities = info_feed.get_base_info().get("facilities", {})
    # Define the helper function locally to avoid import issues
    def find_best_facility_match_here(facilities, user_input):
        """Find the best matching facility from user input"""
        if not facilities:
            return None
            
        user_lower = user_input.lower()
        facility_names = list(facilities.keys())
        
        # Direct substring match
        for facility in facility_names:
            if facility.lower() in user_lower or user_lower in facility.lower():
                return facility
        
        # Fuzzy matching
        import difflib
        best_match = None
        best_ratio = 0
        
        for facility in facility_names:
            ratio = difflib.SequenceMatcher(None, facility.lower(), user_lower).ratio()
            if ratio > best_ratio and ratio > 0.6:  # Threshold for acceptable match
                best_ratio = ratio
                best_match = facility
        
        return best_match
    
    matched_facility = find_best_facility_match_here(facilities, user_input)
    if matched_facility:
        return generate_facility_response(info_feed, user_input, qa_sections=None)

    # Do NOT get context from info_feed first
    context = ""
    # Only get context from info_feed as a fallback if no direct match is found

    # Simple intent classification for response selection
    try:
        # Create intent categories based on keywords
        intent_keywords = {
            "facility": ["facility", "room", "space", "lounge", "xr", "meeting", "research"],
            "pricing": ["price", "cost", "fee", "rental", "charge", "rate"],
            "booking": ["book", "booking", "reserve", "reservation", "schedule", "appointment"],
            "equipment": ["equipment", "hardware", "device", "machine", "gpu"],
            "software": ["software", "program", "application", "tool"],
            "staff": ["staff", "team", "dr.", "mr.", "engineer", "coordinator", "practitioner", "aiden", "jenny", "kal", "lawrence"],
            "internship": ["intern", "internship", "position", "job"],
            "event": ["event", "activity", "lecture", "workshop", "exhibition", "presentation"],
            "policy": ["policy", "requirement", "responsibility", "rule"],
            "tool": ["tool", "ai", "ollama", "chatgpt", "atlhpc"],
            "general": ["what", "how", "when", "where", "who", "tell me"]
        }
        # Determine intent
        detected_intent = "general"
        max_score = 0
        for intent, keywords in intent_keywords.items():
            score = sum(1 for k in keywords if k in user_lower)
            if score > max_score:
                max_score = score
                detected_intent = intent
        # --- NEW: Handle specific intents with structured RAG data ---
        if detected_intent == "staff":
            return generate_staff_response(info_feed, user_input)
        
        if detected_intent == "event":
            return generate_event_response(info_feed, user_input)

        # Check for comprehensive questions that need bullet points
        comprehensive_keywords = ["all", "everything", "list", "overview", "summary", "complete", "comprehensive"]
        is_comprehensive = any(k in user_lower for k in comprehensive_keywords)

        # Try direct match logic first (e.g., direct facility lookup, direct Q&A, etc.)
        # ... (your direct match logic here) ...
        response = None
        # If no direct match, then use info_feed as fallback
        if not response and info_feed:
            context = info_feed.get_context_for_question(user_input)
            # Extract relevant Q&A from context
            lines = context.split('\n')
            qa_sections = []
            current_section = []
            for line in lines:
                if line.startswith('Q: ') or line.startswith('A: '):
                    current_section.append(line)
                elif current_section:
                    qa_sections.append('\n'.join(current_section))
                    current_section = []
            if current_section:
                qa_sections.append('\n'.join(current_section))
            # Create enhanced response based on intent
            if detected_intent == "pricing":
                response = generate_pricing_response(info_feed, user_input)
            elif detected_intent == "booking":
                response = generate_booking_response(info_feed, user_input)
            elif detected_intent == "facility":
                response = generate_facility_response(info_feed, user_input, qa_sections)
            elif is_comprehensive:
                response = generate_comprehensive_response(generator, user_input, context, info_feed)
            else:
                response = extract_enhanced_qa_response(generator, qa_sections, detected_intent, context)
        if not response:
            response = "I don't have specific information about that. Please try asking about ATL facilities, equipment, pricing, staff, internships, events, policies, or tools. If you need further assistance, please contact ATL staff."
        # Calculate timing
        total_time = time.time() - start_time
        # Print timing information
        timing_info = f"[Timing] Total: {total_time:.2f}s | Enhanced lightweight mode with RAG"
        print(f"\n{timing_info}")
        # Log timing information to file
        timing_logger = logging.getLogger("timing")
        timing_logger.info(timing_info)
        # Standardize terminology
        try:
            from terminology import TerminologyStandardizer
            standardizer = TerminologyStandardizer()
            response = standardizer.standardize_text(response, "english")
        except ImportError:
            pass
        # Post-processing for specific phrases and spacing issues
        response = response.replace('TheUniversityofHongKong', 'The University of Hong Kong')
        response = response.replace('artsandtechnology', 'arts and technology')
        
        # Add website links if available
        if WEBSITE_LINKS_AVAILABLE:
            response = add_website_links_to_response(response, user_input)
        
        return response
    except Exception as e:
        logger.error(f"Error in lightweight response generation: {e}")
        return "I'm having trouble processing your request. Please try again."

def extract_qa_response(qa_sections, detected_intent):
    """Extract and structure Q&A response from sections"""
    if not qa_sections:
        return ""
    
    # Group related information
    facilities_info = []
    pricing_info = []
    general_info = []
    equipment_info = []
    contact_info = []
    
    for section in qa_sections:
        section_lower = section.lower()
        if any(keyword in section_lower for keyword in ["facility", "room", "space"]):
            facilities_info.append(section)
        elif any(keyword in section_lower for keyword in ["price", "cost", "fee", "rental"]):
            pricing_info.append(section)
        elif any(keyword in section_lower for keyword in ["equipment", "hardware", "software"]):
            equipment_info.append(section)
        elif any(keyword in section_lower for keyword in ["contact", "phone", "email"]):
            contact_info.append(section)
        else:
            general_info.append(section)
    
    # Build structured response
    response_parts = []
    
    if general_info:
        response_parts.extend(general_info[:2])  # Limit to avoid overwhelming
    
    if facilities_info:
        response_parts.append(f"🏢 **Facilities**: {' '.join(facilities_info[:2])}")
    
    if equipment_info:
        response_parts.append(f"🔧 **Equipment**: {' '.join(equipment_info[:2])}")
    
    if pricing_info:
        response_parts.append(f"💰 **Pricing**: {' '.join(pricing_info[:2])}")
    
    if contact_info:
        response_parts.append(f"📞 **Contact**: {' '.join(contact_info[:1])}")
    
    return "\n\n".join(response_parts)

def generate_comprehensive_response(generator, user_input, context, info_feed):
    """Generate a comprehensive response using the model"""
    try:
        # Enhanced prompt for better responses
        system_prompt = f"""You are an expert assistant for the Arts Technology Lab (ATL) at The University of Hong Kong. 
Provide detailed, accurate information about ATL facilities, equipment, pricing, and services.

Relevant Information:
{context}

User Question: {user_input}

Please provide a comprehensive, well-structured response with specific details. Use bullet points and clear formatting where appropriate."""
        
        # Generate response
        outputs = generator(system_prompt, num_return_sequences=1, temperature=0.6, do_sample=True, pad_token_id=generator.tokenizer.eos_token_id)
        
        if outputs and len(outputs) > 0:
            response = outputs[0]['generated_text']
            # Extract only the new part
            if system_prompt in response:
                response = response.replace(system_prompt, "").strip()
            
            if response and len(response) > 20:
                return response
        
        # Fallback to structured response
        return generate_structured_fallback_response(user_input, context, info_feed)
        
    except Exception as e:
        logger.error(f"Error in comprehensive response generation: {e}")
        return generate_structured_fallback_response(user_input, context, info_feed)

def generate_structured_fallback_response(user_input, context, info_feed):
    """Generate a structured fallback response when model fails"""
    if not context:
        return "I don't have specific information about that. Please contact the Arts Tech Lab directly for more details."
    
    # Extract key information from context
    sections = context.split('\n\n')
    structured_info = extract_and_structure_context(context, user_input)
    
    if structured_info:
        return format_response("ATL Information", structured_info)
    else:
        # Simple context-based response
        return f"Based on available information:\n\n{context[:500]}..."

def format_response(title, sections):
    """
    Format the chatbot response with a title, subtitles, bullet points, and friendly explanations.
    sections: List of dicts, each with 'subtitle', 'points' (list of (point, explanation)), and optional 'paragraph'.
    """
    response = f"**{title}** 🎯\n\n"
    
    for i, section in enumerate(sections):
        if 'subtitle' in section:
            # Add emoji based on subtitle content
            emoji = get_section_emoji(section['subtitle'])
            response += f"__{section['subtitle']}__ {emoji}\n\n"
        
        if 'points' in section and section['points']:
            grouped_points = group_similar_points(section['points'])
            for group_title, items in grouped_points.items():
                # If only one item and it's a long paragraph, print as plain text
                if len(items) == 1 and len(items[0][0]) > 120:
                    response += f"{items[0][0]}"
                    if items[0][1]:
                        response += f" {items[0][1]}"
                    response += "\n"
                elif group_title == "General":
                    for point, explanation in items:
                        response += f"• **{point}**"
                        if explanation:
                            response += f": {explanation}"
                        response += "\n"
                else:
                    # Always show group title for non-General groups, even for single items
                    category_emoji = get_category_emoji(group_title)
                    response += f"**{group_title}** {category_emoji}\n"
                    for point, explanation in items:
                        response += f"  • {point}"
                        if explanation:
                            response += f": {explanation}"
                        response += "\n"
                    response += "\n"
            response += "\n"
        if 'paragraph' in section:
            response += f"{section['paragraph']}\n\n"
        if 'points' in section and len(section['points']) > 2:
            summary = generate_section_summary(section['subtitle'], section['points'])
            if summary:
                response += f"**Summary** 📝: {summary}\n\n"
    response += "If you have more questions, feel free to ask! 😊\nFor further assistance, you may contact ATL staff. 📧"
    return response

def extract_and_structure_context(context, user_input):
    """Extract and structure context into organized sections"""
    if not context:
        return {}
    
    sections = {}
    current_section = "General Information"
    
    lines = context.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Detect section headers
        if line.startswith('**') and line.endswith('**'):
            current_section = line.strip('*')
            if current_section not in sections:
                sections[current_section] = []
        elif line.startswith('•') or line.startswith('-'):
            # Bullet point
            point = line.lstrip('•-').strip()
            if point:
                if current_section not in sections:
                    sections[current_section] = []
                sections[current_section].append(point)
        elif ':' in line and len(line) < 200:
            # Key-value pair
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(line)
        elif len(line) > 10 and len(line) < 300:
            # Regular information
            if current_section not in sections:
                sections[current_section] = []
            sections[current_section].append(line)
    
    return sections

def extract_enhanced_qa_response(generator, qa_sections, detected_intent, context):
    """Extract response from Q&A sections with multilingual T5 enhancement, in the user's language"""
    if qa_sections:
        qa_text = qa_sections[0]
        if 'A: ' in qa_text:
            answer_parts = []
            lines = qa_text.split('\n')
            for line in lines:
                if line.startswith('A: '):
                    answer_parts.append(line[3:])
            if answer_parts:
                base_response = ' '.join(answer_parts)
                from text_processors import detect_language
                lang = detect_language(base_response)
                try:
                    if generator and hasattr(generator, 'model'):
                        enhancement_prompt = f"Enhance and expand this answer about {detected_intent} in English, with bullet points: {base_response}"
                        result = generator(enhancement_prompt, num_return_sequences=1, do_sample=True, temperature=0.5, top_p=0.9, pad_token_id=generator.tokenizer.eos_token_id)
                        enhanced_response = result[0]['generated_text']
                        
                        # Remove the prompt from the enhanced response to prevent prompt leakage
                        if enhancement_prompt in enhanced_response:
                            enhanced_response = enhanced_response.replace(enhancement_prompt, "").strip()
                        
                        if len(enhanced_response) > len(base_response) * 0.8 and enhanced_response.strip() != enhancement_prompt.strip():
                            response = enhanced_response
                        else:
                            response = base_response
                    else:
                        response = base_response
                except:
                    response = base_response
                
                # Structure the response using format_response
                sections = [{
                    "subtitle": f"Information about {detected_intent}",
                    "points": [(response, "")],
                    "paragraph": f"Let me know if you need more specific details about {detected_intent}!"
                }]
                return format_response(f"{detected_intent.title()} Information", sections)
            else:
                sections = [{
                    "subtitle": f"About {detected_intent}",
                    "points": [],
                    "paragraph": f"Based on the available information about {detected_intent}, I can help you with that. Please ask a more specific question for detailed information."
                }]
                return format_response(f"{detected_intent.title()} Information", sections)
        else:
            sections = [{
                "subtitle": f"About {detected_intent}",
                "points": [],
                "paragraph": f"Based on the available information about {detected_intent}, I can help you with that. Please ask a more specific question for detailed information."
            }]
            return format_response(f"{detected_intent.title()} Information", sections)
    else:
        sections = [{
            "subtitle": f"About {detected_intent}",
            "points": [],
            "paragraph": f"Based on the available information about {detected_intent}, I can help you with that. Please ask a more specific question for detailed information."
        }]
        return format_response(f"{detected_intent.title()} Information", sections)

def generate_response(model, tokenizer, user_input, thinking_mode=False, info_feed=None, lightweight_mode=False):
    """Main response generation function"""
    try:
        start_time = time.time()
        
        # Import here to avoid circular imports
        from text_processors import is_non_text_input, get_friendly_non_text_response
        
        # Check for non-text input first
        if is_non_text_input(user_input):
            return get_friendly_non_text_response()
        
        # Handle special cases
        if any(keyword in user_input.lower() for keyword in ["staff", "team", "member", "people", "person"]):
            return generate_staff_response(info_feed, user_input)
        
        if any(keyword in user_input.lower() for keyword in ["event", "activity", "workshop", "seminar"]):
            return generate_event_response(info_feed, user_input)
        
        if any(keyword in user_input.lower() for keyword in ["price", "cost", "fee", "rent", "rental", "booking"]):
            return generate_pricing_response(info_feed, user_input)
        
        if any(keyword in user_input.lower() for keyword in ["facility", "room", "space"]):
            context = info_feed.get_context_for_question(user_input) if info_feed else ""
            return generate_facility_response(info_feed, user_input, [context] if context else [])
        
        # Generate response using model
        if lightweight_mode and hasattr(model, '__call__'):
            response = generate_lightweight_response(model, user_input, info_feed)
        else:
            context = info_feed.get_context_for_question(user_input) if info_feed else ""
            if hasattr(model, '__call__'):
                response = generate_comprehensive_response(model, user_input, context, info_feed)
            else:
                response = generate_lightweight_response(model, user_input, info_feed)
        
        # Add website links if available
        try:
            from website_links import add_website_links_to_response
            response = add_website_links_to_response(response, user_input)
        except ImportError:
            pass
        
        # Log timing
        end_time = time.time()
        timing_logger = logging.getLogger("timing")
        timing_logger.info(f"Response generated in {end_time - start_time:.2f} seconds")
        
        return response
        
    except Exception as e:
        logger.error(f"Error in generate_response: {e}")
        return "I apologize, but I'm having trouble processing your request right now. Please try again or contact the Arts Tech Lab directly for assistance."

def generate_pricing_response(info_feed, user_input):
    user_lower = user_input.lower()
    facility_keywords = ["lounge", "xr space", "meeting room", "research room", "seasonal tech room"]
    specific_facility = None
    for facility in facility_keywords:
        if facility in user_lower:
            specific_facility = facility
            break
    if specific_facility:
        return generate_specific_facility_pricing(info_feed, specific_facility, user_input)
    else:
        return generate_all_facilities_pricing(info_feed, user_input)

def generate_specific_facility_pricing(info_feed, facility_name, user_input):
    from text_processors import detect_language
    lang = detect_language(user_input)
    facilities = info_feed.get_base_info(lang).get("facilities", {})
    # Map facility keywords to actual facility names
    facility_mapping = {
        "lounge": "Lounge",
        "xr space": "XR Space", 
        "meeting room": "Meeting Room",
        "research room": "Research Room",
        "seasonal tech room": "Seasonal Tech Room"
    }
    actual_facility_name = facility_mapping.get(facility_name, facility_name.title())
    if actual_facility_name in facilities:
        facility_info = facilities[actual_facility_name]
        points = [
            ("Area", facility_info.get('area', 'N/A')),
            ("Capacity", facility_info.get('capacity', 'N/A')),
        ]
        if facility_info.get('features'):
            points.append(("Features", ', '.join(facility_info['features'])))
        if facility_info.get('equipment'):
            points.append(("Equipment", ', '.join(facility_info['equipment'])))
        if facility_info.get('software'):
            points.append(("Software", ', '.join(facility_info['software'])))
        pricing_points = []
        if "pricing" in facility_info and facility_info["pricing"]:
            for category, rate in facility_info["pricing"].items():
                pricing_points.append((category, rate))
        else:
            pricing_points.append(("Pricing", "Information not available for this facility"))
        if facility_info.get("reservation_rate"):
            points.append(("Reservation Rate", facility_info['reservation_rate']))
        sections = [
            {
                "subtitle": actual_facility_name,
                "points": points,
                "paragraph": f"Here's detailed information about the {actual_facility_name}."
            },
            {
                "subtitle": "Pricing Information",
                "points": pricing_points,
                "paragraph": "Let me know if you want to know about other facilities or need help with the booking process!"
            }
        ]
        return format_response(f"{actual_facility_name} - Facility Pricing", sections)
    else:
        # Fallback: show all facilities
        return generate_all_facilities_pricing(info_feed, user_input)

def generate_all_facilities_pricing(info_feed, user_input):
    from text_processors import detect_language
    lang = detect_language(user_input)
    facilities = info_feed.get_base_info(lang).get("facilities", {})
    sections = []
    for facility_name, facility_info in facilities.items():
        points = [
            ("Area", facility_info.get('area', 'N/A')),
            ("Capacity", facility_info.get('capacity', 'N/A')),
        ]
        if "pricing" in facility_info and facility_info["pricing"]:
            for category, rate in facility_info["pricing"].items():
                points.append((f"{category}", rate))
        else:
            points.append(("Pricing", "Information available upon request"))
        if facility_info.get('features'):
            for feature in facility_info['features'][:3]:
                points.append((f"Key Feature: {feature}", ""))
        sections.append({
            "subtitle": facility_name,
            "points": points,
            "paragraph": f"Pricing for {facility_name} is flexible and depends on your user category. Let me know if you want a quote!"
        })
    # Pricing categories
    pricing_points = [
        ("External Organizations", "Highest rates"),
        ("Non-UGC Non-Arts Programs", "High rates"),
        ("UGC Non-Arts Programs", "Medium rates"),
        ("Non-UGC Arts Programs", "Lower rates"),
        ("UGC Arts Programs", "Fees waived")
    ]
    sections.append({
        "subtitle": "Pricing Categories",
        "points": pricing_points,
        "paragraph": "We offer different rates for different user types to make ATL accessible to everyone!"
    })
    # Booking requirements
    booking_points = [
        ("Minimum charge", "4 hours per room"),
        ("Faculty advisor booking required", ""),
        ("7-30 days advance notice", ""),
        ("Confirmation within 7 days", "")
    ]
    sections.append({
        "subtitle": "Booking Requirements",
        "points": booking_points,
        "paragraph": "Booking is simple! Just follow these steps and you're set."
    })
    sections.append({
        "subtitle": "Need Help?",
        "points": [],
        "paragraph": "Let me know which facility you want to book, and I can provide detailed information for your user category!"
    })
    return format_response("ATL Facilities and Pricing Overview", sections)

def generate_booking_response(info_feed, user_input):
    from text_processors import detect_language
    lang = detect_language(user_input)
    facilities = info_feed.get_base_info(lang).get("facilities", {})
    sections = []
    booking_points = [
        ("All bookings must be made through a faculty advisor", ""),
        ("Reservations require 7-30 days advance notice", ""),
        ("Confirmation will be provided within 7 days of request", "")
    ]
    sections.append({
        "subtitle": "Booking Process",
        "points": booking_points,
        "paragraph": "Booking is easy! Just ask your faculty advisor to help you reserve a space."
    })
    requirements_points = [
        ("Minimum charge", "4 hours per room"),
        ("Fractions of an hour are treated as full hours", ""),
        ("Faculty advisor must submit the booking request", ""),
        ("Users must be eligible (students with faculty supervision, etc.)", "")
    ]
    sections.append({
        "subtitle": "Booking Requirements",
        "points": requirements_points,
        "paragraph": "These requirements help us keep the lab running smoothly for everyone!"
    })
    responsibilities_points = [
        ("Be mindful while using rooms and equipment", ""),
        ("Responsible for any damage to facility property", ""),
        ("Switch off all electronic systems at the end of booking", ""),
        ("Keep the place clean and tidy", ""),
        ("Responsible for any irremovable marks", "")
    ]
    sections.append({
        "subtitle": "User Responsibilities",
        "points": responsibilities_points,
        "paragraph": "We appreciate your help in keeping ATL a great place for everyone!"
    })
    # Facilities for booking
    for facility_name, facility_info in facilities.items():
        points = [
            ("Area", facility_info.get('area', 'N/A')),
            ("Capacity", facility_info.get('capacity', 'N/A')),
        ]
        # Don't add pricing overview to points - pricing will be shown in separate sections when requested
        if facility_info.get('features'):
            for feature in facility_info['features'][:2]:
                points.append((f"Key Feature: {feature}", ""))
        sections.append({
            "subtitle": facility_name,
            "points": points,
            "paragraph": f"Let me know if you want to book {facility_name} or need more details!"
        })
    # Pricing categories
    pricing_points = [
        ("External Organizations", "Highest rates"),
        ("Non-UGC Non-Arts Programs", "High rates"),
        ("UGC Non-Arts Programs", "Medium rates"),
        ("Non-UGC Arts Programs", "Lower rates"),
        ("UGC Arts Programs", "Fees waived")
    ]
    sections.append({
        "subtitle": "Pricing Categories",
        "points": pricing_points,
        "paragraph": "We offer different rates for different user types!"
    })
    # Contact info
    contact_points = [
        ("Email", "atlab@hku.hk"),
        ("Phone", "(+852) 3917 5801"),
        ("Location", "Run Run Shaw Tower (RRST-4.35), Centennial Campus")
    ]
    sections.append({
        "subtitle": "Contact Information",
        "points": contact_points,
        "paragraph": "Reach out if you need help with booking or have any questions!"
    })
    sections.append({
        "subtitle": "Which facility would you like to book?",
        "points": [],
        "paragraph": "I can provide detailed pricing and information for any specific facility."
    })
    return format_response("ATL Booking Information and Requirements", sections)

def generate_facility_response(info_feed, user_input, qa_sections):
    user_lower = user_input.lower()
    facilities = info_feed.get_base_info().get("facilities", {})
    
    # Define local helper functions to match original
    def normalize_facility_name_local(name):
        """Normalize facility name for matching (lowercase, remove spaces and special chars)"""
        import re
        return re.sub(r'[^a-z0-9]', '', name.lower())

    def extract_facility_from_question_local(user_input):
        """Extract the facility/entity name from natural language questions like 'what is ...', 'tell me about ...', etc."""
        import re
        patterns = [
            r"what is (.+)",
            r"tell me about (.+)",
            r"describe (.+)",
            r"give me information about (.+)",
            r"can you explain (.+)",
            r"(.+) information",
        ]
        user_lower = user_input.lower()
        for pattern in patterns:
            match = re.search(pattern, user_lower)
            if match:
                # Remove trailing punctuation
                entity = match.group(1).strip().rstrip('?.!')
                return entity
        return None

    def find_best_facility_match_local(facilities, user_input):
        """Find the best matching facility name from the facilities dict given the user input."""
        import difflib
        norm_input = normalize_facility_name_local(user_input)
        facility_names = list(facilities.keys())
        norm_names = [normalize_facility_name_local(name) for name in facility_names]
        # Direct match
        for i, norm_name in enumerate(norm_names):
            if norm_input == norm_name:
                return facility_names[i]
        # Substring match
        for i, norm_name in enumerate(norm_names):
            if norm_input in norm_name or norm_name in norm_input:
                return facility_names[i]
        # Fuzzy match
        match = difflib.get_close_matches(norm_input, norm_names, n=1, cutoff=0.6)
        if match:
            idx = norm_names.index(match[0])
            return facility_names[idx]
        return None
    
    # Debug: print available facilities and normalized user input
    print("[DEBUG] User input:", user_input)
    print("[DEBUG] Normalized user input:", normalize_facility_name_local(user_input))
    print("[DEBUG] Available facilities:", list(facilities.keys()))
    print("[DEBUG] Normalized facility names:", [normalize_facility_name_local(name) for name in facilities.keys()])
    # Try to extract facility/entity from natural language question
    facility_query = extract_facility_from_question_local(user_input)
    specific_facility = None
    if facility_query:
        specific_facility = find_best_facility_match_local(facilities, facility_query)
    else:
        # Try to match any facility name in the user input
        specific_facility = find_best_facility_match_local(facilities, user_input)
    if specific_facility:
        return generate_specific_facility_info(info_feed, specific_facility, user_input)
    else:
        # Fallback: list all facilities in the user's language
        sections = [{
            "subtitle": "Available Facilities",
            "points": [(name, "") for name in facilities],
            "paragraph": "Please specify which one you'd like more details about. If you need further assistance, please contact Arts Tech Lab at HKU staff."
        }]
        return format_response("Facility Not Found", sections)

def generate_specific_facility_info(info_feed, facility_name, user_input):
    # Remove language detection and Chinese handling
    facilities = info_feed.get_base_info().get("facilities", {})
    
    def normalize_facility_name_local(name):
        """Normalize facility name for matching (lowercase, remove spaces and special chars)"""
        import re
        return re.sub(r'[^a-z0-9]', '', name.lower())
    
    # Use robust matching
    target_name = facility_name
    def find_facility_key(facilities_dict, target_name):
        norm_target = normalize_facility_name_local(target_name)
        for key in facilities_dict.keys():
            if normalize_facility_name_local(key) == norm_target:
                return key
        for key in facilities_dict.keys():
            if norm_target in normalize_facility_name_local(key) or normalize_facility_name_local(key) in norm_target:
                return key
        import difflib
        norm_keys = [normalize_facility_name_local(k) for k in facilities_dict.keys()]
        match = difflib.get_close_matches(norm_target, norm_keys, n=1, cutoff=0.6)
        if match:
            idx = norm_keys.index(match[0])
            return list(facilities_dict.keys())[idx]
        return None
    facility_key = find_facility_key(facilities, target_name)
    facility_info = facilities.get(facility_key) if facility_key else None
    if facility_key and facility_info:
        points = [
            ("Area", facility_info.get('area', 'N/A')),
            ("Capacity", facility_info.get('capacity', 'N/A')),
        ]
        desc = facility_info.get('description', None)
        if desc:
            points.append(("Description", desc))
        features = facility_info.get('features', facility_info.get('Features', None))
        if features:
            if isinstance(features, list):
                for feature in features:
                    points.append((f"Feature: {feature}", ""))
            elif isinstance(features, str):
                points.append((f"Feature: {features}", ""))
        equipment = facility_info.get('equipment', None)
        if equipment:
            if isinstance(equipment, list):
                for eq in equipment:
                    points.append((f"Equipment: {eq}", ""))
            elif isinstance(equipment, str):
                points.append((f"Equipment: {equipment}", ""))
        hardware = facility_info.get('hardware', None)
        if hardware:
            if isinstance(hardware, list):
                for hw in hardware:
                    points.append((f"Hardware: {hw}", ""))
            elif isinstance(hardware, str):
                points.append((f"Hardware: {hardware}", ""))
        software = facility_info.get('software', None)
        if software:
            if isinstance(software, list):
                for sw in software:
                    points.append((f"Software: {sw}", ""))
            elif isinstance(software, str):
                points.append((f"Software: {software}", ""))
        # Don't add pricing to main points - it will be handled in separate section
        configuration = facility_info.get('configuration', None)
        if configuration:
            points.append(("Configuration", configuration))
        permit = facility_info.get('permit', None)
        if permit:
            points.append(("Permit Required", permit))
        
        # Create sections with pricing overview if available
        sections = [{
            "subtitle": f"{facility_key} - Complete Information",
            "points": points,
            "paragraph": f"Let me know if you want to know about booking procedures or pricing for {facility_key}!"
        }]
        
        # Add pricing section if available
        pricing = facility_info.get('pricing', None)
        if pricing:
            pricing_points = []
            for category, rate in pricing.items():
                pricing_points.append((category, rate))
            sections.append({
                "subtitle": "Pricing & Fees",
                "points": pricing_points,
                "paragraph": "Rates vary by user category. Contact ATL for booking and payment procedures."
            })
        
        return format_response(f"{facility_key} - Facility Details", sections)
    else:
        # Fallback: list all facilities
        sections = [{
            "subtitle": "Available Facilities",
            "points": [(name, "") for name in facilities],
            "paragraph": "Please specify which one you'd like more details about. If you need further assistance, please contact Arts Tech Lab at HKU staff."
        }]
        return format_response("Facility Not Found", sections)

def generate_all_facilities_structured(info_feed, user_input):
    """Generate structured information about all facilities."""
    base_info = info_feed.get_base_info('english')
    facilities = base_info.get("facilities", {})
    
    if not facilities:
        return "I don't have information about ATL facilities available. Please visit the ATL website or contact us directly."
    
    response = "## 🏢 ATL Facilities Overview\n\n"
    
    for facility_name, facility_info in facilities.items():
        response += f"### {facility_name}\n"
        
        if facility_info.get("description"):
            response += f"{facility_info['description']}\n"
        
        details = []
        if facility_info.get("area"):
            details.append(f"Area: {facility_info['area']}")
        if facility_info.get("capacity"):
            details.append(f"Capacity: {facility_info['capacity']}")
        
        if details:
            response += f"*{' | '.join(details)}*\n"
        
        response += "\n"
    
    response += "*For detailed information about any facility, please ask specifically or contact ATL directly.*"
    
    return response

def generate_all_equipment_structured(info_feed, user_input):
    """Generate structured information about all equipment."""
    base_info = info_feed.get_base_info('english')
    equipment = base_info.get("equipment", {})
    
    if not equipment:
        return "I don't have equipment information available. Please contact ATL for details about available equipment."
    
    response = "## 🔧 ATL Equipment\n\n"
    
    for category, items in equipment.items():
        response += f"### {category}\n"
        if isinstance(items, list):
            for item in items:
                response += f"• {item}\n"
        elif isinstance(items, str):
            response += f"• {items}\n"
        response += "\n"
    
    return response

def generate_all_software_structured(info_feed, user_input):
    """Generate structured information about all software."""
    base_info = info_feed.get_base_info('english')
    software = base_info.get("software", {})
    
    if not software:
        return "I don't have software information available. Please contact ATL for details about available software."
    
    response = "## 💻 ATL Software\n\n"
    
    for category, items in software.items():
        response += f"### {category}\n"
        if isinstance(items, list):
            for item in items:
                response += f"• {item}\n"
        elif isinstance(items, str):
            response += f"• {items}\n"
        response += "\n"
    
    return response

def get_all_staff_names(info_feed):
    """Extract all staff names from the available data sources."""
    try:
        # Load staff info from JSON file
        staff_file_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'source_data', 'staff_info.json')
        with open(staff_file_path, 'r', encoding='utf-8') as f:
            staff_data = json.load(f)
            
        staff_list = []
        for staff in staff_data.get('core_staff', []):
            staff_list.append(f"{staff['name']} ({staff['title']})")
            
        return staff_list
    except Exception as e:
        logger.error(f"Error loading staff info: {e}")
        return []

def generate_staff_response(info_feed, user_input):
    """Generate a response for staff-related queries."""
    staff_list = get_all_staff_names(info_feed)
    
    if not staff_list:
        return "I don't have access to staff information at the moment. Please visit the ATL website for team details."
    
    # Check if asking for a specific staff member
    user_lower = user_input.lower()
    
    # Check if the user is asking for a specific person
    for staff_name in staff_list:
        name_parts = staff_name.lower().split('(')[0].strip().split()
        if any(part in user_lower for part in name_parts if len(part) > 2):
            return f"Here's information about {staff_name} at ATL. For more details about their role and expertise, please visit the ATL website or contact us directly. 👤"
    
    # If we have staff information, provide the list
    staff_list_str = "\n".join(staff_list)
    return f"Here are the staff members at ATL:\n\n{staff_list_str}\n\nYou can find more details about their roles on the ATL website. 👥"

def generate_event_response(info_feed, user_input):
    """Generate a response for event-related queries."""
    if not info_feed or not hasattr(info_feed, 'rag_retriever') or not info_feed.rag_retriever:
        return "I can't access event information at the moment. Please try again later. 😥"

    try:
        event_titles = info_feed.rag_retriever.get_all_event_titles()
        if not event_titles:
            return "There are no current events listed. Please check the ATL website for the latest updates! 🎪"

        # Check if the user is asking for a specific event (substring match, case-insensitive)
        user_lower = user_input.lower()
        for title in event_titles:
            if title.lower() in user_lower or user_lower in title.lower():
                details = info_feed.rag_retriever.get_event_details(title)
                if details:
                    lines = [
                        "Here's what I found about this event at ATL:",
                        f"• **Title**: {details['title']}"
                    ]
                    if details.get('date'):
                        lines.append(f"• **Date**: {details['date']} 📅")
                    if details.get('description'):
                        lines.append(f"• **Description**: {details['description']} 📝")
                    return "\n".join(lines)

        # If no specific event is asked, list all available events organized by category
        return organize_events_by_category(event_titles)
    except:
        return "I can't access event information at the moment. Please check the ATL website for the latest updates! 🎪"

def group_similar_points(points):
    """
    Group similar points to avoid repetitive prefixes.
    Returns a dict with group titles as keys and lists of (point, explanation) as values.
    """
    grouped = {}
    
    for point, explanation in points:
        # Check for common prefixes that should be grouped
        point_lower = point.lower()
        
        if point_lower.startswith("feature:"):
            clean_point = point[8:].strip()  # Remove "Feature:" prefix
            if "Key Features" not in grouped:
                grouped["Key Features"] = []
            grouped["Key Features"].append((clean_point, explanation))
        elif point_lower.startswith("hardware:"):
            clean_point = point[9:].strip()  # Remove "Hardware:" prefix
            if "Hardware" not in grouped:
                grouped["Hardware"] = []
            grouped["Hardware"].append((clean_point, explanation))
        elif point_lower.startswith("software:"):
            clean_point = point[9:].strip()  # Remove "Software:" prefix
            if "Software" not in grouped:
                grouped["Software"] = []
            grouped["Software"].append((clean_point, explanation))
        elif point_lower.startswith("equipment:"):
            clean_point = point[10:].strip()  # Remove "Equipment:" prefix
            if "Equipment" not in grouped:
                grouped["Equipment"] = []
            grouped["Equipment"].append((clean_point, explanation))
        elif point_lower.startswith("key feature:"):
            clean_point = point[12:].strip()  # Remove "Key Feature:" prefix
            if "Key Features" not in grouped:
                grouped["Key Features"] = []
            grouped["Key Features"].append((clean_point, explanation))
        elif any(keyword in point_lower for keyword in ["external", "non-ugc", "ugc", "waived", "dollars/hour", "hong kong"]):
            # Pricing information
            if "Pricing" not in grouped:
                grouped["Pricing"] = []
            grouped["Pricing"].append((point, explanation))
        elif any(keyword in point_lower for keyword in ["area", "capacity", "square meters", "people"]):
            # Basic information
            if "Basic Information" not in grouped:
                grouped["Basic Information"] = []
            grouped["Basic Information"].append((point, explanation))
        elif any(keyword in point_lower for keyword in ["permit", "permission", "requirement"]):
            # Requirements
            if "Requirements" not in grouped:
                grouped["Requirements"] = []
            grouped["Requirements"].append((point, explanation))
        else:
            # Regular point without grouping
            if "General" not in grouped:
                grouped["General"] = []
            grouped["General"].append((point, explanation))
    
    return grouped

def get_section_emoji(subtitle):
    """Get appropriate emoji for section subtitle"""
    subtitle_lower = subtitle.lower()
    
    if "basic information" in subtitle_lower or "overview" in subtitle_lower:
        return "ℹ️"
    elif "key features" in subtitle_lower or "features" in subtitle_lower:
        return "✨"
    elif "available equipment" in subtitle_lower or "equipment" in subtitle_lower:
        return "🔧"
    elif "hardware systems" in subtitle_lower or "hardware" in subtitle_lower:
        return "💻"
    elif "software tools" in subtitle_lower or "software" in subtitle_lower:
        return "🖥️"
    elif "pricing information" in subtitle_lower or "pricing" in subtitle_lower or "cost" in subtitle_lower:
        return "💰"
    elif "booking process" in subtitle_lower or "booking" in subtitle_lower:
        return "📅"
    elif "booking requirements" in subtitle_lower or "requirements" in subtitle_lower:
        return "📋"
    elif "user responsibilities" in subtitle_lower or "responsibilities" in subtitle_lower:
        return "🤝"
    elif "available facilities" in subtitle_lower or "facilities" in subtitle_lower:
        return "🏢"
    elif "pricing categories" in subtitle_lower:
        return "💳"
    elif "contact information" in subtitle_lower or "contact" in subtitle_lower:
        return "📞"
    elif "next steps" in subtitle_lower:
        return "➡️"
    elif "permit" in subtitle_lower or "permission" in subtitle_lower:
        return "✅"
    else:
        return "📌"

def get_category_emoji(category):
    """Get appropriate emoji for category titles"""
    category_lower = category.lower()
    
    if "pricing" in category_lower or "cost" in category_lower or "fee" in category_lower:
        return "💰"
    elif "features" in category_lower:
        return "✨"
    elif "hardware" in category_lower:
        return "💻"
    elif "software" in category_lower:
        return "🖥️"
    elif "equipment" in category_lower:
        return "🔧"
    elif "basic information" in category_lower or "overview" in category_lower:
        return "ℹ️"
    elif "requirements" in category_lower or "permit" in category_lower:
        return "✅"
    elif "key features" in category_lower:
        return "⭐"
    else:
        return "📌"

def generate_section_summary(subtitle, points):
    """Generate a summary paragraph for a section based on its points"""
    if not points:
        return None
    
    # Extract key information from points
    key_info = []
    for point, explanation in points:
        if explanation:
            key_info.append(f"{point} ({explanation})")
        else:
            key_info.append(point)
    
    # Generate appropriate summary based on subtitle
    subtitle_lower = subtitle.lower()
    
    if "basic information" in subtitle_lower:
        return f"This facility provides essential space and capacity for your activities! 🏠✨"
    
    elif "key features" in subtitle_lower:
        return f"These features make this space versatile and suitable for various creative and technical projects! ✨🚀"
    
    elif "available equipment" in subtitle_lower or "equipment" in subtitle_lower:
        return f"Professional equipment is available to support your projects and activities! 🔧💪"
    
    elif "hardware systems" in subtitle_lower or "hardware" in subtitle_lower:
        return f"High-performance hardware systems are installed to handle demanding computational tasks! 💻⚡"
    
    elif "software tools" in subtitle_lower or "software" in subtitle_lower:
        return f"Professional software tools are available for creative and technical work! 🖥️🎨"
    
    elif "pricing information" in subtitle_lower or "pricing" in subtitle_lower or "cost" in subtitle_lower:
        return f"Pricing varies based on user category, with different rates for different types of users! 💰📊"
    
    elif "booking process" in subtitle_lower or "booking" in subtitle_lower:
        return f"The booking process involves several steps and requirements to ensure smooth facility access! 📅✅"
    
    elif "booking requirements" in subtitle_lower or "requirements" in subtitle_lower:
        return f"These requirements help maintain facility quality and ensure fair access for all users! 📋🤝"
    
    elif "user responsibilities" in subtitle_lower or "responsibilities" in subtitle_lower:
        return f"These guidelines help ensure everyone has a positive experience and facilities remain in good condition! 🤝🌟"
    
    elif "available facilities" in subtitle_lower or "facilities" in subtitle_lower:
        return f"All facilities are designed for specific activities and group sizes to meet various needs! 🏢🎯"
    
    elif "pricing categories" in subtitle_lower:
        return f"We offer different rates for different user types to make our facilities accessible to everyone! 💳💫"
    
    elif "contact information" in subtitle_lower or "contact" in subtitle_lower:
        return f"Multiple contact channels are available for questions and support! 📞💬"
    
    elif "next steps" in subtitle_lower:
        return f"Follow these steps to proceed with your booking or inquiry! ➡️🚀"
    
    elif "requirements" in subtitle_lower:
        return f"These requirements ensure proper facility usage and maintenance! ✅🔧"
    
    else:
        return f"This section provides important information about {subtitle}! 📌💡"

def generate_all_equipment_structured(info_feed, user_input):
    """Generate structured information about all equipment."""
    base_info = info_feed.get_base_info('english')
    equipment = base_info.get("equipment", {})
    
    if not equipment:
        return "I don't have equipment information available. Please contact ATL for details about available equipment."
    
    response = "## 🔧 ATL Equipment\n\n"
    
    for category, items in equipment.items():
        response += f"### {category}\n"
        if isinstance(items, list):
            for item in items:
                response += f"• {item}\n"
        elif isinstance(items, str):
            response += f"• {items}\n"
        response += "\n"
    
    return response

def generate_all_software_structured(info_feed, user_input):
    """Generate structured information about all software."""
    base_info = info_feed.get_base_info('english')
    software = base_info.get("software", {})
    
    if not software:
        return "I don't have software information available. Please contact ATL for details about available software."
    
    response = "## 💻 ATL Software\n\n"
    
    for category, items in software.items():
        response += f"### {category}\n"
        if isinstance(items, list):
            for item in items:
                response += f"• {item}\n"
        elif isinstance(items, str):
            response += f"• {items}\n"
        response += "\n"
    
    return response

 