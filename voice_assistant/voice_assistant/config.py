import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).parent.absolute()
DATA_DIR = BASE_DIR / 'data'
MODELS_DIR = BASE_DIR / 'models'
PLUGINS_DIR = BASE_DIR / 'plugins'

# Create necessary directories
for directory in [DATA_DIR, MODELS_DIR, PLUGINS_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# Voice Recognition Settings
class VoiceConfig:
    # Wake words and activation
    WAKE_WORDS = ["hey assistant", "hello buddy", "computer"]
    ACTIVATION_METHOD = "continuous"  # or "push_to_talk"
    
    # Speech recognition
    ENERGY_THRESHOLD = 300  # Minimum audio energy to consider for recording
    DEFAULT_MICROPHONE = None  # None for default
    PAUSE_THRESHOLD = 0.8  # Seconds of non-speaking audio before a phrase is considered complete
    
    # Text-to-Speech
    VOICE_RATE = 170  # Words per minute
    VOICE_VOLUME = 0.9  # 0.0 to 1.0
    VOICE_ID = 0  # 0 for male, 1 for female (Windows)


# API Keys (loaded from environment variables)
class APIConfig:
    WOLFRAM_ALPHA_APP_ID = os.getenv('WOLFRAM_ALPHA_APP_ID', '')
    OPENWEATHER_API_KEY = os.getenv('OPENWEATHER_API_KEY', '')
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', '')
    

# Application Settings
class AppConfig:
    # UI Settings
    THEME = "dark"  # or "light"
    LANGUAGE = "en"  # Default language
    
    # Performance
    MAX_WORKERS = 4  # Maximum number of worker threads
    CACHE_EXPIRY = 3600  # Cache expiry in seconds
    
    # Privacy
    LOG_CONVERSATIONS = True
    ENCRYPT_STORAGE = True
    

# Paths
class Paths:
    LOGS_DIR = DATA_DIR / 'logs'
    CACHE_DIR = DATA_DIR / 'cache'
    PROFILES_DIR = DATA_DIR / 'profiles'
    PLUGINS_CONFIG = DATA_DIR / 'plugins.json'
    
    # Create paths if they don't exist
    for path in [LOGS_DIR, CACHE_DIR, PROFILES_DIR]:
        path.mkdir(exist_ok=True, parents=True)


# Initialize configurations
class Config:
    voice = VoiceConfig()
    api = APIConfig()
    app = AppConfig()
    paths = Paths()


# Create a singleton instance
config = Config()
