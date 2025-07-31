#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Text Processors Module for ATL Chatbot

This module handles text processing utilities including:
- Language detection
- Text extraction
- Facility name matching
- Text analysis utilities
"""

import re
import difflib
import logging
from typing import List, Dict, Any, Optional, Tuple

# Import terminology standardizer
try:
    from terminology import TerminologyStandardizer
    standardizer = TerminologyStandardizer()
except ImportError:
    # Fallback if terminology module is not available
    class TerminologyStandardizer:
        def standardize_text(self, text, language):
            return text
    standardizer = TerminologyStandardizer()

logger = logging.getLogger("text_processors")

def detect_language(text):
    """Always return English (simplified for English-only chatbot)"""
    return "english"

def is_non_text_input(user_input):
    """
    Check if the user input is only numbers or symbols.
    Returns True only for pure numbers or pure symbols.
    All other text (including random letters) goes to general intent.
    """
    if not user_input or len(user_input.strip()) == 0:
        return True
    
    user_clean = user_input.strip()
    
    # Check for pure numbers only
    if re.match(r'^\d+$', user_clean):
        return True
    
    # Check for pure symbols only (no letters or numbers)
    if re.match(r'^[^\w\s]+$', user_clean):
        return True
    
    # Check for numbers mixed with symbols only (no letters)
    if re.match(r'^[\d\W]+$', user_clean) and not re.search(r'[a-zA-Z]', user_clean):
        return True
    
    # Everything else (including random letters, mixed text, etc.) goes to general intent
    return False

def extract_facility_from_question(user_input):
    """Extract the facility/entity name from natural language questions like 'what is ...', 'tell me about ...', etc."""
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

def normalize_facility_name(name):
    """Normalize facility name for matching (lowercase, remove spaces and special chars)"""
    import re
    return re.sub(r'[^a-z0-9]', '', name.lower())

def find_best_facility_match(facilities, user_input):
    """Find the best matching facility name from the facilities dict given the user input."""
    import difflib
    norm_input = normalize_facility_name(user_input)
    facility_names = list(facilities.keys())
    norm_names = [normalize_facility_name(name) for name in facility_names]
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

def extract_staff_names_from_text(text):
    """Extract staff names from text using regex patterns."""
    staff_names = []
    
    # Pattern 1: Fix the exact format 'Dr Kal Ng Professional (Practitioner)' -> 'Dr Kal Ng (Professional Practitioner)'
    pattern1 = r'(Dr\.?|Mr\.?|Ms\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+\(([^)]+)\)'
    matches1 = re.finditer(pattern1, text)
    for match in matches1:
        title = match.group(1).replace('.', '').strip()
        name = match.group(2).strip()
        role_part1 = match.group(3).strip()
        role_part2 = match.group(4).strip()
        full_name = f"{title} {name}"
        full_role = f"{role_part1} {role_part2}"
        staff_names.append(f"{full_name} ({full_role})")
    
    # Pattern 2: Handle 'Dr Kal Ng Professional Practitioner' style (no parentheses)
    pattern2 = r'(Dr\.?|Mr\.?|Ms\.?)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?=\s*(?:Dr\.?|Mr\.?|Ms\.?|$|\n))'
    matches2 = re.finditer(pattern2, text)
    for match in matches2:
        title = match.group(1).replace('.', '').strip()
        name = match.group(2).strip()
        role = match.group(3).strip()
        full_name = f"{title} {name}"
        # Skip if already processed by pattern1
        formatted_entry = f"{full_name} ({role})"
        if not any(formatted_entry.startswith(existing.split(' (')[0]) for existing in staff_names):
            staff_names.append(formatted_entry)
    
    # Pattern 3: Handle already correct format 'Dr. Kal Ng (Director)'
    pattern3 = r'(Dr|Mr|Ms)\.\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*\(([^)]+)\)'
    matches3 = re.finditer(pattern3, text)
    for match in matches3:
        title = match.group(1)
        name = match.group(2).strip()
        role = match.group(3).strip()
        staff_names.append(f"{title}. {name} ({role})")
    
    return staff_names

def get_category_emoji(category):
    """Get emoji for different categories"""
    emoji_map = {
        "facilities": "🏢",
        "equipment": "🔧", 
        "software": "💻",
        "pricing": "💰",
        "contact": "📞",
        "general": "ℹ️",
        "events": "🎪",
        "staff": "👥",
        "programs": "📚",
        "booking": "📅",
        "rental": "🏠"
    }
    
    category_lower = category.lower()
    for key, emoji in emoji_map.items():
        if key in category_lower:
            return emoji
    
    return "📋"  # Default emoji

def get_section_emoji(subtitle):
    """Get appropriate emoji for section subtitles"""
    subtitle_lower = subtitle.lower()
    
    if any(word in subtitle_lower for word in ["facility", "room", "space"]):
        return "🏢"
    elif any(word in subtitle_lower for word in ["equipment", "hardware"]):
        return "🔧"
    elif any(word in subtitle_lower for word in ["software", "program", "application"]):
        return "💻"
    elif any(word in subtitle_lower for word in ["price", "cost", "fee", "rental"]):
        return "💰"
    elif any(word in subtitle_lower for word in ["contact", "phone", "email"]):
        return "📞"
    elif any(word in subtitle_lower for word in ["capacity", "size", "area"]):
        return "📏"
    elif any(word in subtitle_lower for word in ["feature", "capability"]):
        return "⭐"
    elif any(word in subtitle_lower for word in ["booking", "reservation"]):
        return "📅"
    elif any(word in subtitle_lower for word in ["description", "overview"]):
        return "📝"
    else:
        return "•"

def group_similar_points(points):
    """Group similar points together to reduce redundancy"""
    if not points:
        return []
    
    grouped = []
    used_indices = set()
    
    for i, point in enumerate(points):
        if i in used_indices:
            continue
            
        similar_points = [point]
        used_indices.add(i)
        
        # Find similar points
        for j, other_point in enumerate(points[i+1:], i+1):
            if j in used_indices:
                continue
                
            # Check similarity (simple word overlap)
            point_words = set(point.lower().split())
            other_words = set(other_point.lower().split())
            
            # If significant overlap, group them
            overlap = len(point_words & other_words)
            total_unique = len(point_words | other_words)
            
            if total_unique > 0 and overlap / total_unique > 0.6:
                similar_points.append(other_point)
                used_indices.add(j)
        
        # Use the longest/most informative point from the group
        best_point = max(similar_points, key=len)
        grouped.append(best_point)
    
    return grouped

def translate_response(response, target_lang):
    """Simplified translation function - just return the response as-is since we're English-only now."""
    return response

def get_friendly_non_text_response():
    """Get a friendly response for non-text input"""
    responses = [
        "I see you've entered some numbers or symbols! 🤔 Could you please type a question or message in words? I'd love to help you with information about ATL facilities, booking, equipment, or anything else! 💬✨",
        
        "Oops! It looks like you might have typed numbers or symbols by accident! 😊 Could you please write your question in words? I'm here to help with all things ATL! 🎯💫",
        
        "I'm not sure I understand that input! 🤷‍♂️ Could you please type your question using words? For example, you could ask about 'facilities', 'booking', 'pricing', or 'equipment'! 📝💡",
        
        "That looks like numbers or symbols to me! 😅 Could you please rephrase your question using words? I'm excited to help you learn about ATL! 🚀🌟",
        
        "I'd love to help you, but I need a text message! 📱 Could you please type your question in words? You can ask about anything related to the Arts Technology Lab! 🎨💬"
    ]
    import random
    return random.choice(responses) 