#!/usr/bin/env python3
"""
Test Audio Recording + Transcription Pipeline

This script tests the complete audio recording and transcription pipeline
exactly as used by the main agent:
1. Record audio from BlackHole 2ch (same input device as main agent)
2. Process and transcribe the audio using the same pipeline
3. Compare results to identify any issues with live audio capture

Usage:
1. Play audio on your laptop (YouTube, music, etc.)
2. Run this script
3. It will record for a few seconds and transcribe what it captured
"""

import sys
import asyncio
import numpy as np
from pathlib import Path
import time
import threading
from datetime import datetime

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)
sys.path.insert(0, str(Path(project_root) / "src"))

from src.audio.capture import AudioCapture
from src.audio.vad import VoiceActivityDetector
from src.ai.whisper_client import WhisperClient
from src.ai.conversation_manager import ConversationManager
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class AudioRecordingTranscriptionTest:
    def __init__(self):
        self.whisper_client = WhisperClient()
        self.conversation_manager = ConversationManager()
        self.audio_capture = None
        self.vad = None
        
    def setup_audio_capture(self):
        """Set up audio capture exactly like the main agent."""
        try:
            print(f"🎤 Setting up audio capture...")
            print(f"   Input device: {Config.AUDIO_DEVICE_INPUT}")
            print(f"   Sample rate: {Config.SAMPLE_RATE} Hz")
            print(f"   Channels: {Config.CHANNELS}")
            
            # Initialize audio capture (same as main agent)
            self.audio_capture = AudioCapture(
                device=Config.AUDIO_DEVICE_INPUT,
                sample_rate=Config.SAMPLE_RATE
            )
            
            # Initialize VAD (same as main agent)
            self.vad = VoiceActivityDetector(
                sample_rate=Config.SAMPLE_RATE,
                aggressiveness=Config.VAD_AGGRESSIVENESS
            )
            
            print("✅ Audio capture setup complete")
            return True
            
        except Exception as e:
            print(f"❌ Audio capture setup failed: {e}")
            return False
    
    def test_simple_recording(self, duration: float = 10.0):
        """Test simple audio recording without VAD."""
        print(f"\n🎙️ Test 1: Simple Audio Recording ({duration}s)")
        print("-" * 50)
        
        try:
            if not self.audio_capture.start_recording():
                print("❌ Failed to start recording")
                return None
            
            print(f"🔴 Recording for {duration} seconds...")
            print("   💡 Play some audio on your laptop now!")
            
            # Record for specified duration
            audio_chunks = []
            start_time = time.time()
            
            while time.time() - start_time < duration:
                chunk = self.audio_capture.get_audio_chunk(timeout=0.1)
                if chunk is not None:
                    audio_chunks.append(chunk)
                time.sleep(0.01)  # Small delay
            
            self.audio_capture.stop_recording()
            
            if not audio_chunks:
                print("❌ No audio captured")
                return None
            
            # Combine chunks
            audio_data = np.concatenate(audio_chunks)
            print(f"✅ Captured {len(audio_data)} samples ({len(audio_data)/Config.SAMPLE_RATE:.2f}s)")
            
            # Check audio levels
            max_amplitude = np.max(np.abs(audio_data))
            rms_amplitude = np.sqrt(np.mean(audio_data.astype(float) ** 2))
            print(f"📊 Audio levels - Max: {max_amplitude:.6f}, RMS: {rms_amplitude:.6f}")
            
            # Save recording
            timestamp = int(time.time())
            filename = f"test_recording_{timestamp}.wav"
            self._save_audio_to_file(audio_data, filename)
            print(f"💾 Saved recording as: {filename}")
            
            return audio_data, filename
            
        except Exception as e:
            print(f"❌ Recording failed: {e}")
            return None
    
    def test_vad_recording(self, max_duration: float = 30.0):
        """Test audio recording with VAD (same as main agent)."""
        print(f"\n🗣️ Test 2: VAD-Based Recording (max {max_duration}s)")
        print("-" * 50)
        
        try:
            if not self.audio_capture.start_recording():
                print("❌ Failed to start recording")
                return None
            
            print("🎧 Listening for speech...")
            print("   💡 Play some speech/audio on your laptop!")
            
            audio_chunks = []
            start_time = time.time()
            speech_detected = False
            
            while time.time() - start_time < max_duration:
                chunk = self.audio_capture.get_audio_chunk(timeout=0.1)
                if chunk is not None:
                    audio_chunks.append(chunk)
                    
                    # Check for speech activity (same as main agent)
                    is_speaking, speech_started, speech_ended = self.vad.update_speech_state(chunk)
                    
                    if speech_started:
                        print("🗣️ Speech detected!")
                        speech_detected = True
                    
                    if speech_ended and speech_detected:
                        print("🔇 Speech ended, stopping recording")
                        break
                
                time.sleep(0.01)
            
            self.audio_capture.stop_recording()
            
            if not audio_chunks:
                print("❌ No audio captured")
                return None
            
            # Get recent audio buffer (same as main agent)
            audio_data = self.audio_capture.get_audio_buffer(duration=5.0)
            if audio_data is None:
                print("⚠️ No audio buffer available, using chunks")
                audio_data = np.concatenate(audio_chunks)
            
            print(f"✅ Captured {len(audio_data)} samples ({len(audio_data)/Config.SAMPLE_RATE:.2f}s)")
            
            # Check audio levels
            max_amplitude = np.max(np.abs(audio_data))
            rms_amplitude = np.sqrt(np.mean(audio_data.astype(float) ** 2))
            print(f"📊 Audio levels - Max: {max_amplitude:.6f}, RMS: {rms_amplitude:.6f}")
            
            # Save recording
            timestamp = int(time.time())
            filename = f"test_vad_recording_{timestamp}.wav"
            self._save_audio_to_file(audio_data, filename)
            print(f"💾 Saved recording as: {filename}")
            
            return audio_data, filename
            
        except Exception as e:
            print(f"❌ VAD recording failed: {e}")
            return None
    
    def test_transcription_pipeline(self, audio_data: np.ndarray, label: str):
        """Test transcription using the same pipeline as main agent."""
        print(f"\n📝 Test 3: Transcription Pipeline ({label})")
        print("-" * 50)
        
        try:
            # Method 1: Direct Whisper transcription
            print("🎤 Method 1: Direct Whisper transcription...")
            start_time = time.time()
            transcribed_text = self.whisper_client.transcribe_speech_segment(
                audio_data,
                sample_rate=Config.SAMPLE_RATE,
                context="AI Assistant conversation in Google Meet"
            )
            end_time = time.time()
            
            print(f"⏱️ Transcription time: {end_time - start_time:.2f} seconds")
            print(f"📝 Transcribed text: '{transcribed_text}'")
            
            if not transcribed_text.strip():
                print("⚠️ No text transcribed - possible issues:")
                print("   - Audio too quiet")
                print("   - No speech in audio")
                print("   - Audio format issues")
                print("   - BlackHole not receiving audio")
            
            return transcribed_text
            
        except Exception as e:
            print(f"❌ Transcription failed: {e}")
            return None
    
    async def test_full_conversation_pipeline(self, audio_data: np.ndarray, label: str):
        """Test the complete conversation manager pipeline."""
        print(f"\n💬 Test 4: Full Conversation Pipeline ({label})")
        print("-" * 50)
        
        try:
            # Start conversation manager
            self.conversation_manager.start_conversation()
            
            start_time = time.time()
            # This is the exact method the main agent calls!
            response_audio_file = await self.conversation_manager.process_audio_input(
                audio_data,
                Config.SAMPLE_RATE
            )
            end_time = time.time()
            
            print(f"⏱️ Total pipeline time: {end_time - start_time:.2f} seconds")
            
            if response_audio_file:
                print(f"🎵 Generated response audio: {response_audio_file}")
                print("✅ Full conversation pipeline successful!")
                
                # Show file size
                if Path(response_audio_file).exists():
                    size = Path(response_audio_file).stat().st_size
                    print(f"📊 Response audio size: {size} bytes")
                    
                    # Clean up response file
                    try:
                        Path(response_audio_file).unlink()
                    except:
                        pass
                        
                return True
            else:
                print("🤐 No response generated - possible issues:")
                print("   - Audio not transcribed")
                print("   - Transcription too short")
                print("   - GPT decided not to respond")
                return False
                
        except Exception as e:
            print(f"❌ Full pipeline test failed: {e}")
            return False
        finally:
            self.conversation_manager.stop_conversation()
    
    def _save_audio_to_file(self, audio_data: np.ndarray, filename: str):
        """Save audio data to WAV file."""
        try:
            import wave
            
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(Config.CHANNELS)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(Config.SAMPLE_RATE)
                wav_file.writeframes(audio_data.astype(np.int16).tobytes())
                
        except Exception as e:
            print(f"❌ Failed to save audio file: {e}")
    
    def run_diagnostics(self):
        """Run audio system diagnostics."""
        print(f"\n🔧 Audio System Diagnostics")
        print("-" * 50)
        
        try:
            # Check audio devices
            print("📱 Available audio devices:")
            if self.audio_capture:
                devices = self.audio_capture._list_audio_devices()
                for i, device in enumerate(devices):
                    marker = " ← TARGET" if Config.AUDIO_DEVICE_INPUT in device.get('name', '') else ""
                    print(f"   {i}: {device.get('name', 'Unknown')}{marker}")
            
            # Check configuration
            print(f"\n⚙️ Configuration:")
            print(f"   Input device: {Config.AUDIO_DEVICE_INPUT}")
            print(f"   Sample rate: {Config.SAMPLE_RATE} Hz")
            print(f"   VAD aggressiveness: {Config.VAD_AGGRESSIVENESS}")
            print(f"   Min speech duration: {Config.MIN_SPEECH_DURATION}s")
            print(f"   Min silence duration: {Config.MIN_SILENCE_DURATION}s")
            
        except Exception as e:
            print(f"❌ Diagnostics failed: {e}")

