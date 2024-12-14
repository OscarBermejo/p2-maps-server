# Import the required frameworks
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from datetime import datetime  
from src.models.models import RestaurantSchema, Restaurant, Video, Tag
from src.database import get_db
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from ..utils.logger_config import setup_cloudwatch_logging
import logging
from fastapi.responses import JSONResponse

# Setup logging first
setup_cloudwatch_logging('maps-server')

# Then get the logger for this file
logger = logging.getLogger(__name__)

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
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to TikTok Restaurant Maps API"}

@app.get("/restaurants")
async def get_restaurants(db: Session = Depends(get_db)):
    logger.info("Fetching all restaurants")
    try:
        restaurants = db.query(Restaurant).all()
        
        result = []
        for restaurant in restaurants:
            videos = [video.video_url for video in restaurant.videos if video.video_url]
            tags = [{"id": tag.id, "name": tag.name} for tag in restaurant.tags]
            
            result.append({
                "id": restaurant.id,
                "name": restaurant.name,
                "location": restaurant.location,
                "coordinates": restaurant.coordinates,
                "phone": restaurant.phone,
                "rating": restaurant.rating,
                "price_level": restaurant.price_level,
                "video_urls": videos,
                "tags": tags
            })
        
        response = JSONResponse(content=result)
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response
    except Exception as e:
        logger.error(f"Error fetching restaurants: {str(e)}", exc_info=True)
        raise

@app.get("/cities")
async def get_cities(db: Session = Depends(get_db)):
    logger.info("Fetching distinct cities")
    try:
        cities = db.query(distinct(Restaurant.city))\
            .filter(Restaurant.city.isnot(None))\
            .order_by(Restaurant.city)\
            .all()
        logger.info(f"Successfully retrieved {len(cities)} distinct cities")
        return [city[0] for city in cities]
    except Exception as e:
        logger.error(f"Error fetching cities: {str(e)}", exc_info=True)
        raise

@app.get("/tags")
async def get_tags(db: Session = Depends(get_db)):
    logger.info("Fetching all tags")
    try:
        tags = db.query(Tag).all()
        return [{"id": tag.id, "name": tag.name} for tag in tags]
    except Exception as e:
        logger.error(f"Error fetching tags: {str(e)}", exc_info=True)
        raise

@app.post("/log")
async def log_frontend_event(event: dict):
    logger.info(f"Frontend: {event.get('message', 'No message')}", extra={
        "frontend_data": event.get('data', {}),
        "session_id": event.get('data', {}).get('session_id'),
        "timestamp": event.get('timestamp', datetime.now().isoformat())
    })
    return {"status": "logged"}