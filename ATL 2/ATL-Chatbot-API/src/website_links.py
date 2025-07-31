#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Website Links Module for ATL Chatbot

This module manages website links and provides friendly responses with relevant URLs
when users ask about specific topics.
"""

import re
from typing import Dict, List, Tuple, Optional

class WebsiteLinkManager:
    """Manages website links and provides friendly responses with relevant URLs"""
    
    def __init__(self):
        self.website_links = {
            "ug_research": {
                "url": "https://www.atlab.hku.hk/ug-research/",
                "keywords": ["ug research", "undergraduate research", "research", "student research", "ug", "undergraduate"],
                "title": "Undergraduate Research",
                "emoji": "🔬",
                "description": "Learn about undergraduate research opportunities at ATL"
            },
            "hagg": {
                "url": "https://www.atlab.hku.hk/lab-use-and-policies/atl-student-cohort-group/gamemakers-group/",
                "keywords": ["hagg", "gamemakers", "student cohort", "student group", "cohort group"],
                "title": "HAGG (Gamemakers Group)",
                "emoji": "🎮",
                "description": "Join the HAGG student cohort group for game development"
            },
            "facilities": {
                "url": "https://www.atlab.hku.hk/facilities-information/",
                "keywords": ["facility", "facilities", "software", "tool", "tools", "equipment", "hardware", "space", "room"],
                "title": "Facilities, Software & Tools",
                "emoji": "🏢",
                "description": "Explore our facilities, software, and tools"
            },
            "venue_pricing": {
                "url": "https://www.atlab.hku.hk/venue-info/",
                "keywords": ["venue", "price", "pricing", "cost", "fee", "rental", "booking", "reservation"],
                "title": "Venue & Pricing Information",
                "emoji": "💰",
                "description": "Check venue availability and pricing details"
            },
            "lab_use_policies": {
                "url": "https://www.atlab.hku.hk/lab-use-and-policies/",
                "keywords": ["lab use", "policies", "policy", "rules", "guidelines", "requirements", "permit"],
                "title": "Lab Use & Policies",
                "emoji": "📋",
                "description": "Learn about lab usage policies and guidelines"
            },
            "events": {
                "url": "https://www.atlab.hku.hk/events/",
                "keywords": ["event", "events", "exhibition", "exhibitions", "workshop", "lecture", "activity", "activities"],
                "title": "Events & Exhibitions",
                "emoji": "🎪",
                "description": "Discover upcoming events and exhibitions"
            },
            "lab_team": {
                "url": "https://www.atlab.hku.hk/lab-team/",
                "keywords": ["lab team", "team", "staff", "people", "members", "who are working here", "dr.", "mr.", "engineer", "coordinator"],
                "title": "Lab Team",
                "emoji": "👥",
                "description": "Meet our amazing lab team members"
            },
            "student_interns": {
                "url": "https://www.atlab.hku.hk/lab-team/interns-at-atl/",
                "keywords": ["student intern", "student interns", "student internship", "interns at atl"],
                "title": "Student Interns",
                "emoji": "🎓",
                "description": "Learn about our student intern program"
            },
            "contact": {
                "url": "https://www.atlab.hku.hk/lab-team/contact-us/",
                "keywords": ["contact", "contact us", "get in touch", "reach us", "email", "phone", "address"],
                "title": "Contact Us",
                "emoji": "📞",
                "description": "Get in touch with our team"
            },
            "internship": {
                "url": "https://www.atlab.hku.hk/internship/",
                "keywords": ["internship", "internship opportunity", "internship opportunities", "job opportunity", "career opportunity"],
                "title": "Internship Opportunities",
                "emoji": "💼",
                "description": "Explore internship opportunities at ATL"
            },
            "resources": {
                "url": "https://www.atlab.hku.hk/resources/",
                "keywords": ["resources", "resource", "materials", "guides", "tutorials", "help"],
                "title": "Resources",
                "emoji": "📚",
                "description": "Access helpful resources and guides"
            },
            "hpc": {
                "url": "https://www.atlab.hku.hk/atl-high-performance-computing/",
                "keywords": ["high performance computing", "hpc", "computing", "server", "gpu", "atlhpc"],
                "title": "High Performance Computing",
                "emoji": "⚡",
                "description": "Access our high-performance computing resources"
            }
        }
    
    def find_relevant_links(self, user_input: str) -> List[Dict]:
        """
        Find relevant website links based on user input
        Returns a list of relevant link information
        """
        user_lower = user_input.lower()
        relevant_links = []
        
        for link_id, link_info in self.website_links.items():
            # Check if any keywords match
            for keyword in link_info["keywords"]:
                if keyword in user_lower:
                    relevant_links.append(link_info)
                    break
        
        return relevant_links
    
    def generate_link_response(self, user_input: str) -> Optional[str]:
        """
        Generate a friendly response with relevant website links
        Returns None if no relevant links found
        """
        relevant_links = self.find_relevant_links(user_input)
        
        if not relevant_links:
            return None
        
        # Remove duplicates while preserving order
        seen_urls = set()
        unique_links = []
        for link in relevant_links:
            if link["url"] not in seen_urls:
                seen_urls.add(link["url"])
                unique_links.append(link)
        
        if len(unique_links) == 1:
            link = unique_links[0]
            return f"**{link['title']}** {link['emoji']}\n\n{link['description']}\n\n🔗 **Learn More**: {link['url']}"
        
        else:
            response = "**Relevant Resources** 🌐\n\n"
            for link in unique_links:
                response += f"• **{link['title']}** {link['emoji']}: {link['description']}\n"
                response += f"  🔗 {link['url']}\n\n"
            
            return response
    
    def get_all_links(self) -> Dict[str, Dict]:
        """Get all available website links"""
        return self.website_links
    
    def get_link_by_id(self, link_id: str) -> Optional[Dict]:
        """Get a specific link by ID"""
        return self.website_links.get(link_id)

# Global instance
website_manager = WebsiteLinkManager()

def add_website_links_to_response(response: str, user_input: str) -> str:
    """
    Add relevant website links to an existing response
    """
    link_response = website_manager.generate_link_response(user_input)
    
    if link_response:
        response += f"\n\n**🌐 Learn More Online**\n\n{link_response}"
    
    return response

def get_website_link_response(user_input: str) -> Optional[str]:
    """
    Get a standalone website link response
    """
    return website_manager.generate_link_response(user_input) 