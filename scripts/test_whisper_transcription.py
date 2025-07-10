#!/usr/bin/env python3
"""
Test Whisper Speech-to-Text Transcription

This script tests the exact same transcription pipeline used by the main agent,
using a generated TTS audio file to simulate the real scenario.
"""

import sys
import asyncio
import numpy as np
from pathlib import Path
import wave
import time

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, str(Path(project_root) / "src"))

from src.ai.whisper_client import WhisperClient
from src.ai.conversation_manager import ConversationManager
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class WhisperTranscriptionTest:
    def __init__(self):
        self.whisper_client = WhisperClient()
        self.conversation_manager = ConversationManager()
    
    def load_wav_file(self, file_path: str) -> tuple[np.ndarray, int]:
        """Load WAV file and return audio data and sample rate."""
        try:
            with wave.open(file_path, 'rb') as wav_file:
                # Get audio parameters
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                frames = wav_file.getnframes()
                
                print(f"📊 Audio file info:")
                print(f"   Channels: {channels}")
                print(f"   Sample width: {sample_width} bytes")
                print(f"   Sample rate: {sample_rate} Hz")
                print(f"   Frames: {frames}")
                print(f"   Duration: {frames / sample_rate:.2f} seconds")
                
                # Read audio data
                audio_data = wav_file.readframes(frames)
                
                # Convert to numpy array
                if sample_width == 1:
                    audio_array = np.frombuffer(audio_data, dtype=np.uint8)
                    # Convert to signed 16-bit
                    audio_array = (audio_array.astype(np.int16) - 128) * 256
                elif sample_width == 2:
                    audio_array = np.frombuffer(audio_data, dtype=np.int16)
                elif sample_width == 4:
                    audio_array = np.frombuffer(audio_data, dtype=np.int32)
                    # Convert to 16-bit
                    audio_array = (audio_array / 65536).astype(np.int16)
                else:
                    raise ValueError(f"Unsupported sample width: {sample_width}")
                
                # Convert stereo to mono if needed
                if channels == 2:
                    audio_array = audio_array.reshape(-1, 2)
                    audio_array = np.mean(audio_array, axis=1).astype(np.int16)
                
                print(f"✅ Loaded audio: {len(audio_array)} samples")
                return audio_array, sample_rate
                
        except Exception as e:
            logger.error(f"❌ Error loading WAV file: {e}")
            raise
    
    def test_direct_whisper_transcription(self, audio_file: str):
        """Test direct Whisper transcription (method 1)."""
        print(f"\n🎤 Method 1: Direct Whisper File Transcription")
        print("-" * 50)
        
        try:
            start_time = time.time()
            result = self.whisper_client.transcribe_audio_file(
                audio_file,
                language=Config.WHISPER_LANGUAGE,
                temperature=Config.WHISPER_TEMPERATURE,
                response_format="verbose_json"
            )
            end_time = time.time()
            
            print(f"⏱️  Transcription time: {end_time - start_time:.2f} seconds")
            
            if "error" in result:
                print(f"❌ Transcription error: {result['error']}")
                return None
            
            transcribed_text = result.get("text", "").strip()
            print(f"📝 Transcribed text: '{transcribed_text}'")
            
            if "language" in result:
                print(f"🌍 Detected language: {result['language']}")
            if "duration" in result:
                print(f"⏱️  Audio duration: {result['duration']:.2f} seconds")
            
            return transcribed_text
            
        except Exception as e:
            print(f"❌ Direct transcription failed: {e}")
            return None
    
    def test_audio_data_transcription(self, audio_file: str):
        """Test transcription via audio data (method 2)."""
        print(f"\n🔊 Method 2: Audio Data Transcription (Main Agent Method)")
        print("-" * 50)
        
        try:
            # Load audio data
            audio_data, original_sample_rate = self.load_wav_file(audio_file)
            
            # Resample to 16kHz if needed (main agent uses 16kHz)
            target_sample_rate = Config.SAMPLE_RATE
            if original_sample_rate != target_sample_rate:
                print(f"🔄 Resampling from {original_sample_rate}Hz to {target_sample_rate}Hz...")
                # Simple resampling
                ratio = target_sample_rate / original_sample_rate
                new_length = int(len(audio_data) * ratio)
                audio_data = np.interp(
                    np.linspace(0, len(audio_data) - 1, new_length),
                    np.arange(len(audio_data)),
                    audio_data
                ).astype(np.int16)
            
            start_time = time.time()
            result = self.whisper_client.transcribe_audio_data(
                audio_data,
                sample_rate=target_sample_rate,
                language=Config.WHISPER_LANGUAGE,
                temperature=Config.WHISPER_TEMPERATURE,
                response_format="verbose_json"
            )
            end_time = time.time()
            
            print(f"⏱️  Transcription time: {end_time - start_time:.2f} seconds")
            
            if "error" in result:
                print(f"❌ Transcription error: {result['error']}")
                return None
            
            transcribed_text = result.get("text", "").strip()
            print(f"📝 Transcribed text: '{transcribed_text}'")
            
            return transcribed_text
            
        except Exception as e:
            print(f"❌ Audio data transcription failed: {e}")
            return None
    
    def test_speech_segment_transcription(self, audio_file: str):
        """Test speech segment transcription (method 3 - exact main agent method)."""
        print(f"\n🗣️  Method 3: Speech Segment Transcription (Exact Main Agent Pipeline)")
        print("-" * 50)
        
        try:
            # Load audio data
            audio_data, original_sample_rate = self.load_wav_file(audio_file)
            
            # Resample to 16kHz if needed
            target_sample_rate = Config.SAMPLE_RATE
            if original_sample_rate != target_sample_rate:
                print(f"🔄 Resampling from {original_sample_rate}Hz to {target_sample_rate}Hz...")
                ratio = target_sample_rate / original_sample_rate
                new_length = int(len(audio_data) * ratio)
                audio_data = np.interp(
                    np.linspace(0, len(audio_data) - 1, new_length),
                    np.arange(len(audio_data)),
                    audio_data
                ).astype(np.int16)
            
            # Simulate conversation context (like main agent)
            context = "AI Assistant conversation in Google Meet"
            
            start_time = time.time()
            transcribed_text = self.whisper_client.transcribe_speech_segment(
                audio_data,
                sample_rate=target_sample_rate,
                context=context
            )
            end_time = time.time()
            
            print(f"⏱️  Transcription time: {end_time - start_time:.2f} seconds")
            print(f"📝 Transcribed text: '{transcribed_text}'")
            
            return transcribed_text
            
        except Exception as e:
            print(f"❌ Speech segment transcription failed: {e}")
            return None
    
    async def test_full_conversation_pipeline(self, audio_file: str):
        """Test the complete conversation manager pipeline (method 4)."""
        print(f"\n💬 Method 4: Full Conversation Manager Pipeline")
        print("-" * 50)
        
        try:
            # Load audio data
            audio_data, original_sample_rate = self.load_wav_file(audio_file)
            
            # Resample to 16kHz if needed
            target_sample_rate = Config.SAMPLE_RATE
            if original_sample_rate != target_sample_rate:
                print(f"🔄 Resampling from {original_sample_rate}Hz to {target_sample_rate}Hz...")
                ratio = target_sample_rate / original_sample_rate
                new_length = int(len(audio_data) * ratio)
                audio_data = np.interp(
                    np.linspace(0, len(audio_data) - 1, new_length),
                    np.arange(len(audio_data)),
                    audio_data
                ).astype(np.int16)
            
            # Start conversation manager
            self.conversation_manager.start_conversation()
            
            start_time = time.time()
            # This is the exact method the main agent calls!
            response_audio_file = await self.conversation_manager.process_audio_input(
                audio_data,
                target_sample_rate
            )
            end_time = time.time()
            
            print(f"⏱️  Total pipeline time: {end_time - start_time:.2f} seconds")
            
            if response_audio_file:
                print(f"🎵 Generated response audio: {response_audio_file}")
                print("✅ Full conversation pipeline successful!")
                
                # Show file size
                if Path(response_audio_file).exists():
                    size = Path(response_audio_file).stat().st_size
                    print(f"📊 Response audio size: {size} bytes")
            else:
                print("🤐 No response generated")
            
            return response_audio_file
            
        except Exception as e:
            print(f"❌ Full pipeline test failed: {e}")
            return None
        finally:
            self.conversation_manager.stop_conversation()

