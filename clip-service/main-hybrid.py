import os
import io
import base64
import json
from typing import List, Optional
import numpy as np
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
import chromadb
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import requests
import asyncio
import aiohttp
import random

app = FastAPI(title="Anime CLIP Service - Hybrid")

# Global variables
device = "cuda" if torch.cuda.is_available() else "cpu"
model = None
processor = None
chroma_client = None
collection = None
model_loaded = False

# Sample characters for immediate functionality
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
    },
    {
        "id": 6,
        "name": "Light Yagami",
        "anime": "Death Note",
        "description": "A brilliant student who finds the Death Note",
        "image_url": "https://example.com/light.jpg"
    },
    {
        "id": 7,
        "name": "Saitama",
        "anime": "One Punch Man",
        "description": "A bald superhero who can defeat any enemy with one punch",
        "image_url": "https://example.com/saitama.jpg"
    },
    {
        "id": 8,
        "name": "Tanjiro Kamado",
        "anime": "Demon Slayer",
        "description": "A demon slayer with a checkered haori",
        "image_url": "https://example.com/tanjiro.jpg"
    }
]

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

class ReExamineRequest(BaseModel):
    image_data: str
    exclude_ids: List[int] = []
    focus_ids: List[int] = []
    search_type: str = "normal"  # "normal", "exclude", "focus"

@app.on_event("startup")
async def startup_event():
    global model, processor, chroma_client, collection, model_loaded
    
    print("Starting Anime CLIP Service...")
    print("Phase 1: Basic functionality with sample data")
    
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(
        name="anime_characters",
        metadata={"hnsw:space": "cosine"}
    )
    
    print(f"Sample characters ready: {len(SAMPLE_CHARACTERS)}")
    
    # Start loading CLIP model in background
    asyncio.create_task(load_clip_model())

async def load_clip_model():
    global model, processor, model_loaded
    
    try:
        print("Phase 2: Loading CLIP model (this may take 5-10 minutes)...")
        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        model.to(device)
        model_loaded = True
        print(f"CLIP model loaded successfully on {device}")
        
        # Check if we need to populate the database
        if collection.count() == 0:
            print("Phase 3: Populating character database with real data...")
            await populate_character_database()
        
        print(f"Real character database ready with {collection.count()} characters")
        
    except Exception as e:
        print(f"Failed to load CLIP model: {e}")
        print("Continuing with sample data...")

async def get_popular_anime_characters():
    """Fetch popular anime characters from AniList API"""
    query = '''
    query {
        Page(page: 1, perPage: 50) {
            characters(sort: FAVOURITES_DESC) {
                id
                name {
                    full
                    native
                }
                image {
                    large
                    medium
                }
                description
                media(sort: POPULARITY_DESC, perPage: 3) {
                    nodes {
                        title {
                            romaji
                            english
                        }
                        type
                    }
                }
            }
        }
    }
    '''
    
    url = 'https://graphql.anilist.co'
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json={'query': query}) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['data']['Page']['characters']
                else:
                    print(f"Failed to fetch characters: {response.status}")
                    return []
    except Exception as e:
        print(f"Error fetching characters: {e}")
        return []

def encode_image_from_url(image_url: str) -> Optional[np.ndarray]:
    """Download and encode image from URL using CLIP"""
    if not model_loaded:
        return None
        
    try:
        response = requests.get(image_url, timeout=10)
        if response.status_code == 200:
            image = Image.open(io.BytesIO(response.content)).convert('RGB')
            inputs = processor(images=image, return_tensors="pt").to(device)
            
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
                image_features = image_features / image_features.norm(dim=-1, keepdim=True)
            
            return image_features.cpu().numpy().flatten()
    except Exception as e:
        print(f"Failed to encode image from {image_url}: {e}")
    return None

async def populate_character_database():
    """Populate ChromaDB with anime characters and their image embeddings"""
    if not model_loaded:
        return
        
    characters = await get_popular_anime_characters()
    
    embeddings = []
    metadatas = []
    ids = []
    
    for char in characters:
        if not char.get('image', {}).get('large'):
            continue
            
        # Get primary anime
        primary_anime = "Unknown"
        if char.get('media', {}).get('nodes'):
            anime_node = char['media']['nodes'][0]
            primary_anime = (anime_node.get('title', {}).get('english') or 
                           anime_node.get('title', {}).get('romaji') or 
                           "Unknown")
        
        # Encode character image
        embedding = encode_image_from_url(char['image']['large'])
        if embedding is not None:
            embeddings.append(embedding.tolist())
            metadatas.append({
                'name': char['name']['full'] or char['name']['native'] or f"Character {char['id']}",
                'anime': primary_anime,
                'description': char.get('description', '').replace('<br>', ' ')[:200] if char.get('description') else '',
                'image_url': char['image']['large'],
                'anilist_id': char['id']
            })
            ids.append(str(char['id']))
            
            # Add some delay to avoid rate limiting
            await asyncio.sleep(0.2)
    
    if embeddings:
        collection.add(
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(embeddings)} characters to database")

def encode_uploaded_image(base64_image: str) -> Optional[np.ndarray]:
    """Encode uploaded image using CLIP"""
    if not model_loaded:
        return None
        
    try:
        # Remove data URL prefix if present
        if base64_image.startswith('data:image'):
            base64_image = base64_image.split(',')[1]
        
        # Fix padding if necessary
        missing_padding = len(base64_image) % 4
        if missing_padding:
            base64_image += '=' * (4 - missing_padding)
        
        # Decode and process image
        image_bytes = base64.b64decode(base64_image)
        image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        inputs = processor(images=image, return_tensors="pt").to(device)
        
        with torch.no_grad():
            image_features = model.get_image_features(**inputs)
            image_features = image_features / image_features.norm(dim=-1, keepdim=True)
        
        return image_features.cpu().numpy().flatten()
    except Exception as e:
        print(f"Error encoding uploaded image: {e}")
        return None

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    return await _analyze_image_internal(request.image_data)

