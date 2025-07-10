#!/usr/bin/env python3
"""
Test: Text → TTS → System Audio → BlackHole → AI Agent Detection

This test verifies the full audio routing pipeline by:
1. Converting text to speech using Azure TTS
2. Playing the speech through system audio 
3. Monitoring BlackHole to see if the AI agent detects it
"""

import asyncio
import sys
import os
import time
import threading
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.ai.tts_client import TTSClient
from src.audio.capture import AudioCapture
from src.audio.vad import VoiceActivityDetector
from src.audio.playback import AudioPlayback
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class TTSToBlackHoleTest:
    def __init__(self):
        self.config = Config()
        self.tts_client = TTSClient()  # TTS client gets config internally
        self.audio_capture = AudioCapture()  # AudioCapture gets config internally
        self.vad = VoiceActivityDetector()
        self.audio_playback = AudioPlayback()  # AudioPlayback gets config internally
        
        self.detection_results = []
        self.listening = False
        
    async def generate_test_speech(self, text: str) -> tuple[bytes, str]:
        """Generate speech audio from text using TTS"""
        logger.info(f"🗣️  Generating TTS for: '{text}'")
        audio_data = await self.tts_client.synthesize_speech(text)
        
        # Save to output file
        output_file = f"test_tts_output_{int(time.time())}.wav"
        file_path = self.save_audio_to_file(audio_data, output_file)
        
        logger.info(f"✅ TTS generated: {len(audio_data)} bytes")
        logger.info(f"💾 Audio saved to: {file_path}")
        
        return audio_data, file_path
    
    def save_audio_to_file(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to proper WAV file with correct format conversion"""
        import tempfile
        import subprocess
        
        # Azure TTS returns encoded audio (MP3), not raw PCM
        # We need to properly convert it to WAV format
        
        # First, save the raw TTS data to a temporary file
        temp_input = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_input.write(audio_data)
        temp_input.close()
        
        # Output file path
        file_path = os.path.join(os.getcwd(), filename)
        
        try:
            # Try afconvert first (macOS built-in, more reliable)
            subprocess.run([
                'afconvert', 
                temp_input.name,  # Input
                file_path,  # Output
                '-d', 'LEI16',  # Data format: Little Endian Integer 16-bit
                '-f', 'WAVE',  # File format: WAV
                '-r', '44100',  # Sample rate: 44.1kHz (higher quality for Meet)
                '-c', '1'  # Channels: mono
            ], check=True, capture_output=True)
            
            logger.info(f"✅ Audio converted using afconvert: {file_path}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ afconvert failed: {e}")
            # Fallback: try with ffmpeg if available
            try:
                subprocess.run([
                    'ffmpeg', '-y',  # -y to overwrite output file
                    '-i', temp_input.name,  # Input: TTS MP3 data
                    '-acodec', 'pcm_s16le',  # Audio codec: 16-bit PCM little-endian
                    '-ar', '44100',  # Sample rate: 44.1kHz (higher quality for Meet)
                    '-ac', '1',  # Channels: mono
                    '-f', 'wav',  # Format: WAV
                    file_path  # Output file
                ], check=True, capture_output=True)
                
                logger.info(f"✅ Audio converted using ffmpeg: {file_path}")
                
            except (subprocess.CalledProcessError, FileNotFoundError) as e2:
                logger.error(f"❌ ffmpeg also failed: {e2}")
                # Last resort: save as MP3 directly
                mp3_path = file_path.replace('.wav', '.mp3')
                with open(mp3_path, 'wb') as f:
                    f.write(audio_data)
                file_path = mp3_path
                logger.warning(f"⚠️  Saved as MP3 instead: {file_path}")
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_input.name)
            except:
                pass
        
        return file_path
        
    def start_listening(self):
        """Start listening for audio on BlackHole in a separate thread"""
        def listen_worker():
            logger.info("🎧 Starting BlackHole listener...")
            self.listening = True
            
            try:
                # Start audio capture
                self.audio_capture.start_recording()
                
                chunk_count = 0
                max_volume = 0.0
                speech_chunks = 0
                
                while self.listening:
                    # Get audio chunk
                    audio_chunk = self.audio_capture.get_audio_chunk()
                    if audio_chunk is None:
                        continue
                        
                    chunk_count += 1
                    
                    # Calculate volume
                    import numpy as np
                    volume = np.sqrt(np.mean(audio_chunk**2))
                    max_volume = max(max_volume, volume)
                    
                    # Check for speech
                    is_speech, _, _ = self.vad.update_speech_state(audio_chunk)
                    if is_speech:
                        speech_chunks += 1
                        logger.info(f"🗣️  SPEECH DETECTED! Chunk {chunk_count}, Volume: {volume:.3f}")
                    
                    # Progress indicator
                    if chunk_count % 50 == 0:  # Every ~1.5 seconds
                        volume_bar = "█" * int(volume * 50) + "░" * (50 - int(volume * 50))
                        print(f"\r🎧 Listening... Vol: [{volume_bar[:30]}] {volume:.3f} | Chunks: {chunk_count} | Speech: {speech_chunks}", end="", flush=True)
                
                self.detection_results = {
                    'total_chunks': chunk_count,
                    'max_volume': max_volume,
                    'speech_chunks': speech_chunks
                }
                
            except Exception as e:
                logger.error(f"❌ Listening error: {e}")
            finally:
                self.audio_capture.stop_recording()
                print()  # New line after progress
                
        # Start listener thread
        self.listener_thread = threading.Thread(target=listen_worker, daemon=True)
        self.listener_thread.start()
        time.sleep(1)  # Give listener time to start
        
    def stop_listening(self):
        """Stop listening for audio"""
        logger.info("🛑 Stopping BlackHole listener...")
        self.listening = False
        if hasattr(self, 'listener_thread'):
            self.listener_thread.join(timeout=2)
        
    async def play_tts_audio(self, audio_data: bytes):
        """Play TTS audio through system speakers with proper conversion"""
        logger.info("🔊 Playing TTS audio through system speakers...")
        
        import tempfile
        import subprocess
        
        # Azure TTS returns encoded audio (MP3), not raw PCM
        # We need to properly convert it before playing
        
        # First, save the raw TTS data to a temporary MP3 file
        temp_input = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False)
        temp_input.write(audio_data)
        temp_input.close()
        
        # Create temporary WAV file for playback
        temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
        temp_wav.close()
        
        try:
            # Convert MP3 to high-quality WAV using afconvert
            subprocess.run([
                'afconvert', 
                temp_input.name,  # Input: TTS MP3 data
                temp_wav.name,  # Output: converted WAV
                '-d', 'LEI16',  # Data format: Little Endian Integer 16-bit
                '-f', 'WAVE',  # File format: WAV
                '-r', '44100',  # Sample rate: 44.1kHz (higher quality)
                '-c', '1'  # Channels: mono
            ], check=True, capture_output=True)
            
            logger.info("✅ Audio converted for playback")
            
            # Play the converted WAV file
            result = subprocess.run([
                'afplay', temp_wav.name
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                logger.info("✅ Audio played successfully")
            else:
                logger.error(f"❌ Audio playback failed: {result.stderr}")
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Audio conversion failed: {e}")
            # Fallback: try playing the MP3 directly
            try:
                result = subprocess.run([
                    'afplay', temp_input.name
                ], capture_output=True, text=True, timeout=10)
                
                if result.returncode == 0:
                    logger.info("✅ Audio played successfully (MP3 fallback)")
                else:
                    logger.error(f"❌ MP3 playback also failed: {result.stderr}")
                    
            except Exception as e2:
                logger.error(f"❌ All playback methods failed: {e2}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Audio playback timed out")
        except FileNotFoundError:
            logger.error("❌ afplay not found")
            
        finally:
            # Clean up temporary files
            try:
                os.unlink(temp_input.name)
            except:
                pass
            try:
                os.unlink(temp_wav.name)
            except:
                pass
            
    async def run_test(self, test_text: str = "Hello, this is a test of the audio routing system."):
        """Run the complete TTS to BlackHole test"""
        
        print("=" * 60)
        print("🧪 TTS → BlackHole Audio Routing Test")
        print("=" * 60)
        print()
        
        try:
            # Step 1: Generate TTS audio
            print("📝 Step 1: Converting text to speech...")
            audio_data, output_file = await self.generate_test_speech(test_text)
            
            # Show file information
            file_size = os.path.getsize(output_file)
            print(f"   💾 Generated file: {os.path.basename(output_file)}")
            print(f"   📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
            print(f"   🎵 Audio data: {len(audio_data):,} bytes")
            print(f"   ⏱️  Estimated duration: ~{len(audio_data)/32000:.1f} seconds")
            
            # Step 2: Start listening on BlackHole
            print("🎧 Step 2: Starting BlackHole listener...")
            self.start_listening()
            
            # Give listener time to stabilize
            await asyncio.sleep(2)
            
            # Step 3: Play TTS audio
            print("🔊 Step 3: Playing TTS audio...")
            print(f"   Text: '{test_text}'")
            print("   This should route through Multi-Output → BlackHole → AI Agent")
            print()
            
            await self.play_tts_audio(audio_data)
            
            # Step 4: Continue listening for a bit
            print("⏳ Step 4: Continuing to listen for audio detection...")
            await asyncio.sleep(5)
            
            # Step 5: Stop and analyze results
            print("📊 Step 5: Analyzing results...")
            self.stop_listening()
            
            await asyncio.sleep(1)  # Let cleanup finish
            
            # Results
            print("\n" + "=" * 60)
            print("📊 TEST RESULTS:")
            print("=" * 60)
            
            # Show file information
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"  💾 Output file: {os.path.basename(output_file)}")
                print(f"  📁 Full path: {output_file}")
                print(f"  📊 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                print(f"  🎧 You can play this file to hear what was generated")
                print()
            
            if self.detection_results:
                results = self.detection_results
                print(f"  🎵 Total audio chunks: {results['total_chunks']}")
                print(f"  📢 Maximum volume: {results['max_volume']:.3f}")
                print(f"  🗣️  Speech chunks detected: {results['speech_chunks']}")
                
                # Calculate detection percentage
                detection_rate = (results['speech_chunks'] / results['total_chunks']) * 100 if results['total_chunks'] > 0 else 0
                print(f"  📈 Speech detection rate: {detection_rate:.1f}%")
                print()
                
                if results['speech_chunks'] > 0:
                    print("✅ SUCCESS! TTS audio was detected on BlackHole")
                    print("   → Audio routing is working correctly")
                    print("   → AI Agent should be able to hear meeting audio")
                    print(f"   → Detected speech in {results['speech_chunks']} out of {results['total_chunks']} chunks")
                elif results['max_volume'] > 0.01:
                    print("⚠️  PARTIAL SUCCESS: Audio detected but no speech recognition")
                    print("   → Audio is routing but may need VAD tuning")
                    print("   → Check TTS audio quality and VAD settings")
                else:
                    print("❌ FAILURE: No audio detected on BlackHole")
                    print("   → Multi-Output Device may not include BlackHole 2ch")
                    print("   → Check Audio MIDI Setup configuration")
            else:
                print("❌ ERROR: No detection results available")
                
        except Exception as e:
            logger.error(f"❌ Test failed with error: {e}")
            self.stop_listening()
            
        print("\n" + "=" * 60)
        print("🔧 NEXT STEPS:")
        print("   📁 Generated audio file saved for inspection")
        print(f"   🎧 Play the file: afplay {os.path.basename(output_file) if 'output_file' in locals() else 'test_tts_output_*.wav'}")
        print("   🔍 Check the file to verify TTS quality")
        print()
        print("🔧 TROUBLESHOOTING (if test failed):")
        print("   1. Open Audio MIDI Setup")
        print("   2. Ensure Multi-Output Device includes BlackHole 2ch")
        print("   3. Set Multi-Output Device as default output")
        print("   4. Test with: python scripts/test_tts_to_blackhole.py")
        print("=" * 60)

async def main():
    """Main test function"""
    
    print("🚀 Initializing TTS → BlackHole Test...")
    
    # Check if test text provided
    test_text = "Hello everyone, this is a test of the audio routing system from text to speech to BlackHole detection."
    
    if len(sys.argv) > 1:
        test_text = " ".join(sys.argv[1:])
        
    print(f"📝 Test text: '{test_text}'")
    print()
    
    # Run the test
    test = TTSToBlackHoleTest()
    await test.run_test(test_text)

if __name__ == "__main__":
    asyncio.run(main()) 