async def main():
    """Main test function."""
    print("🧪 WHISPER TRANSCRIPTION TEST")
    print("=" * 60)
    
    # Check if test file exists
    test_file = "test_tts_output_1751972513.wav"
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        print("\nAvailable files:")
        for f in Path(".").glob("test_tts_output_*.wav"):
            print(f"  {f.name}")
        return
    
    print(f"📁 Testing with file: {test_file}")
    
    # Create test instance
    test = WhisperTranscriptionTest()
    
    # Test all methods
    try:
        # Method 1: Direct file transcription
        result1 = test.test_direct_whisper_transcription(test_file)
        
        # Method 2: Audio data transcription
        result2 = test.test_audio_data_transcription(test_file)
        
        # Method 3: Speech segment transcription (main agent method)
        result3 = test.test_speech_segment_transcription(test_file)
        
        # Method 4: Full conversation pipeline
        result4 = await test.test_full_conversation_pipeline(test_file)
        
        # Summary
        print(f"\n📋 TRANSCRIPTION RESULTS SUMMARY")
        print("=" * 60)
        print(f"Method 1 (Direct File):      '{result1}'")
        print(f"Method 2 (Audio Data):       '{result2}'")
        print(f"Method 3 (Speech Segment):   '{result3}'")
        print(f"Method 4 (Full Pipeline):    {'Generated response' if result4 else 'No response'}")
        
        # Check consistency
        results = [r for r in [result1, result2, result3] if r]
        if len(set(results)) == 1:
            print("✅ All transcription methods produced consistent results!")
        elif len(set(results)) > 1:
            print("⚠️  Transcription methods produced different results")
        else:
            print("❌ No successful transcriptions")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 