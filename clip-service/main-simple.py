import os
import io
import base64
import json
from typing import List, Optional
import numpy as np
from PIL import Image
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests
import asyncio
import aiohttp
import random

app = FastAPI(title="Anime CLIP Service - Simple Version")

class ImageAnalysisRequest(BaseModel):
    image_data: str

class Character(BaseModel):
    id: int
    name: str
    anime: str
    description: str
    image_url: str
    confidence: float = 0.0

class AnalysisResponse(BaseModel):
    success: bool
    character: Optional[Character] = None
    suggestions: List[Character] = []
    error: Optional[str] = None

# Sample anime characters for testing
SAMPLE_CHARACTERS = [
    {
        "id": 1,
        "name": "Naruto Uzumaki",
        "anime": "Naruto",
        "description": "A young ninja with dreams of becoming Hokage",
        "image_url": "https://example.com/naruto.jpg"
    },
    {
        "id": 2,
        "name": "Goku",
        "anime": "Dragon Ball",
        "description": "A Saiyan warrior with incredible strength",
        "image_url": "https://example.com/goku.jpg"
    },
    {
        "id": 3,
        "name": "Luffy",
        "anime": "One Piece",
        "description": "A rubber-powered pirate captain",
        "image_url": "https://example.com/luffy.jpg"
    },
    {
        "id": 4,
        "name": "Edward Elric",
        "anime": "Fullmetal Alchemist",
        "description": "A young alchemist searching for the Philosopher's Stone",
        "image_url": "https://example.com/edward.jpg"
    },
    {
        "id": 5,
        "name": "Ichigo Kurosaki",
        "anime": "Bleach",
        "description": "A substitute Soul Reaper with orange hair",
        "image_url": "https://example.com/ichigo.jpg"
    }
]

@app.on_event("startup")
async def startup_event():
    print("Simple CLIP service started - using mock data for testing")
    print(f"Loaded {len(SAMPLE_CHARACTERS)} sample characters")

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    try:
        # Simulate processing time
        await asyncio.sleep(2)
        
        # For demo purposes, return random characters with confidence scores
        # In a real implementation, this would use CLIP to analyze the image
        
        # Shuffle characters and assign random confidence scores
        characters = SAMPLE_CHARACTERS.copy()
        random.shuffle(characters)
        
        suggestions = []
        for i, char_data in enumerate(characters[:3]):
            confidence = random.uniform(0.4, 0.9) if i == 0 else random.uniform(0.2, 0.6)
            character = Character(
                id=char_data["id"],
                name=char_data["name"],
                anime=char_data["anime"],
                description=char_data["description"],
                image_url=char_data["image_url"],
                confidence=confidence
            )
            suggestions.append(character)
        
        # Sort by confidence
        suggestions.sort(key=lambda x: x.confidence, reverse=True)
        
        best_match = suggestions[0] if suggestions and suggestions[0].confidence > 0.5 else None
        
        return AnalysisResponse(
            success=True,
            character=best_match,
            suggestions=suggestions
        )
        
    except Exception as e:
        return AnalysisResponse(
            success=False,
            error=str(e)
        )

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_device": "cpu",
        "characters_count": len(SAMPLE_CHARACTERS),
        "version": "simple-demo"
    }

@app.post("/refresh-database")
async def refresh_database():
    """Mock refresh endpoint"""
    return {
        "success": True,
        "message": f"Database refreshed with {len(SAMPLE_CHARACTERS)} characters"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)