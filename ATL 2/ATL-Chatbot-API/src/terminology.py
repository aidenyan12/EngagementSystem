#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Terminology Standardization Module

This module provides functionality for standardizing terminology
in the model's responses according to configurable rules.
"""

import os
import json
import re
from typing import Dict, List, Any, Optional

# Default path to the terminology configuration file
DEFAULT_CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data", "config", "terminology.json"
)

class TerminologyStandardizer:
    """
    Standardizes terminology in text based on configurable rules
    loaded from a JSON file.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the standardizer with rules from the configuration file.
        
        Args:
            config_path (str, optional): Path to the terminology configuration file.
                                        If not provided, uses the default path.
        """
        self.config_path = config_path or DEFAULT_CONFIG_PATH
        self.rules = self._load_rules()
    
    def _load_rules(self) -> Dict[str, Any]:
        """
        Load terminology rules from the configuration file.
        
        Returns:
            Dict[str, Any]: Dictionary containing the terminology rules
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                rules = json.load(f)
            return rules
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading terminology rules: {e}")
            # Return a minimal default configuration if the file can't be loaded
            return {
                "english": {"replacements": []},
                "chinese": {"replacements": []}
            }
    
    def reload_rules(self) -> None:
        """Reload terminology rules from the configuration file."""
        self.rules = self._load_rules()
    
    def standardize(self, text: str, language: str = "auto", single_pass: bool = False) -> str:
        """
        Apply terminology standardization to the given text.
        
        Args:
            text (str): Text to standardize
            language (str): Language of the text ("en", "zh", or "auto" for auto-detection)
            single_pass (bool): If True, only apply replacements once without iterations
            
        Returns:
            str: Standardized text
        """
        # Keep original for comparison
        original_text = text
        
        # Auto-detect language if not specified
        if language == "auto":
            language = self._detect_language(text)
        
        # Map the language code to the rule set
        rule_set = None
        if language == "en":
            rule_set = self.rules.get("english", {})
        elif language == "zh":
            rule_set = self.rules.get("chinese", {})
        else:
            # Default to English if language is uncertain
            rule_set = self.rules.get("english", {})
        
        # If no rule set found for the language, return the original text
        if not rule_set:
            print(f"[Terminology] No rules found for language: {language}")
            return text
        
        # Apply all replacements for the language
        result = text
        replacements_applied = 0
        
        # Instead of tracking positions, we'll create a "replaced" flag for each character
        # This prevents characters from being part of multiple replacements
        char_replaced = [False] * len(text)
        
        # Get all replacements for the language
        replacements = rule_set.get("replacements", [])
        
        # Process replacements in a specific order to avoid conflicts:
        # 1. First, handle all multi-part entity conversions (e.g., "Hong Kong University Arts Tech Lab" → "Arts Tech Lab at HKU")
        # 2. Then handle single entity standardizations
        
        # Sort replacements by complexity (pattern length as a rough heuristic)
        sorted_replacements = sorted(
            replacements,
            key=lambda r: len(r.get("pattern", "")),
            reverse=True  # Longer patterns (more complex) first
        )
        
        # Either do a single pass or limited iterations
        max_iterations = 1 if single_pass else 1  # Restrict to single pass by default to avoid over-replacement
        iteration = 0
        
        while iteration < max_iterations:
            previous_result = result
            replacements_in_iteration = 0
            
            # Process each replacement rule once per iteration
            for replacement in sorted_replacements:
                pattern = replacement.get("pattern", "")
                replace_with = replacement.get("replacement", "")
                
                if pattern and replace_with:
                    # Find all matches in the current text
                    matches = list(re.finditer(pattern, result))
                    
                    if not matches:
                        continue
                        
                    # Create a new result with replacements
                    new_result = ""
                    last_end = 0
                    
                    for match in matches:
                        start, end = match.span()
                        matched_text = result[start:end]
                        
                        # Check if any character in this region has already been replaced
                        already_replaced = any(char_replaced[i] for i in range(start, end) if i < len(char_replaced))
                        
                        if not already_replaced:
                            # Add text before the match
                            new_result += result[last_end:start]
                            
                            # Add the replacement
                            new_result += replace_with
                            
                            # Mark these characters as replaced
                            for i in range(start, end):
                                if i < len(char_replaced):
                                    char_replaced[i] = True
                                    
                            replacements_applied += 1
                            replacements_in_iteration += 1
                        else:
                            # Don't replace, keep original
                            new_result += result[last_end:end]
                            
                        last_end = end
                    
                    # Add the remaining text
                    new_result += result[last_end:]
                    
                    # Update result
                    if new_result != result:
                        result = new_result
                        # Need to recreate the char_replaced array
                        char_replaced = [False] * len(result)
                        break
            
            # Stop if no replacements were made in this iteration
            if replacements_in_iteration == 0 or result == previous_result:
                break
                
            iteration += 1
        
        # Log changes if any were made
        if result != original_text and replacements_applied > 0:
            # Use a more concise log message
            print(f"[Terminology] Applied {replacements_applied} replacements ({language}, {iteration+1} passes)")
        
        return result
    
    def _detect_language(self, text: str) -> str:
        """
        Detect the language of the text.
        
        Args:
            text (str): Text to detect language from
            
        Returns:
            str: "zh" for Chinese, "en" for English or other languages
        """
        # Simple detection: if there are many Chinese characters, consider it Chinese
        chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]')
        chinese_chars = re.findall(chinese_pattern, text)
        
        # If more than 15% of characters are Chinese, consider it Chinese
        if len(chinese_chars) > len(text) * 0.15:
            return "zh"
        return "en"
    
    def add_rule(self, language: str, pattern: str, replacement: str) -> bool:
        """
        Add a new standardization rule.
        
        Args:
            language (str): Language code ("en" or "zh")
            pattern (str): Regular expression pattern to match
            replacement (str): Text to replace matches with
            
        Returns:
            bool: True if the rule was added successfully, False otherwise
        """
        # Map language codes to rule set names
        lang_map = {
            "en": "english",
            "zh": "chinese"
        }
        
        # Get the appropriate rule set
        lang_key = lang_map.get(language)
        if not lang_key or lang_key not in self.rules:
            return False
        
        # Ensure the replacements list exists
        if "replacements" not in self.rules[lang_key]:
            self.rules[lang_key]["replacements"] = []
        
        # Add the new rule
        self.rules[lang_key]["replacements"].append({
            "pattern": pattern,
            "replacement": replacement
        })
        
        # Save the updated rules
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.rules, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False
    
    def remove_rule(self, language: str, pattern: str) -> bool:
        """
        Remove a standardization rule.
        
        Args:
            language (str): Language code ("en" or "zh")
            pattern (str): Pattern of the rule to remove
            
        Returns:
            bool: True if the rule was removed successfully, False otherwise
        """
        # Map language codes to rule set names
        lang_map = {
            "en": "english",
            "zh": "chinese"
        }
        
        # Get the appropriate rule set
        lang_key = lang_map.get(language)
        if not lang_key or lang_key not in self.rules:
            return False
        
        # Find and remove the rule
        if "replacements" in self.rules[lang_key]:
            original_length = len(self.rules[lang_key]["replacements"])
            self.rules[lang_key]["replacements"] = [
                rule for rule in self.rules[lang_key]["replacements"]
                if rule.get("pattern") != pattern
            ]
            
            # If a rule was removed, save the updated rules
            if len(self.rules[lang_key]["replacements"]) < original_length:
                try:
                    with open(self.config_path, 'w', encoding='utf-8') as f:
                        json.dump(self.rules, f, indent=2, ensure_ascii=False)
                    return True
                except Exception:
                    return False
        
        return False
    
    def standardize_text(self, text: str, language: str = "english") -> str:
        """
        Standardize terminology in the given text based on rules for the specified language.
        
        Args:
            text (str): The text to standardize
            language (str): The language of the text ("english" or "chinese")
            
        Returns:
            str: Text with standardized terminology
        """
        if not text:
            return text
            
        # Map the language name to the language code expected by standardize method
        lang_map = {
            "english": "en",
            "chinese": "zh"
        }
        lang_code = lang_map.get(language, "en")
        
        # Use the more comprehensive standardize method
        return self.standardize(text, lang_code)

# Create a singleton instance for easy import
standardizer = TerminologyStandardizer()

# Utility function for easier access
def standardize_terminology(text: str, language: str = "auto", single_pass: bool = False) -> str:
    """
    Standardize terminology in the provided text.
    
    Args:
        text (str): Text to standardize
        language (str): Language of the text ("en", "zh", or "auto" for auto-detection)
        single_pass (bool): If True, only apply replacements once without iterations
        
    Returns:
        str: Standardized text
    """
    return standardizer.standardize(text, language, single_pass)
