"""Azure OpenAI Text-to-Speech (TTS) client for generating speech from text."""

import io
import tempfile
from pathlib import Path
from typing import Optional, List, Literal, cast
import time
import subprocess
import os

try:
    from openai import AzureOpenAI
except ImportError:
    AzureOpenAI = None

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger("ai.tts")

# Type alias for response formats
ResponseFormat = Literal["mp3", "opus", "aac", "flac", "wav", "pcm"]

class TTSClient:
    """Azure OpenAI TTS client for text-to-speech synthesis."""
    
    def __init__(self,
                 azure_endpoint: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_version: Optional[str] = None,
                 model: Optional[str] = None,
                 voice: Optional[str] = None,
                 response_format: Optional[str] = None,
                 speed: Optional[float] = None):
        """Initialize TTS client.
        
        Args:
            azure_endpoint: Azure OpenAI endpoint URL
            api_key: Azure OpenAI API key
            api_version: API version to use
            model: TTS model ("tts-1" or "tts-1-hd")
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            response_format: Audio format (mp3, opus, aac, flac, wav, pcm)
            speed: Speech speed (0.25 to 4.0)
        """
        if AzureOpenAI is None:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        # Use simplified configuration
        config = Config.get_tts_config()
        self.azure_endpoint = azure_endpoint or config["azure_endpoint"]
        self.api_key = api_key or config["api_key"]
        self.api_version = api_version or config["api_version"]
        self.model = model or config["model"]
        self.voice = voice or config["voice"]
        self.response_format = response_format or config["response_format"]
        self.speed = speed or config["speed"]
        
        if not self.azure_endpoint or not self.api_key:
            raise ValueError("Azure OpenAI endpoint and API key are required")
        
        # Validate parameters
        self._validate_parameters()
        
        # Initialize Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        logger.info(f"🔊 TTS client initialized (model: {self.model}, voice: {self.voice})")
    
    def _validate_parameters(self):
        """Validate TTS parameters."""
        # For Azure deployment, the model can be the deployment name (e.g., "tts")
        # Valid standard models are ["tts-1", "tts-1-hd"] but Azure allows custom deployment names
        valid_models = ["tts-1", "tts-1-hd", "tts"]  # Include common deployment name
        if self.model not in valid_models:
            logger.warning(f"Using custom model/deployment name: {self.model}")
        
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if self.voice not in valid_voices:
            raise ValueError(f"Invalid voice: {self.voice}. Must be one of {valid_voices}")
        
        valid_formats = ["mp3", "opus", "aac", "flac", "wav", "pcm"]
        if self.response_format not in valid_formats:
            raise ValueError(f"Invalid format: {self.response_format}. Must be one of {valid_formats}")
        
        if not 0.25 <= self.speed <= 4.0:
            raise ValueError(f"Invalid speed: {self.speed}. Must be between 0.25 and 4.0")
    
    def synthesize_text(self, text: str, output_file: Optional[str] = None) -> Optional[str]:
        """Synthesize text to speech and save to file.
        
        Args:
            text: Text to synthesize
            output_file: Output file path (if None, creates temporary file)
            
        Returns:
            Path to generated audio file
        """
        try:
            if not text.strip():
                logger.warning("⚠️ Empty text provided for TTS")
                return None
            
            logger.info(f"🎵 Synthesizing text: {text[:50]}...")
            
            # Generate speech
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=cast(ResponseFormat, self.response_format),
                speed=self.speed
            )
            
            # Determine output file path
            if output_file is None:
                # Create temporary file with WAV extension for high quality
                temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                output_file = temp_file.name
                temp_file.close()
            
            output_path = Path(output_file)
            
            # Collect MP3 data from response
            mp3_data = b""
            for chunk in response.iter_bytes():
                mp3_data += chunk
            
            # Convert MP3 to high-quality WAV using afconvert (same fix as test scripts)
            try:
                # Create temporary MP3 file
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_mp3:
                    temp_mp3.write(mp3_data)
                    temp_mp3_path = temp_mp3.name
                
                # Convert MP3 to WAV using afconvert (macOS built-in, high quality)
                convert_cmd = [
                    'afconvert', 
                    temp_mp3_path, 
                    str(output_path),
                    '-f', 'WAVE',           # WAV format
                    '-d', 'LEI16@44100',    # 16-bit PCM little-endian, 44.1kHz
                    '-c', '1'               # Mono
                ]
                
                result = subprocess.run(convert_cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    logger.info(f"✅ TTS audio converted using afconvert: {output_path}")
                else:
                    logger.warning(f"⚠️ afconvert failed, trying ffmpeg fallback")
                    # Fallback to ffmpeg
                    convert_cmd = [
                        'ffmpeg', '-i', temp_mp3_path, 
                        '-acodec', 'pcm_s16le', '-ar', '44100', '-ac', '1',
                        '-y', str(output_path)
                    ]
                    result = subprocess.run(convert_cmd, capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        logger.info(f"✅ TTS audio converted using ffmpeg: {output_path}")
                    else:
                        logger.warning(f"⚠️ Both afconvert and ffmpeg failed, saving raw MP3")
                        # Final fallback: save raw MP3 (will have quality issues)
                        with open(output_path, "wb") as f:
                            f.write(mp3_data)
                
                # Clean up temporary MP3 file
                try:
                    os.unlink(temp_mp3_path)
                except:
                    pass
                    
            except Exception as e:
                logger.warning(f"⚠️ Audio conversion failed: {e}, saving raw MP3")
                # Fallback: write raw MP3 data (will have quality issues)
                with open(output_path, "wb") as f:
                    f.write(mp3_data)
            
            logger.info(f"✅ TTS synthesis completed: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            return None
    
    def synthesize_to_stream(self, text: str) -> Optional[io.BytesIO]:
        """Synthesize text to audio stream.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as BytesIO stream
        """
        try:
            if not text.strip():
                logger.warning("⚠️ Empty text provided for TTS")
                return None
            
            logger.info(f"🎵 Synthesizing text to stream: {text[:50]}...")
            
            # Generate speech
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=cast(ResponseFormat, self.response_format),
                speed=self.speed
            )
            
            # Create BytesIO stream
            audio_stream = io.BytesIO()
            for chunk in response.iter_bytes():
                audio_stream.write(chunk)
            
            audio_stream.seek(0)  # Reset to beginning
            
            logger.info("✅ TTS synthesis to stream completed")
            return audio_stream
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis to stream failed: {e}")
            return None
    
    def synthesize_text_chunks(self, 
                             text_chunks: list,
                             output_dir: Optional[str] = None) -> list:
        """Synthesize multiple text chunks to separate audio files.
        
        Args:
            text_chunks: List of text strings to synthesize
            output_dir: Directory to save audio files
            
        Returns:
            List of paths to generated audio files
        """
        try:
            if not text_chunks:
                return []
            output_path = Path(output_dir) if output_dir else None
            if output_path and not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            
            audio_files = []
            for i, chunk in enumerate(text_chunks):
                if not chunk.strip():
                    continue
                
                # Determine output file path
                if output_path:
                    filename = f"tts_chunk_{i:03d}.{self.response_format}"
                    output_file = output_path / filename
                else:
                    output_file = None
                
                # Synthesize chunk
                audio_file = self.synthesize_text(chunk, str(output_file) if output_file else None)
                if audio_file:
                    audio_files.append(audio_file)
            
            logger.info(f"✅ Synthesized {len(audio_files)} text chunks")
            return audio_files
            
        except Exception as e:
            logger.error(f"❌ Batch TTS synthesis failed: {e}")
            return []
    
    def get_speech_duration_estimate(self, text: str) -> float:
        """Estimate speech duration for given text.
        
        Args:
            text: Text to estimate duration for
            
        Returns:
            Estimated duration in seconds
        """
        # Rough estimate: average speaking rate is about 150-200 words per minute
        # Adjust for speed setting
        words = len(text.split())
        base_wpm = 175  # words per minute
        adjusted_wpm = base_wpm * self.speed
        duration_minutes = words / adjusted_wpm
        duration_seconds = duration_minutes * 60
        
        # Add small buffer
        return max(1.0, duration_seconds + 0.5)
    
    def split_text_for_synthesis(self, 
                               text: str, 
                               max_length: int = 4000,
                               preserve_sentences: bool = True) -> list:
        """Split long text into chunks suitable for TTS synthesis.
        
        Args:
            text: Text to split
            max_length: Maximum length per chunk
            preserve_sentences: Try to split on sentence boundaries
            
        Returns:
            List of text chunks
        """
        if len(text) <= max_length:
            return [text]
        
        chunks = []
        
        if preserve_sentences:
            # Split on sentence boundaries
            sentences = text.replace('!', '.').replace('?', '.').split('.')
            current_chunk = ""
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue
                
                # Check if adding this sentence would exceed limit
                test_chunk = current_chunk + ". " + sentence if current_chunk else sentence
                
                if len(test_chunk) <= max_length:
                    current_chunk = test_chunk
                else:
                    # Save current chunk and start new one
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = sentence
            
            # Add final chunk
            if current_chunk:
                chunks.append(current_chunk)
        else:
            # Simple split by character count
            for i in range(0, len(text), max_length):
                chunks.append(text[i:i + max_length])
        
        return chunks
    
    async def test_connection(self) -> bool:
        """Test connection to Azure OpenAI TTS.
        
        Returns:
            True if connection successful
        """
        try:
            # Test with simple text
            test_text = "Hello, this is a test."
            
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=test_text,
                response_format="mp3"
            )
            
            # Check if we get audio data
            audio_data = b""
            for chunk in response.iter_bytes():
                audio_data += chunk
                if len(audio_data) > 100:  # Just need some data
                    break
            
            if len(audio_data) > 0:
                logger.info("✅ TTS connection test successful")
                return True
            else:
                logger.warning("⚠️ TTS connection test returned no audio data")
                return False
                
        except Exception as e:
            logger.error(f"❌ TTS connection test failed: {e}")
            return False
    
    def get_available_voices(self) -> list:
        """Get list of available voices.
        
        Returns:
            List of voice names with descriptions
        """
        return [
            {"name": "alloy", "description": "Neutral, balanced voice"},
            {"name": "echo", "description": "Male, friendly voice"},
            {"name": "fable", "description": "Female, warm voice"},
            {"name": "onyx", "description": "Male, deep voice"},
            {"name": "nova", "description": "Female, professional voice"},
            {"name": "shimmer", "description": "Female, bright voice"}
                ]
    
    async def close(self):
        """Close the client connection."""
        # Azure OpenAI client doesn't always need explicit closing
        logger.info("TTS client closed")
    
    async def synthesize_speech(self, text: str) -> Optional[bytes]:
        """Synthesize speech and return audio data as bytes.
        
        Args:
            text: Text to synthesize
            
        Returns:
            Audio data as bytes or None if failed
        """
        try:
            if not text.strip():
                logger.warning("⚠️ Empty text provided for TTS")
                return None
            
            logger.info(f"🎵 Synthesizing speech: {text[:50]}...")
            
            # Generate speech
            response = self.client.audio.speech.create(
                model=self.model,
                voice=self.voice,
                input=text,
                response_format=cast(ResponseFormat, self.response_format),
                speed=self.speed
            )
            
            # Collect audio data
            audio_data = b""
            for chunk in response.iter_bytes():
                audio_data += chunk
            
            logger.info(f"✅ TTS synthesis completed: {len(audio_data)} bytes")
            return audio_data
            
        except Exception as e:
            logger.error(f"❌ TTS synthesis failed: {e}")
            return None
    
    def set_voice(self, voice: str):
        """Change the voice setting.
        
        Args:
            voice: Voice name to use
        """
        valid_voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
        if voice not in valid_voices:
            raise ValueError(f"Invalid voice: {voice}. Must be one of {valid_voices}")
        
        self.voice = voice
        logger.info(f"🎙️ Voice changed to: {voice}")
    
    def set_speed(self, speed: float):
        """Change the speech speed.
        
        Args:
            speed: Speech speed (0.25 to 4.0)
        """
        if not 0.25 <= speed <= 4.0:
            raise ValueError(f"Invalid speed: {speed}. Must be between 0.25 and 4.0")
        
        self.speed = speed
        logger.info(f"⚡ Speech speed changed to: {speed}") 