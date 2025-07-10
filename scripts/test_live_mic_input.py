#!/usr/bin/env python3
"""
Live Microphone Input Test for Google Meet

This test continuously plays audio through BlackHole to test if Google Meet
can detect it as microphone input in real-time.
"""

import asyncio
import sys
import os
import time
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.ai.tts_client import TTSClient
from src.audio.playback import AudioPlayback
from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class LiveMicTest:
    def __init__(self):
        self.config = Config()
        self.tts_client = TTSClient()
        self.audio_playback = AudioPlayback()
        
    async def generate_test_phrases(self):
        """Generate multiple test phrases for continuous testing"""
        phrases = [
            "Testing microphone input, can you hear me?",
            "This is a test of the AI agent microphone",
            "Google Meet should detect this audio",
            "BlackHole audio routing test in progress",
            "AI Assistant speaking through virtual microphone"
        ]
        
        audio_files = []
        print("🎵 Generating test phrases...")
        
        for i, phrase in enumerate(phrases):
            print(f"   Generating phrase {i+1}: '{phrase}'")
            audio_data = await self.tts_client.synthesize_speech(phrase)
            
            # Save to file
            filename = f"test_phrase_{i+1}.wav"
            file_path = self.save_audio_to_file(audio_data, filename)
            audio_files.append(file_path)
            
        print(f"✅ Generated {len(audio_files)} test phrases")
        return audio_files
    
    def save_audio_to_file(self, audio_data: bytes, filename: str) -> str:
        """Save audio data to proper WAV file with correct format conversion"""
        import tempfile
        import subprocess
        
        # Azure TTS returns encoded audio (MP3), not raw PCM
        # We need to properly convert it to WAV format for Google Meet
        
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
            
            print(f"✅ Audio converted using afconvert: {os.path.basename(file_path)}")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ afconvert failed, trying ffmpeg...")
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
                
                print(f"✅ Audio converted using ffmpeg: {os.path.basename(file_path)}")
                
            except (subprocess.CalledProcessError, FileNotFoundError) as e2:
                print(f"❌ Conversion failed, saving as MP3: {e2}")
                # Last resort: save as MP3 directly
                mp3_path = file_path.replace('.wav', '.mp3')
                with open(mp3_path, 'wb') as f:
                    f.write(audio_data)
                file_path = mp3_path
        
        finally:
            # Clean up temporary file
            try:
                os.unlink(temp_input.name)
            except:
                pass
        
        return file_path
    
    def play_audio_continuously(self, audio_files, duration_minutes=5):
        """Play audio files continuously through BlackHole"""
        import subprocess
        
        print(f"🔊 Playing audio continuously for {duration_minutes} minutes...")
        print("   This should appear as microphone input in Google Meet")
        print("   Press Ctrl+C to stop")
        print()
        
        start_time = time.time()
        end_time = start_time + (duration_minutes * 60)
        phrase_index = 0
        
        try:
            while time.time() < end_time:
                current_file = audio_files[phrase_index % len(audio_files)]
                phrase_num = (phrase_index % len(audio_files)) + 1
                
                elapsed = int(time.time() - start_time)
                remaining = int(end_time - time.time())
                
                print(f"🎤 [{elapsed:02d}:{elapsed%60:02d}] Playing phrase {phrase_num} (time remaining: {remaining//60}:{remaining%60:02d})")
                
                # Play using afplay to route through system audio
                subprocess.run(['afplay', current_file], check=True)
                
                phrase_index += 1
                time.sleep(2)  # Pause between phrases
                
        except KeyboardInterrupt:
            print("\n⏹️  Stopped by user")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print("🏁 Test completed")
    
    async def run_live_test(self, duration_minutes=5):
        """Run the live microphone test"""
        
        print("=" * 60)
        print("🎤 Live Microphone Input Test for Google Meet")
        print("=" * 60)
        print()
        print("📋 SETUP CHECKLIST:")
        print("  1. ✅ Open Google Meet in your browser")
        print("  2. ✅ Join a meeting or create a test meeting")
        print("  3. ✅ Check Google Meet microphone settings")
        print("  4. ✅ Ensure microphone is set to 'BlackHole 2ch'")
        print("  5. ✅ Enable microphone in Google Meet")
        print()
        
        # Generate test phrases
        audio_files = await self.generate_test_phrases()
        
        print("🚀 STARTING LIVE TEST:")
        print("   → Audio will play continuously through BlackHole")
        print("   → You should see microphone levels in Google Meet")
        print("   → Other participants should hear the AI voice")
        print()
        
        input("Press Enter when you're ready to start the test...")
        print()
        
        # Play audio continuously
        self.play_audio_continuously(audio_files, duration_minutes)
        
        # Cleanup
        print("\n🧹 Cleaning up test files...")
        for file_path in audio_files:
            try:
                os.remove(file_path)
                print(f"   Deleted: {os.path.basename(file_path)}")
            except:
                pass
        
        print()
        print("=" * 60)
        print("🔍 TROUBLESHOOTING:")
        print("   If Google Meet didn't detect audio:")
        print("   1. Check Google Meet microphone dropdown → 'BlackHole 2ch'")
        print("   2. Try refreshing Google Meet page")
        print("   3. Check browser microphone permissions")
        print("   4. Verify Multi-Output Device includes BlackHole 2ch")
        print("=" * 60)

async def main():
    """Main test function"""
    
    print("🚀 Initializing Live Microphone Test...")
    
    # Check duration
    duration = 3  # Default 3 minutes
    if len(sys.argv) > 1:
        try:
            duration = int(sys.argv[1])
        except ValueError:
            print("⚠️  Invalid duration, using 3 minutes")
    
    print(f"⏱️  Test duration: {duration} minutes")
    print()
    
    # Run the test
    test = LiveMicTest()
    await test.run_live_test(duration)

if __name__ == "__main__":
    asyncio.run(main()) 