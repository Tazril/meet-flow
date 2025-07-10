#!/usr/bin/env python3
"""
Test Audio Recording Saving

This script tests that audio recordings are properly saved to the recordings directory.
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
    from src.ai.conversation_manager import ConversationManager
    from src.utils.logger import setup_logger
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)

logger = setup_logger(__name__)

def test_audio_saving():
    """Test that audio recordings are saved properly."""
    print("🧪 TESTING AUDIO RECORDING SAVING")
    print("=" * 50)
    print("This test will:")
    print("1. Record 3 seconds of audio from BlackHole")
    print("2. Save it to the recordings directory")
    print("3. Show you where the file is saved")
    print("")
    
    input("Press Enter to start recording (make sure audio is playing)...")
    
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
            return False
        
        # Combine audio data
        audio_data = np.concatenate(chunks)
        
        # Test the conversation manager's save method
        conversation_manager = ConversationManager()
        
        # Manually save using the same method
        timestamp = int(time.time())
        recordings_dir = Path("recordings")
        recordings_dir.mkdir(exist_ok=True)
        
        output_file = recordings_dir / f"test_recording_{timestamp}.wav"
        conversation_manager._save_audio_to_wav(audio_data, Config.SAMPLE_RATE, str(output_file))
        
        # Check if file was created
        if output_file.exists():
            file_size = output_file.stat().st_size
            duration = len(audio_data) / Config.SAMPLE_RATE
            
            print(f"✅ SUCCESS! Audio saved to: {output_file}")
            print(f"📊 File size: {file_size:,} bytes")
            print(f"📊 Duration: {duration:.2f} seconds")
            print(f"📊 Samples: {len(audio_data):,}")
            
            # Show the absolute path for easy access
            abs_path = output_file.resolve()
            print(f"🎵 Full path: {abs_path}")
            print("")
            print("You can now:")
            print(f"  1. Open Finder and go to: {abs_path.parent}")
            print(f"  2. Double-click {output_file.name} to play it")
            print("  3. Check what audio the AI agent is actually hearing")
            
            return True
        else:
            print("❌ Audio file was not created")
            return False
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False

def main():
    """Main function."""
    success = test_audio_saving()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 AUDIO SAVING TEST PASSED!")
        print("The recordings directory is now working correctly.")
        print("When you run the main agent, captured audio will be saved here.")
    else:
        print("🔧 AUDIO SAVING TEST FAILED")
        print("Please check the error messages above.")
    
    print("=" * 50)

if __name__ == "__main__":
    main() 