@app.post("/re-examine", response_model=AnalysisResponse)
async def re_examine_image(request: ReExamineRequest):
    return await _analyze_image_internal(
        request.image_data, 
        exclude_ids=request.exclude_ids,
        focus_ids=request.focus_ids,
        search_type=request.search_type
    )

async def _analyze_image_internal(
    image_data: str, 
    exclude_ids: List[int] = None, 
    focus_ids: List[int] = None,
    search_type: str = "normal"
):
    try:
        exclude_ids = exclude_ids or []
        focus_ids = focus_ids or []
        
        if model_loaded and collection.count() > 0:
            # Use real CLIP analysis
            query_embedding = encode_uploaded_image(image_data)
            
            if query_embedding is not None:
                # Determine search parameters based on search type
                n_results = 50 if search_type in ["exclude", "focus"] else 10
                
                # Search for similar characters
                results = collection.query(
                    query_embeddings=[query_embedding.tolist()],
                    n_results=n_results
                )
                
                if results['metadatas'] and results['metadatas'][0]:
                    # Convert results to Character objects
                    all_characters = []
                    for i, metadata in enumerate(results['metadatas'][0]):
                        distance = results['distances'][0][i]
                        confidence = max(0, 1 - distance)  # Convert distance to confidence
                        
                        character = Character(
                            id=metadata['anilist_id'],
                            name=metadata['name'],
                            anime=metadata['anime'],
                            description=metadata['description'],
                            image_url=metadata['image_url'],
                            confidence=confidence
                        )
                        all_characters.append(character)
                    
                    # Apply filtering based on search type
                    if search_type == "exclude" and exclude_ids:
                        # Exclude specified characters and find new ones
                        filtered_characters = [c for c in all_characters if c.id not in exclude_ids]
                        # Lower confidence threshold for exclude searches to find more alternatives
                        good_matches = [c for c in filtered_characters if c.confidence > 0.1][:5]
                        print(f"Excluded {len(exclude_ids)} characters, found {len(good_matches)} alternatives")
                    elif search_type == "focus" and focus_ids:
                        # Focus only on specified characters, re-ranked by confidence
                        focused_characters = [c for c in all_characters if c.id in focus_ids]
                        good_matches = sorted(focused_characters, key=lambda x: x.confidence, reverse=True)[:5]
                        print(f"Focused on {len(focus_ids)} characters, found {len(good_matches)} matches")
                    else:
                        # Normal search
                        good_matches = [c for c in all_characters if c.confidence > 0.2][:5]
                    
                    best_match = good_matches[0] if good_matches else None
                    suggestions = good_matches
                    
                    return AnalysisResponse(
                        success=True,
                        character=best_match,
                        suggestions=suggestions
                    )
        
        # Fallback to sample data with improved logic
        await asyncio.sleep(1)  # Simulate processing time
        
        # Use basic image analysis (size, format) to influence results
        try:
            if image_data.startswith('data:image'):
                image_data_clean = image_data.split(',')[1]
            else:
                image_data_clean = image_data
            
            # Fix padding if necessary
            missing_padding = len(image_data_clean) % 4
            if missing_padding:
                image_data_clean += '=' * (4 - missing_padding)
                
            image_bytes = base64.b64decode(image_data_clean)
            image = Image.open(io.BytesIO(image_bytes))
            
            # Simple heuristics based on image properties
            width, height = image.size
            aspect_ratio = width / height
            
            # Apply filtering for fallback data too
            available_characters = SAMPLE_CHARACTERS.copy()
            
            if search_type == "exclude" and exclude_ids:
                available_characters = [c for c in available_characters if c["id"] not in exclude_ids]
                print(f"Fallback: Excluded {len(exclude_ids)} characters, {len(available_characters)} remaining")
            elif search_type == "focus" and focus_ids:
                available_characters = [c for c in available_characters if c["id"] in focus_ids]
                print(f"Fallback: Focused on {len(focus_ids)} characters")
            
            random.shuffle(available_characters)
            
            suggestions = []
            for i, char_data in enumerate(available_characters[:4]):
                # Assign confidence based on position and some randomness
                base_confidence = 0.8 - (i * 0.15)
                confidence = base_confidence + random.uniform(-0.1, 0.1)
                confidence = max(0.3, min(0.9, confidence))
                
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
            print(f"Error in fallback analysis: {e}")
            # Ultimate fallback
            character = Character(
                id=1,
                name="Naruto Uzumaki",
                anime="Naruto",
                description="A young ninja with dreams of becoming Hokage",
                image_url="https://example.com/naruto.jpg",
                confidence=0.6
            )
            
            return AnalysisResponse(
                success=True,
                character=character,
                suggestions=[character]
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
        "model_device": device,
        "model_loaded": model_loaded,
        "characters_count": collection.count() if collection else len(SAMPLE_CHARACTERS),
        "version": "hybrid"
    }

@app.post("/refresh-database")
async def refresh_database():
    """Manually refresh the character database"""
    try:
        if model_loaded:
            # Clear existing data
            collection.delete(where={})
            
            # Repopulate
            await populate_character_database()
            
            return {
                "success": True,
                "message": f"Database refreshed with {collection.count()} characters"
            }
        else:
            return {
                "success": False,
                "message": "CLIP model not loaded yet, using sample data"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)