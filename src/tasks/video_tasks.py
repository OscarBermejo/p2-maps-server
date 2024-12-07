from celery import shared_task
from src.services.video_processing.download_video import VideoDownloader
from src.services.video_processing.extract_audio import AudioExtractor
from src.services.video_processing.extract_text import TextExtractor
from src.services.video_processing.utils import query_chatgpt, search_location, store_video_data
import asyncio
import os
import shutil

@shared_task
def process_video(url: str):
    try:
        # 1. Download video and get metadata
        print("[DEBUG] Starting video download...")
        video_id, video_file, audio_file, description, creator_info = asyncio.run(VideoDownloader().process(url))
        print(f"[DEBUG] Download completed. Video ID: {video_id}")
        
        # 2. Extract audio and text in parallel
        print("[DEBUG] Starting audio extraction...")
        audio_data = AudioExtractor().transcribe_audio(audio_file)
        print(f"[DEBUG] Audio extraction completed. Length: {len(audio_data)}")
        print(f"[DEBUG] Audio data: {audio_data[:100]}...")  # Print first 100 chars

        print("\n[DEBUG] Starting text extraction...")
        try:
            text_data = TextExtractor().extract_text(video_file, video_id)
            print(f"[DEBUG] Text extraction completed. Length: {len(text_data)}")
            print(f"[DEBUG] Extracted text: {text_data[:100]}...")  # Print first 100 chars
        except Exception as e:
            print(f"[ERROR] Text extraction failed: {str(e)}")
            print(f"[ERROR] Error type: {type(e)}")
            text_data = ""
        
        # 3. Extract location from text
        print("\n[DEBUG] Starting ChatGPT query...")
        recommendations = query_chatgpt(description, text_data, audio_data)
        print(f"[DEBUG] ChatGPT query completed: {recommendations}")
        
        # 4. Get coordinates and place details
        places_data = search_location(recommendations)
        print(places_data)
        
        # 5. Store all data
        store_video_data(
            video_id=video_id,
            url=url,
            creator_info=creator_info,
            description=description,
            text_data=text_data,
            audio_data=audio_data,
            recommendations=recommendations,
            places_data=places_data
        )

        # 6. Cleanup files
        print(f"[DEBUG] Cleaning up temporary files for video {video_id}")
        
        # Define file paths
        video_file = f"/home/ec2-user/maps-server/files/video/{video_id}.mp4"
        audio_file = f"/home/ec2-user/maps-server/files/audio/{video_id}.wav"
        
        # Remove video file
        if os.path.exists(video_file):
            os.remove(video_file)
            print(f"[DEBUG] Removed video file: {video_file}")
            
        # Remove audio file
        if os.path.exists(audio_file):
            os.remove(audio_file)
            print(f"[DEBUG] Removed audio file: {audio_file}")

    except Exception as e:
        print(f"[ERROR] Major error in process_video: {str(e)}")
        print(f"[ERROR] Error type: {type(e)}")
        raise
