import yt_dlp
import aiohttp
from bs4 import BeautifulSoup
import json
from functools import lru_cache, wraps
import asyncio
import ssl
import certifi
import logging
import os
import ffmpeg
import time
from dataclasses import dataclass, field
from typing import Dict, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
@dataclass
class DownloadConfig:
    base_path: str = '/home/ec2-user/maps-server/files'
    video_path: str = field(init=False)
    audio_path: str = field(init=False)
    ydl_opts: Dict = field(default_factory=lambda: {'quiet': True})

    def __post_init__(self):
        self.video_path = f"{self.base_path}/video"
        self.audio_path = f"{self.base_path}/audio"
        self._ensure_directories()

    def _ensure_directories(self):
        """Ensure necessary directories exist"""
        for path in [self.video_path, self.audio_path]:
            os.makedirs(path, exist_ok=True)

# Decorators
def retry_with_backoff(max_retries=3, initial_delay=1):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay)
                        delay *= 2
            
            raise last_exception
        return wrapper
    return decorator

def measure_time(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time
        logger.info(f"{func.__name__} took {duration:.2f} seconds")
        return result
    return wrapper

class VideoDownloader:
    def __init__(self, config: DownloadConfig = DownloadConfig()):
        print("Initializing VideoDownloader...")
        self.config = config
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())

    @retry_with_backoff(max_retries=3)
    async def extract_video_id(self, url: str) -> str:
        print(f"Extracting video ID from URL: {url}")
        with yt_dlp.YoutubeDL(self.config.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            print(f"Extracted video ID: {info['id']}")
            return info['id']

    @retry_with_backoff(max_retries=3)
    async def download_video(self, url: str, video_id: str) -> str:
        print(f"Starting video download for ID: {video_id}")
        output_file = f"{self.config.video_path}/{video_id}.mp4"
        ydl_opts = {
            **self.config.ydl_opts,
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': output_file
        }
        
        def _download():
            print("Downloading video...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            print(f"Video downloaded to: {output_file}")
            return output_file
        
        return await asyncio.to_thread(_download)

    @retry_with_backoff(max_retries=3)
    async def extract_description(self, url: str) -> str:
        print("Extracting video description...")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, ssl=self.ssl_context) as response:
                content = await response.text()

        soup = BeautifulSoup(content, 'html.parser')
        for script in soup.find_all('script'):
            if script.string:
                try:
                    json_data = json.loads(script.string)
                    if '__DEFAULT_SCOPE__' in json_data:
                        scope = json_data['__DEFAULT_SCOPE__']
                        if isinstance(scope, list):
                            for item in scope:
                                if 'webapp.video-detail' in item:
                                    desc = item['webapp.video-detail']['itemInfo']['itemStruct']['desc']
                                    print(f"Description extracted: {desc[:100]}...")  # Print first 100 chars
                                    return desc
                        elif isinstance(scope, dict):
                            desc = scope['webapp.video-detail']['itemInfo']['itemStruct']['desc']
                            print(f"Description extracted: {desc[:100]}...")  # Print first 100 chars
                            return desc
                except (json.JSONDecodeError, KeyError, TypeError):
                    continue
        print("No description found")
        return ""

    async def extract_audio(self, video_file: str) -> str:
        print(f"Starting audio extraction from: {video_file}")
        video_id = os.path.splitext(os.path.basename(video_file))[0]
        output_file = f"{self.config.audio_path}/{video_id}.wav"
        
        try:
            cmd = [
                'ffmpeg', '-i', video_file,
                '-vn',  # No video
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-y',  # Overwrite output file
                output_file
            ]
            print(f"Running FFmpeg command: {' '.join(cmd)}")
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                print(f"FFmpeg error: {stderr.decode()}")
                raise Exception(f"FFmpeg failed: {stderr.decode()}")
            
            print(f"Audio extracted successfully to: {output_file}")
            return output_file
        except Exception as e:
            print(f"Error during audio extraction: {str(e)}")
            logger.error(f"Error extracting audio: {str(e)}")
            raise

    @measure_time
    async def process(self, url: str) -> tuple:
        print(f"\n=== Starting video processing for URL: {url} ===")
        
        # First extract all video info to get creator details
        with yt_dlp.YoutubeDL(self.config.ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_id = info['id']
            creator_name = f"@{info['uploader']}" if info.get('uploader') else None
            creator_id = info.get('uploader_id')
        
        print("Starting concurrent video download and description extraction...")
        video_file, description = await asyncio.gather(
            self.download_video(url, video_id),
            self.extract_description(url)
        )
        
        print("Starting audio extraction...")
        audio_file = await self.extract_audio(video_file)
        
        print("\n=== Video processing completed ===")
        print(f"Video ID: {video_id}")
        print(f"Video file: {video_file}")
        print(f"Audio file: {audio_file}")
        print(f"Description length: {len(description)} characters")
        
        try:
            creator_info = {
                'creator_name': creator_name,
                'creator_id': creator_id,
                'view_count': info.get('view_count')  # Also getting view count from the API
            }
            
            return video_id, video_file, audio_file, description, creator_info
            
        except Exception as e:
            print(f"Error in video processing: {str(e)}")
            raise

async def extract_data(url: str) -> tuple:
    """Convenience function for external use"""
    downloader = VideoDownloader()
    return await downloader.process(url)