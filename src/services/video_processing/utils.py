from typing import Dict, Optional, Union
import re
import googlemaps
import openai
import sys
import os
from openai.types.chat import ChatCompletion
from decouple import config  # Add this import at the top
import json
import boto3
from datetime import datetime
from botocore.exceptions import ClientError


# Add the directory above the current one to the system path
#sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
#from config import Config

#logger = logger_config.get_logger(__name__)

gmaps = googlemaps.Client(key=config('GOOGLE_MAPS_API_KEY'))

def query_chatgpt(description: str, text: str, transcription: str) -> str:
    """
    Query ChatGPT to extract places of interest from video information.
    
    Args:
        description: Video description
        text: Extracted text from video
        transcription: Video transcription
    
    Returns:
        str: Formatted recommendations or "No places of interest found"
    """
    if not any([description, text, transcription]):
        print("All input parameters are empty")
        return "No places of interest found"

    chatgpt_query = f"""
        Analyze the following information from a TikTok video and identify recommended places:
        
        Description: {description}
        Transcription: {transcription}
        Text in images: {text}
        
        Instructions:
        1. Return only specific places that are being explicitly recommended or reviewed
        2. Format each place as: [Place Name], [City/Country], [Type of Place]
        3. One place per line
        4. If no specific place is mentioned, return exactly: "No places of interest found"
        
        Example format:
        Maseria Moroseta, Ostuni Italy, Boutique Hotel
        Grotta Palazzese, Polignano Italy, Restaurant
    """

    # Initialize OpenAI client with API key
    openai.api_key = config('OPENAI_API_KEY')
    
    try:
        response: ChatCompletion = openai.chat.completions.create(
            model="gpt-4-turbo-preview",  # Updated to latest model
            messages=[{"role": "user", "content": chatgpt_query}],
            max_tokens=150,
            temperature=0.3  # Reduced for more consistent outputs
        )
        return response.choices[0].message.content.strip()
    except openai.APIError as e:
        print(f"OpenAI API error: {str(e)}", exc_info=True)
        return "No places of interest found"

def search_location(recommendations: str) -> Dict[str, Dict]:
    """
    Search for places using Google Maps API and return their details.
    
    Args:
        recommendations: String containing place recommendations
    
    Returns:
        Dict mapping place names to their details including:
        - Google Maps link
        - Rating
        - Price level
        - Opening hours
        - Contact info
    """
    if not recommendations or "No places of interest found" in recommendations:
        print("No valid recommendations to search")
        return {}

    google_map_dict = {}
    places = [place.strip() for place in recommendations.splitlines() if place.strip()]
    print(f'Places recommended: {places}')

    for location in places:
        if not location:
            continue

        try:
            place_name = location.split(',')[0].strip()
            
            # First get basic place info
            result = gmaps.places(query=place_name)
            if result['status'] == 'OK':
                place = result['results'][0]
                place_id = place['place_id']
                
                # Get detailed place information
                place_details = gmaps.place(place_id, fields=[
                    'name',
                    'formatted_address',
                    'geometry/location',
                    'rating',
                    'price_level',
                    'formatted_phone_number',
                    'opening_hours',
                    'website',
                    'user_ratings_total'
                ])['result']
                
                location_info = {
                    'name': place['name'],
                    'address': place.get('formatted_address', 'No address found'),
                    'latitude': place['geometry']['location']['lat'],
                    'longitude': place['geometry']['location']['lng'],
                    'google_maps_link': f"https://www.google.com/maps/place/?q=place_id:{place_id}",
                    'rating': place_details.get('rating', 'No rating'),
                    'total_ratings': place_details.get('user_ratings_total', 0),
                    'price_level': {
                        0: 'Free',
                        1: '$',
                        2: '$$',
                        3: '$$$',
                        4: '$$$$'
                    }.get(place_details.get('price_level'), 'Price not available'),
                    'phone': place_details.get('formatted_phone_number', 'No phone number'),
                    'website': place_details.get('website', 'No website'),
                }
                
                # Add opening hours if available
                if 'opening_hours' in place_details:
                    location_info['is_open_now'] = place_details['opening_hours'].get('open_now')
                    location_info['hours'] = place_details['opening_hours'].get('weekday_text', [])
                
                google_map_dict[location] = location_info
                print(f"Successfully found location for: {location}")
            else:
                print(f"No results found for location: {location}")
        
        except Exception as e:
            print(f"Error searching location '{location}': {str(e)}", exc_info=True)
            continue

    return google_map_dict

def store_video_data(video_id: str, url: str, creator_info: dict, description: str, 
                     text_data: str, audio_data: str, recommendations: str, places_data: dict) -> None:
    """
    Store video processing results in both S3 and database.
    
    Args:
        video_id: Unique identifier for the video
        url: Original video URL
        creator_info: Dictionary containing creator information
        description: Video description
        text_data: Extracted text from video
        audio_data: Transcribed audio data
        recommendations: Processed recommendations from ChatGPT
        places_data: Dictionary containing place details
    """
    # Prepare data structure
    extracted_data = {
        "video_id": video_id,
        "platform": "tiktok",
        "video_url": url,
        "creator_info": creator_info,
        "extracted_data": {
        "description": description,
        "text_data": text_data,
        "audio_data": audio_data,
        "recommendations": recommendations
        },
        "places_data": places_data,
        "processed_at": datetime.utcnow().isoformat()
    }

    # Save to S3
    try:
        s3_client = boto3.client('s3')
        bucket_name = config('AWS_S3_BUCKET')
        s3_key = f'video_data/{video_id}.json'
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=s3_key,
            Body=json.dumps(extracted_data, ensure_ascii=False),
            ContentType='application/json'
        )
        print(f"Successfully saved data to S3: s3://{bucket_name}/{s3_key}")
    except ClientError as e:
        print(f"Error saving to S3: {str(e)}")

    # Save to database
    try:
        from src.utils.database_utils import update_database
        update_database(
            video_id=video_id,
            platform="tiktok",
            video_url=url,
            creator_info=creator_info,
            places_data=places_data
        )
        print("Successfully updated database")
    except Exception as e:
        print(f"Error updating database: {str(e)}")