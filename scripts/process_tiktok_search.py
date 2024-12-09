from tiktokapipy.api import TikTokAPI
from typing import List
import time
from sqlalchemy import select
import sys
import os
import logging
# Suppress SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
# Suppress MySQL Connector logging
logging.getLogger('mysql.connector').setLevel(logging.WARNING)


# Replace the existing sys.path.append line with these:
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.tasks.video_tasks import process_video
from src.database import SessionLocal
from src.models.models import Video

# Barcelona-specific restaurant hashtags
BARCELONA_HASHTAGS = [
    "restaurantesbarcelona",
    "barcelonafood",
    "foodbarcelona",
    "barcelonafoodie",
    "comerenbcn",
    "comerbarcelona",
    "barcelonaeats",
    "dondecomerbcn",
    "barcelonafoodguide",
    "bcnfood",
    "bcnfoodie",
    "barcelonafoodies",
    "restaurantsbarcelona",
    "barcelonagastronomia"
]

# Melbourne-specific restaurant hashtags
MELBOURNE_HASHTAGS = [
    "melbournerestaurants",
    "melbournefood",
    "melbournefoodie",
    "melbourneeats",
    "foodmelbourne",
    "melbournefoodscene",
    "melbournefoodguide",
    "melbournefoodspots",
    "melbournefoodblog",
    "melbournecafe",
    "wheretoeatingmelbourne",
    "melbournebrunch",
    "melbournedining",
    "visitmelbourne",
    "melbournefoodshare"
]

def video_exists(video_id: str, db_session) -> bool:
    print(f"[DEBUG] Checking if video {video_id} exists in database")
    query = select(Video).where(Video.video_id == video_id)
    result = db_session.execute(query).first()
    print(f"[DEBUG] Video exists: {result is not None}")
    return result is not None

def get_challenge_videos(hashtag: str, max_videos: int = 10) -> List[dict]:
    print(f"\n[DEBUG] Starting get_challenge_videos for #{hashtag}")
    video_data = []
    
    print("[DEBUG] Initializing TikTokAPI")
    with TikTokAPI(
        headless=True,
        navigation_timeout=60000
    ) as api:
        try:
            hashtag = hashtag.replace('#', '')
            print(f"[DEBUG] Cleaned hashtag: #{hashtag}")
            
            print("[DEBUG] Fetching challenge data from TikTok")
            challenge = api.challenge(hashtag, video_limit=max_videos)
            
            print("[DEBUG] Opening database session")
            db = SessionLocal()
            
            print("[DEBUG] Starting to process videos")
            for video in challenge.videos:
                video_id = str(video.id)
                print(f"\n[DEBUG] Processing video ID: {video_id}")
                
                if video_exists(video_id, db):
                    print(f"[DEBUG] Video {video_id} already exists, skipping")
                    continue
                
                try:
                    video_info = {
                        'url': f"https://www.tiktok.com/@{video.author.unique_id}/video/{video_id}",
                        'views': getattr(video.stats, 'play_count', 0),
                        'likes': getattr(video.stats, 'digg_count', 0),
                        'video_id': video_id
                    }
                    video_data.append(video_info)
                except AttributeError as e:
                    print(f"Skipping video due to missing attributes: {e}")
                    continue
            
            db.close()
            
            # Sort videos by view count (descending)
            video_data.sort(key=lambda x: x['views'], reverse=True)
            return video_data[:max_videos]
                
        except Exception as e:
            print(f"Error fetching challenge videos: {e}")
            print(f"Error type: {type(e)}")
            return []

def process_hashtag_videos(hashtag: str, max_videos: int = 100):
    print(f"\n=== Fetching TikTok videos for hashtag: #{hashtag} ===")
    videos = get_challenge_videos(hashtag, max_videos)
    print(f"[DEBUG] Found {len(videos)} new videos to process")
    
    for i, video in enumerate(videos, 1):
        try:
            print(f"\nProcessing video {i}/{len(videos)}: {video['url']}")
            print(f"Views: {video.get('view_count', 'N/A')}")
            process_video(video['url'])
            # Add longer sleep between videos to avoid rate limiting
            time.sleep(5)
        except Exception as e:
            print(f"[ERROR] Failed to process video {video['url']}: {str(e)}")
            continue

if __name__ == "__main__":
    total_processed = 0
    failed_hashtags = []
    
    print(f"Starting to process {len(BARCELONA_HASHTAGS)} hashtags for Barcelona restaurants...")
    
    for hashtag in BARCELONA_HASHTAGS:
        try:
            print(f"\n{'='*50}")
            print(f"Processing hashtag: {hashtag}")
            print(f"{'='*50}")
            process_hashtag_videos(hashtag, max_videos=100)
            total_processed += 1
        except Exception as e:
            print(f"[ERROR] Failed to process hashtag #{hashtag}: {str(e)}")
            failed_hashtags.append(hashtag)
            continue
            
    print(f"\n{'='*50}")
    print("Processing completed!")
    print(f"Successfully processed {total_processed}/{len(BARCELONA_HASHTAGS)} hashtags")
    if failed_hashtags:
        print(f"Failed hashtags: {', '.join(failed_hashtags)}")