async def main():
    """Main test function."""
    print("🧪 AUDIO RECORDING + TRANSCRIPTION TEST")
    print("=" * 60)
    print("This test simulates the exact audio pipeline used by main.py")
    print("It will record from BlackHole 2ch and transcribe the audio")
    print("=" * 60)
    
    # Create test instance
    test = AudioRecordingTranscriptionTest()
    
    # Setup audio capture
    if not test.setup_audio_capture():
        print("❌ Failed to setup audio capture")
        return
    
    # Run diagnostics
    test.run_diagnostics()
    
    print(f"\n🎵 PREPARATION:")
    print("1. Make sure BlackHole 2ch is your system's Default Input Device")
    print("2. Make sure Multi-Output Device is your system's Default Output Device")
    print("3. Open a YouTube video, music, or any audio source")
    print("4. Keep the audio playing during the tests")
    
    input("\nPress Enter when ready to start recording tests...")
    
    # Test 1: Simple recording
    result1 = test.test_simple_recording(duration=5.0)
    if result1:
        audio_data1, filename1 = result1
        
        # Transcribe the simple recording
        transcription1 = test.test_transcription_pipeline(audio_data1, "Simple Recording")
        
        # Test full pipeline
        await test.test_full_conversation_pipeline(audio_data1, "Simple Recording")
    
    input("\nPress Enter to test VAD-based recording (speak or play speech audio)...")
    
    # Test 2: VAD recording
    result2 = test.test_vad_recording(max_duration=15.0)
    if result2:
        audio_data2, filename2 = result2
        
        # Transcribe the VAD recording
        transcription2 = test.test_transcription_pipeline(audio_data2, "VAD Recording")
        
        # Test full pipeline
        await test.test_full_conversation_pipeline(audio_data2, "VAD Recording")
    
    # Summary
    print(f"\n📋 TEST SUMMARY")
    print("=" * 60)
    if result1:
        print(f"✅ Simple recording: {filename1}")
        if 'transcription1' in locals() and transcription1:
            print(f"   Transcription: '{transcription1[:100]}...'")
        else:
            print(f"   ❌ No transcription")
    
    if result2:
        print(f"✅ VAD recording: {filename2}")
        if 'transcription2' in locals() and transcription2:
            print(f"   Transcription: '{transcription2[:100]}...'")
        else:
            print(f"   ❌ No transcription")
    
    print(f"\n💡 If no audio was captured:")
    print("   - Check if BlackHole is receiving audio from other apps")
    print("   - Verify Multi-Output Device is working")
    print("   - Test with Audio MIDI Setup.app")
    print("   - Make sure audio is actually playing on your system")

if __name__ == "__main__":
    asyncio.run(main()) 