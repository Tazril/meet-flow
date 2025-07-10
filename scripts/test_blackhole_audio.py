#!/usr/bin/env python3
"""
Simple BlackHole Audio Test

This script tests if BlackHole is receiving audio from your system.
Run this while playing audio (YouTube, music, etc.) to verify setup.
"""

import sys
import time
import numpy as np
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

try:
    from src.audio.capture import AudioCapture
    from src.utils.config import Config
    from src.utils.logger import setup_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = setup_logger(__name__)

def test_blackhole_audio():
    """Test if BlackHole is receiving audio."""
    print("🧪 SIMPLE BLACKHOLE AUDIO TEST")
    print("=" * 50)
    print("This test checks if BlackHole is receiving audio from your system")
    print("")
    print("SETUP:")
    print("1. Make sure Multi-Output Device is configured with:")
    print("   - Built-in Output (checked)")
    print("   - BlackHole 2ch (checked and set as MASTER)")
    print("2. System Preferences → Sound → Output: Multi-Output Device")
    print("3. System Preferences → Sound → Input: BlackHole 2ch")
    print("4. Play some audio (YouTube, music, etc.)")
    print("")
    
    input("Press Enter when audio is playing to start the test...")
    
    try:
        # Initialize audio capture
        print(f"🎤 Initializing audio capture from: {Config.AUDIO_DEVICE_INPUT}")
        capture = AudioCapture(
            device=Config.AUDIO_DEVICE_INPUT,
            sample_rate=Config.SAMPLE_RATE
        )
        
        # Start recording
        if not capture.start_recording():
            print("❌ Failed to start audio recording")
            return False
        
        print("🔴 Recording for 3 seconds...")
        
        # Collect audio chunks
        chunks = []
        start_time = time.time()
        
        while time.time() - start_time < 3.0:
            chunk = capture.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                chunks.append(chunk)
            time.sleep(0.01)
        
        # Stop recording
        capture.stop_recording()
        
        if not chunks:
            print("❌ No audio chunks captured")
            print("💡 Possible issues:")
            print("   - BlackHole not set as input device")
            print("   - Multi-Output Device not configured")
            print("   - No audio playing")
            return False
        
        # Analyze audio
        audio_data = np.concatenate(chunks)
        duration = len(audio_data) / Config.SAMPLE_RATE
        max_amplitude = np.max(np.abs(audio_data))
        rms_amplitude = np.sqrt(np.mean(audio_data.astype(float) ** 2))
        
        print(f"📊 RESULTS:")
        print(f"   Duration: {duration:.2f} seconds")
        print(f"   Samples: {len(audio_data)}")
        print(f"   Max amplitude: {max_amplitude:.6f}")
        print(f"   RMS amplitude: {rms_amplitude:.6f}")
        
        # Determine success
        if max_amplitude > 0.001:
            print("\n✅ SUCCESS! BlackHole is receiving audio!")
            print("🚀 Your audio routing is working correctly.")
            print("   The AI agent should be able to hear Google Meet audio.")
            
            # Save sample for verification
            timestamp = int(time.time())
            filename = f"blackhole_test_{timestamp}.wav"
            save_audio_to_file(audio_data, filename)
            print(f"💾 Audio sample saved as: {filename}")
            
            return True
        else:
            print("\n❌ FAILURE! BlackHole is not receiving audio.")
            print("💡 Troubleshooting steps:")
            print("   1. Check Multi-Output Device configuration:")
            print("      - Open Audio MIDI Setup")
            print("      - Select Multi-Output Device")
            print("      - Ensure Built-in Output is checked")
            print("      - Ensure BlackHole 2ch is checked AND set as master")
            print("   2. Check System Preferences → Sound:")
            print("      - Output: Multi-Output Device")
            print("      - Input: BlackHole 2ch")
            print("   3. Make sure audio is actually playing")
            print("   4. Try restarting Audio MIDI Setup")
            
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def save_audio_to_file(audio_data: np.ndarray, filename: str):
    """Save audio data to WAV file."""
    try:
        import wave
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(Config.SAMPLE_RATE)
            wav_file.writeframes(audio_data.astype(np.int16).tobytes())
            
    except Exception as e:
        print(f"❌ Failed to save audio file: {e}")

def main():
    """Main function."""
    success = test_blackhole_audio()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 BLACKHOLE AUDIO ROUTING IS WORKING!")
        print("You can now run the main AI agent:")
        print("   python main.py")
    else:
        print("🔧 BLACKHOLE AUDIO ROUTING NEEDS FIXING")
        print("Please follow the troubleshooting steps above.")
        print("Run this test again after making changes.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 