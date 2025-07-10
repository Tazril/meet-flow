"""Azure OpenAI Whisper client for speech-to-text transcription."""

import io
import wave
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
import numpy as np

try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger("ai.whisper")

class WhisperClient:
    """Azure OpenAI Whisper client for speech-to-text transcription."""
    
    def __init__(self, 
                 azure_endpoint: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_version: Optional[str] = None,
                 deployment_name: Optional[str] = None):
        """Initialize Whisper client.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            api_version: API version to use
            deployment_name: Whisper deployment name
        """
        if AzureOpenAI is None:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        # Use simplified configuration
        config = Config.get_whisper_config()
        self.azure_endpoint = azure_endpoint or config["azure_endpoint"]
        self.api_key = api_key or config["api_key"]
        self.api_version = api_version or config["api_version"]
        self.deployment_name = deployment_name or config["deployment_name"]
        
        if not self.azure_endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key are required")
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        logger.info(f"🎤 Whisper client initialized (deployment: {self.deployment_name})")
    
    def transcribe_audio_file(self, 
                            audio_file_path: str,
                            language: Optional[str] = None,
                            prompt: Optional[str] = None,
                            response_format: str = "json",
                            temperature: float = 0.0) -> Dict[str, Any]:
        """Transcribe audio file using Azure OpenAI Whisper.
        
        Args:
            audio_file_path: Path to audio file
            language: Language code (e.g., "en", "es", "fr")
            prompt: Optional context prompt to improve accuracy
            response_format: Response format ("json", "text", "srt", "verbose_json", "vtt")
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Transcription result with text and metadata
        """
        try:
            audio_path = Path(audio_file_path)
            if not audio_path.exists():
                raise FileNotFoundError(f"Audio file not found: {audio_file_path}")
            
            logger.info(f"🎙️ Transcribing audio file: {audio_path.name}")
            
            # Prepare API parameters, filtering out None values
            api_params = {
                "model": self.deployment_name,
                "file": open(audio_path, "rb")
            }
            
            if language is not None:
                api_params["language"] = language
            if prompt is not None:
                api_params["prompt"] = prompt
            
            # Ensure response_format is valid
            valid_formats = ["text", "json", "srt", "verbose_json", "vtt"]
            if response_format not in valid_formats:
                logger.warning(f"Invalid response format '{response_format}', using 'json'")
                response_format = "json"
            
            api_params["response_format"] = response_format
            api_params["temperature"] = temperature
            
            try:
                transcript = self.client.audio.transcriptions.create(**api_params)
            finally:
                # Always close the file
                api_params["file"].close()
            
            if response_format == "json":
                result = {
                    "text": transcript.text,
                    "language": getattr(transcript, 'language', language),
                    "duration": getattr(transcript, 'duration', None),
                    "words": getattr(transcript, 'words', None)
                }
            elif response_format == "verbose_json":
                result = {
                    "text": transcript.text,
                    "language": transcript.language,
                    "duration": transcript.duration,
                    "words": transcript.words,
                    "segments": transcript.segments
                }
            else:
                result = {"text": str(transcript)}
            
            logger.info(f"✅ Transcription completed: {len(result['text'])} characters")
            logger.debug(f"Transcribed text: {result['text'][:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return {"text": "", "error": str(e)}
    
    def transcribe_audio_data(self,
                            audio_data: np.ndarray,
                            sample_rate: int = 16000,
                            language: Optional[str] = None,
                            prompt: Optional[str] = None,
                            response_format: str = "json",
                            temperature: float = 0.0) -> Dict[str, Any]:
        """Transcribe audio from numpy array.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            language: Language code (e.g., "en", "es", "fr")
            prompt: Optional context prompt
            response_format: Response format
            temperature: Sampling temperature
            
        Returns:
            Transcription result with text and metadata
        """
        try:
            # Create temporary WAV file from audio data
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            # Save audio data as WAV file
            self._save_audio_as_wav(audio_data, temp_path, sample_rate)
            
            try:
                # Transcribe the temporary file
                result = self.transcribe_audio_file(
                    str(temp_path),
                    language=language,
                    prompt=prompt,
                    response_format=response_format,
                    temperature=temperature
                )
                return result
            finally:
                # Clean up temporary file
                temp_path.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"❌ Audio data transcription failed: {e}")
            return {"text": "", "error": str(e)}
    
    def transcribe_speech_segment(self,
                                audio_data: np.ndarray,
                                sample_rate: int = 16000,
                                context: Optional[str] = None) -> str:
        """Transcribe a speech segment with context awareness.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate
            context: Previous conversation context for better accuracy
            
        Returns:
            Transcribed text string
        """
        try:
            # Use context as prompt for better accuracy
            prompt = None
            if context:
                # Use last few words as prompt (max 224 tokens for Whisper)
                words = context.split()
                if len(words) > 30:  # Keep prompt reasonable
                    prompt = " ".join(words[-30:])
                else:
                    prompt = context
            
            result = self.transcribe_audio_data(
                audio_data,
                sample_rate=sample_rate,
                prompt=prompt,
                response_format="json",
                temperature=0.1  # Low temperature for more consistent results
            )
            
            return result.get("text", "").strip()
            
        except Exception as e:
            logger.error(f"❌ Speech segment transcription failed: {e}")
            return ""
    
    def _save_audio_as_wav(self, audio_data: np.ndarray, file_path: Path, sample_rate: int):
        """Save audio data as WAV file.
        
        Args:
            audio_data: Audio data as numpy array
            file_path: Output file path
            sample_rate: Audio sample rate
        """
        try:
            # Ensure audio data is in the right format
            if audio_data.dtype != np.int16:
                # Convert float to int16
                if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    audio_data = audio_data.astype(np.int16)
            
            # Write WAV file
            with wave.open(str(file_path), 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
                
        except Exception as e:
            logger.error(f"❌ Failed to save audio as WAV: {e}")
            raise
    
    async def test_connection(self) -> bool:
        """Test connection to Azure OpenAI Whisper.
        
        Returns:
            True if connection successful
        """
        try:
            # Create a simple test audio file (1 second of silence)
            test_audio = np.zeros(16000, dtype=np.int16)  # 1 second at 16kHz
            
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_path = Path(temp_file.name)
            
            try:
                self._save_audio_as_wav(test_audio, temp_path, 16000)
                
                # Try to transcribe the test file
                with open(temp_path, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model=self.deployment_name,
                        file=audio_file,
                        response_format="text"
                    )
                
                logger.info("✅ Whisper connection test successful")
                return True
                
            finally:
                temp_path.unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"❌ Whisper connection test failed: {e}")
            return False
    
    def get_supported_languages(self) -> list:
        """Get list of supported languages.
        
        Returns:
            List of supported language codes
        """
        # Whisper supports these languages
        return [
            "en", "zh", "de", "es", "ru", "ko", "fr", "ja", "pt", "tr", "pl", "ca", "nl",
            "ar", "sv", "it", "id", "hi", "fi", "vi", "he", "uk", "el", "ms", "cs", "ro",
            "da", "hu", "ta", "no", "th", "ur", "hr", "bg", "lt", "la", "mi", "ml", "cy",
            "sk", "te", "fa", "lv", "bn", "sr", "az", "sl", "kn", "et", "mk", "br", "eu",
            "is", "hy", "ne", "mn", "bs", "kk", "sq", "sw", "gl", "mr", "pa", "si", "km",
            "sn", "yo", "so", "af", "oc", "ka", "be", "tg", "sd", "gu", "am", "yi", "lo",
            "uz", "fo", "ht", "ps", "tk", "nn", "mt", "sa", "lb", "my", "bo", "tl", "mg",
            "as", "tt", "haw", "ln", "ha", "ba", "jw", "su"
        ]
    
    async def close(self):
        """Close the client connection."""
        # Azure OpenAI client doesn't always need explicit closing
        logger.info("Whisper client closed")