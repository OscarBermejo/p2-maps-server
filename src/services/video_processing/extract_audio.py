import whisper
import os
import sys
import warnings 
import time

# Suppress all warnings
warnings.filterwarnings("ignore")

class AudioExtractor:
    def __init__(self, model_name='small'):
        self.model_name = model_name

    def transcribe_audio(self, audio_path):
        try:
            print(f"[DEBUG] Starting audio transcription process")
            
            # Check if the audio file exists
            if not os.path.isfile(audio_path):
                print(f"[ERROR] Audio file not found: {audio_path}")
                return ""

            # Get file size
            file_size = os.path.getsize(audio_path) / (1024 * 1024)  # Size in MB
            print(f"[DEBUG] Audio file size: {file_size:.2f} MB")

            # Load the Whisper model
            print(f"[DEBUG] Loading Whisper model '{self.model_name}'...")
            start_time = time.time()
            model = whisper.load_model(self.model_name)
            print(f"[DEBUG] Model loaded in {time.time() - start_time:.2f} seconds")

            # Perform transcription
            print(f"[DEBUG] Starting transcription...")
            transcription_start = time.time()
            result = model.transcribe(
                audio_path,
                verbose=True  # Enable progress updates
            )
            transcription_time = time.time() - transcription_start
            print(f"[DEBUG] Transcription completed in {transcription_time:.2f} seconds")

            text = result['text'].strip()
            print(f"[DEBUG] Transcription result length: {len(text)} characters")
            return text

        except Exception as e:
            print(f"[ERROR] Transcription failed: {str(e)}")
            print(f"[ERROR] Error type: {type(e)}")
            return ""

def main(audio_path):
    extractor = AudioExtractor()
    return extractor.transcribe_audio(audio_path)

if __name__ == "__main__":
    main()