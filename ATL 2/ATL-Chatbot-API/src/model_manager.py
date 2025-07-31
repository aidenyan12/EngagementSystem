#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Model Manager Module for ATL Chatbot

This module handles model loading, caching, and management operations.
"""

import os
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import warnings

# Set up environment variables for transformers
os.environ["TRANSFORMERS_NO_ADVISORY_WARNINGS"] = "1"
os.environ["TRANSFORMERS_NO_CONSOLE_WARNING"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("torch").setLevel(logging.ERROR)

logger = logging.getLogger("model_manager")

# Global model cache
_model_cache = None
_tokenizer_cache = None

def load_model(lightweight_mode=False):
    """Load the model and tokenizer with caching"""
    global _model_cache, _tokenizer_cache
    
    if _model_cache is not None and _tokenizer_cache is not None:
        logger.info("Using cached model and tokenizer")
        return _model_cache, _tokenizer_cache
    
    try:
        # Suppress warnings
        warnings.filterwarnings("ignore", category=UserWarning)
        
        if lightweight_mode:
            logger.info("Loading lightweight model...")
            model_name = "microsoft/DialoGPT-medium"
            generator = pipeline('text-generation', model=model_name, tokenizer=model_name)
            _model_cache = generator
            _tokenizer_cache = generator.tokenizer
            return generator, generator.tokenizer
        else:
            logger.info("Loading full model...")
            model_name = "microsoft/DialoGPT-medium"
            tokenizer = AutoTokenizer.from_pretrained(model_name)
            model = AutoModelForCausalLM.from_pretrained(model_name)
            
            # Cache the loaded model and tokenizer
            _model_cache = model
            _tokenizer_cache = tokenizer
            
            return model, tokenizer
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        raise

def clear_model_cache():
    """Clear the model cache to free up memory"""
    global _model_cache, _tokenizer_cache
    _model_cache = None
    _tokenizer_cache = None
    logger.info("Model cache cleared")

def get_model_info():
    """Get information about the currently loaded model"""
    global _model_cache, _tokenizer_cache
    
    if _model_cache is None or _tokenizer_cache is None:
        return {"status": "No model loaded"}
    
    info = {
        "status": "Model loaded",
        "model_type": type(_model_cache).__name__,
        "tokenizer_type": type(_tokenizer_cache).__name__
    }
    
    # Add device information if available
    if hasattr(_model_cache, 'device'):
        info["device"] = str(_model_cache.device)
    
    return info 