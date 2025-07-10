"""Configuration management for the Google Meet AI Agent."""

import os
from pathlib import Path
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path, override=True)

class Config:
    """Configuration for Google Meet AI Agent using individual service endpoints."""
    
    # === AZURE OPENAI SERVICES ===
    # Whisper (Speech-to-Text)
    WHISPER_ENDPOINT = os.getenv("WHISPER_ENDPOINT")
    WHISPER_API_KEY = os.getenv("WHISPER_API_KEY")
    WHISPER_API_VERSION = os.getenv("WHISPER_API_VERSION", "2024-06-01")
    WHISPER_DEPLOYMENT_NAME = os.getenv("WHISPER_DEPLOYMENT_NAME", "whisper")
    WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "en")  # Force English for better transcription
    WHISPER_TEMPERATURE = float(os.getenv("WHISPER_TEMPERATURE", "0.0"))  # Deterministic transcription
    
    # GPT (Text Generation)
    GPT_ENDPOINT = os.getenv("GPT_ENDPOINT")
    GPT_API_KEY = os.getenv("GPT_API_KEY")
    GPT_API_VERSION = os.getenv("GPT_API_VERSION", "2024-12-01-preview")
    GPT_DEPLOYMENT_NAME = os.getenv("GPT_DEPLOYMENT", "gpt-4o")
    GPT_MAX_TOKENS = int(os.getenv("GPT_MAX_TOKENS", "1000"))
    GPT_TEMPERATURE = float(os.getenv("GPT_TEMPERATURE", "0.7"))
    
    # TTS (Text-to-Speech)
    TTS_ENDPOINT = os.getenv("TTS_ENDPOINT")
    TTS_API_KEY = os.getenv("TTS_API_KEY")
    TTS_API_VERSION = os.getenv("TTS_API_VERSION", "2025-03-01-preview")
    TTS_MODEL = os.getenv("TTS_MODEL", "tts-1")
    TTS_VOICE = os.getenv("TTS_VOICE", "alloy")
    TTS_SPEED = float(os.getenv("TTS_SPEED", "1.0"))
    TTS_FORMAT = os.getenv("TTS_FORMAT", "mp3")
    
    # OpenAI Fallback
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    # === GOOGLE MEET ===
    GMEET_URL = os.getenv("GMEET_URL", "https://meet.google.com/new")
    AGENT_NAME = os.getenv("AGENT_NAME", "AI Assistant")
    
    # === AUDIO SETTINGS ===
    AUDIO_DEVICE_INPUT = os.getenv("AUDIO_DEVICE_INPUT", "BlackHole 2ch")
    AUDIO_DEVICE_OUTPUT = os.getenv("AUDIO_DEVICE_OUTPUT", "BlackHole 2ch")
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
    BUFFER_SIZE = int(os.getenv("BUFFER_SIZE", "1024"))  # Audio buffer size in samples
    CHANNELS = 1  # Mono audio for speech processing
    
    # === CHROME PROFILE ===
    CHROME_PROFILE_PATH = os.getenv("CHROME_PROFILE_PATH", "gmeet_ai_agent_profile")  # Dedicated profile
    USE_CHROME_PROFILE = os.getenv("USE_CHROME_PROFILE", "true").lower() == "true"
    CHROME_EXECUTABLE_PATH = os.getenv("CHROME_EXECUTABLE_PATH")  # Optional custom Chrome path
    
    # === VOICE ACTIVITY DETECTION ===
    VAD_AGGRESSIVENESS = int(os.getenv("VAD_AGGRESSIVENESS", "1"))  # Less aggressive to capture full speech
    MIN_SPEECH_DURATION = float(os.getenv("MIN_SPEECH_DURATION", "0.3"))  # Faster detection
    MIN_SILENCE_DURATION = float(os.getenv("MIN_SILENCE_DURATION", "1.5"))  # Wait longer before ending
    
    # === AGENT BEHAVIOR ===
    RESPONSE_DELAY = float(os.getenv("RESPONSE_DELAY", "0.5"))
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", "50"))
    KEEP_MICROPHONE_ON = os.getenv("KEEP_MICROPHONE_ON", "true").lower() == "true"
    
    # === LOGGING ===
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    # === BACKWARDS COMPATIBILITY ===
    # For unified Azure OpenAI access (fallback to individual services)
    AZURE_OPENAI_ENDPOINT = WHISPER_ENDPOINT or GPT_ENDPOINT or TTS_ENDPOINT
    AZURE_OPENAI_KEY = WHISPER_API_KEY or GPT_API_KEY or TTS_API_KEY
    AZURE_OPENAI_API_VERSION = WHISPER_API_VERSION or GPT_API_VERSION or TTS_API_VERSION
    WHISPER_DEPLOYMENT = WHISPER_DEPLOYMENT_NAME
    GPT_DEPLOYMENT = GPT_DEPLOYMENT_NAME
    TTS_DEPLOYMENT = TTS_MODEL
    
    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration."""
        missing = []
        
        # Check individual service configurations
        if not cls.WHISPER_ENDPOINT:
            missing.append("WHISPER_ENDPOINT")
        if not cls.WHISPER_API_KEY:
            missing.append("WHISPER_API_KEY")
        if not cls.GPT_ENDPOINT:
            missing.append("GPT_ENDPOINT")
        if not cls.GPT_API_KEY:
            missing.append("GPT_API_KEY")
        if not cls.TTS_ENDPOINT:
            missing.append("TTS_ENDPOINT")
        if not cls.TTS_API_KEY:
            missing.append("TTS_API_KEY")
        
        if missing:
            for item in missing:
                print(f"❌ {item} is required")
            return False
        
        return True
    
    @classmethod
    def print_status(cls):
        """Print current configuration status."""
        print("🔧 GMeet AI Agent Configuration")
        print("=" * 40)
        print(f"Agent Name: {cls.AGENT_NAME}")
        print(f"Meeting URL: {cls.GMEET_URL}")
        print(f"Chrome Profile: {'✅' if cls.USE_CHROME_PROFILE else '❌'}")
        
        # Check individual services
        whisper_ok = bool(cls.WHISPER_ENDPOINT and cls.WHISPER_API_KEY)
        gpt_ok = bool(cls.GPT_ENDPOINT and cls.GPT_API_KEY)
        tts_ok = bool(cls.TTS_ENDPOINT and cls.TTS_API_KEY)
        
        print(f"Whisper STT: {'✅' if whisper_ok else '❌'}")
        print(f"GPT Chat: {'✅' if gpt_ok else '❌'}")
        print(f"TTS Speech: {'✅' if tts_ok else '❌'}")
        print(f"Audio Input: {cls.AUDIO_DEVICE_INPUT}")
        print(f"Audio Output: {cls.AUDIO_DEVICE_OUTPUT}")
        print("=" * 40)
    
    @classmethod
    def get_whisper_config(cls) -> Dict[str, Any]:
        """Get Whisper configuration."""
        return {
            "azure_endpoint": cls.WHISPER_ENDPOINT,
            "api_key": cls.WHISPER_API_KEY,
            "api_version": cls.WHISPER_API_VERSION,
            "deployment_name": cls.WHISPER_DEPLOYMENT_NAME,
            "language": cls.WHISPER_LANGUAGE,
            "temperature": cls.WHISPER_TEMPERATURE
        }
    
    @classmethod
    def get_gpt_config(cls) -> Dict[str, Any]:
        """Get GPT configuration."""
        return {
            "azure_endpoint": cls.GPT_ENDPOINT,
            "api_key": cls.GPT_API_KEY,
            "api_version": cls.GPT_API_VERSION,
            "deployment_name": cls.GPT_DEPLOYMENT_NAME,
            "max_tokens": cls.GPT_MAX_TOKENS,
            "temperature": cls.GPT_TEMPERATURE
        }
    
    @classmethod
    def get_tts_config(cls) -> Dict[str, Any]:
        """Get TTS configuration."""
        return {
            "azure_endpoint": cls.TTS_ENDPOINT,
            "api_key": cls.TTS_API_KEY,
            "api_version": cls.TTS_API_VERSION,
            "model": cls.TTS_MODEL,
            "voice": cls.TTS_VOICE,
            "speed": cls.TTS_SPEED,
            "response_format": cls.TTS_FORMAT
        } 