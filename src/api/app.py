# Import the required frameworks
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from src.models.models import RestaurantSchema, Restaurant, Video
from src.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import distinct

# Create a FastAPI application instance
app = FastAPI(
    title="TikTok Restaurant Maps",
    description="API for managing and displaying TikTok-featured restaurants",
    version="0.1.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to TikTok Restaurant Maps API"}

@app.get("/restaurants")
async def get_restaurants(db: Session = Depends(get_db)):
    query_results = db.query(Restaurant)\
        .join(Video, Restaurant.id == Video.restaurant_id)\
        .with_entities(
            Restaurant.id,
            Restaurant.name,
            Restaurant.location,
            Restaurant.coordinates,
            Restaurant.phone,
            Restaurant.rating,
            Restaurant.price_level,
            Video.video_url
        ).all()
    
    restaurant_dict = {}
    
    for result in query_results:
        restaurant_id = result.id
        if restaurant_id not in restaurant_dict:
            restaurant_dict[restaurant_id] = {
                "id": result.id,
                "name": result.name,
                "location": result.location,
                "coordinates": result.coordinates,
                "phone": result.phone,
                "rating": result.rating,
                "price_level": result.price_level,
                "video_urls": []
            }
        
        if result.video_url:
            restaurant_dict[restaurant_id]["video_urls"].append(result.video_url)
    
    return list(restaurant_dict.values())

@app.get("/cities")
async def get_cities(db: Session = Depends(get_db)):
    # Query distinct cities from the city column
    cities = db.query(distinct(Restaurant.city))\
        .filter(Restaurant.city.isnot(None))\
        .order_by(Restaurant.city)\
        .all()
    # Convert tuple of tuples to list of strings
    return [city[0] for city in cities]

