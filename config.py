import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # API Keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    JAMENDO_CLIENT_ID = os.getenv("JAMENDO_CLIENT_ID")
    FREESOUND_API_KEY = os.getenv("FREESOUND_API_KEY")
    
    # Directories
    MUSIC_DIR = "music"
    EXPORTS_DIR = "exports"
    TEMP_DIR = "temp"
    
    # Audio Settings
    DEFAULT_SAMPLE_RATE = 44100
    DEFAULT_CHANNELS = 2
    DEFAULT_BIT_DEPTH = 16
    
    # Mix Settings
    MAX_MIX_DURATION = 600  # 10 minutes
    DEFAULT_FADE_DURATION = 3000  # 3 seconds
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        for dir_path in [cls.MUSIC_DIR, cls.EXPORTS_DIR, cls.TEMP_DIR]:
            os.makedirs(dir_path, exist_ok=True)