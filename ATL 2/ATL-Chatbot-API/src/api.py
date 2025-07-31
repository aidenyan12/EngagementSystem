#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
ATL Chatbot API Server

This module provides a FastAPI server to expose the chatbot functionality via REST API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import logging
import os
import sys
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

# Add src directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import chatbot components
from response_generators import generate_lightweight_response
from data_loader import InformationFeed
from model_manager import load_model

# Set up logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("atl_chatbot_api")

# Initialize FastAPI app
app = FastAPI(
    title="ATL Chatbot API",
    description="API for the Arts Technology Lab Chatbot",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize InformationFeed with error handling
try:
    logger.info("Initializing InformationFeed...")
    info_feed = InformationFeed()
    logger.info("InformationFeed initialized successfully")
except Exception as e:
    logger.error(f"Error initializing InformationFeed: {str(e)}")
    logger.error(traceback.format_exc())
    raise

# Initialize model with error handling
try:
    logger.info("Loading model...")
    model, tokenizer = load_model(lightweight_mode=True)
    logger.info("Model loaded successfully")
except Exception as e:
    logger.error(f"Error loading model: {str(e)}")
    logger.error(traceback.format_exc())
    model = None
    tokenizer = None

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str
    session_id: Optional[str] = None

class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    response: str
    session_id: Optional[str]
    metadata: Optional[Dict[str, Any]] = None

@app.get("/")
async def root():
    """Root endpoint to check if API is running"""
    return {
        "status": "ok",
        "message": "ATL Chatbot API is running"
    }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint that processes user messages and returns chatbot responses
    
    Args:
        request (ChatRequest): The chat request containing the user's message
        
    Returns:
        ChatResponse: The chatbot's response
    """
    try:
        # Log incoming request
        logger.info(f"Received chat request with message: {request.message}")
        
        # Generate response using the chatbot
        logger.debug("Calling generate_lightweight_response...")
        response = generate_lightweight_response(
            generator=model,  # Pass the loaded model as generator
            user_input=request.message,
            info_feed=info_feed
        )
        logger.debug("Response generated successfully")
        
        # Prepare the response
        chat_response = ChatResponse(
            response=response,
            session_id=request.session_id,
            metadata={
                "timestamp": str(datetime.now()),
                "message_length": len(request.message),
                "response_length": len(response)
            }
        )
        
        # Log the response
        logger.info(f"Generated response: {response[:100]}...")
        
        return chat_response
        
    except Exception as e:
        tb = traceback.format_exc()
        logger.error(f"Error processing chat request: {str(e)}\n{tb}")
        # Return the traceback in the response for debugging
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while processing your request: {str(e)}\n{tb}"
        )

if __name__ == "__main__":
    import uvicorn
    # Run the API server with debug logging
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="debug"
    ) 