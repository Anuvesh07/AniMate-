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

app = FastAPI(title="Anime CLIP Service")

# Global variables
device = "cuda" if torch.cuda.is_available() else "cpu"
model = None
processor = None
chroma_client = None
collection = None

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

@app.on_event("startup")
async def startup_event():
    global model, processor, chroma_client, collection
    
    print("Loading CLIP model...")
    model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
    processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    model.to(device)
    print(f"CLIP model loaded on {device}")
    
    # Initialize ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_or_create_collection(
        name="anime_characters",
        metadata={"hnsw:space": "cosine"}
    )
    
    # Check if we need to populate the database
    if collection.count() == 0:
        print("Populating character database...")
        await populate_character_database()
    
    print(f"Character database ready with {collection.count()} characters")

async def get_popular_anime_characters():
    """Fetch popular anime characters from AniList API"""
    query = '''
    query {
        Page(page: 1, perPage: 100) {
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
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json={'query': query}) as response:
            if response.status == 200:
                data = await response.json()
                return data['data']['Page']['characters']
            else:
                print(f"Failed to fetch characters: {response.status}")
                return []

def encode_image_from_url(image_url: str) -> Optional[np.ndarray]:
    """Download and encode image from URL using CLIP"""
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
            await asyncio.sleep(0.1)
    
    if embeddings:
        collection.add(
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        print(f"Added {len(embeddings)} characters to database")

def encode_uploaded_image(base64_image: str) -> np.ndarray:
    """Encode uploaded image using CLIP"""
    # Remove data URL prefix if present
    if base64_image.startswith('data:image'):
        base64_image = base64_image.split(',')[1]
    
    # Decode and process image
    image_bytes = base64.b64decode(base64_image)
    image = Image.open(io.BytesIO(image_bytes)).convert('RGB')
    inputs = processor(images=image, return_tensors="pt").to(device)
    
    with torch.no_grad():
        image_features = model.get_image_features(**inputs)
        image_features = image_features / image_features.norm(dim=-1, keepdim=True)
    
    return image_features.cpu().numpy().flatten()

@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(request: ImageAnalysisRequest):
    try:
        # Encode the uploaded image
        query_embedding = encode_uploaded_image(request.image_data)
        
        # Search for similar characters
        results = collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=10
        )
        
        if not results['metadatas'] or not results['metadatas'][0]:
            return AnalysisResponse(
                success=True,
                suggestions=[]
            )
        
        # Convert results to Character objects
        characters = []
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
            characters.append(character)
        
        # Filter characters with reasonable confidence
        good_matches = [c for c in characters if c.confidence > 0.3]
        
        best_match = good_matches[0] if good_matches else None
        suggestions = good_matches[:5] if good_matches else []
        
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
        "model_device": device,
        "characters_count": collection.count() if collection else 0
    }

@app.post("/refresh-database")
async def refresh_database():
    """Manually refresh the character database"""
    try:
        # Clear existing data
        collection.delete(where={})
        
        # Repopulate
        await populate_character_database()
        
        return {
            "success": True,
            "message": f"Database refreshed with {collection.count()} characters"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)