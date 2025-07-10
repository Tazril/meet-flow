#!/usr/bin/env python3
"""Test script to verify Google Meet audio routing through BlackHole."""

import sys
import time
import numpy as np
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.audio.capture import AudioCapture
from src.audio.vad import VoiceActivityDetector
from src.utils.logger import setup_logger

logger = setup_logger("meeting_audio_test")

def test_meeting_audio():
    """Test if audio from Google Meet is being captured."""
    print("🎤 Google Meet Audio Routing Test")
    print("=" * 50)
    print()
    print("📋 SETUP CHECKLIST:")
    print("  1. ✅ Multi-Output Device created in Audio MIDI Setup")
    print("  2. ✅ Multi-Output Device set as default output")  
    print("  3. ✅ Google Meet speakers set to Multi-Output Device")
    print("  4. ✅ Join a Google Meet or play audio/video")
    print()
    print("🔊 Now playing audio from Google Meet, YouTube, or any app...")
    print("   The agent should detect this audio if routing is correct")
    print()
    
    try:
        # Initialize audio capture
        capture = AudioCapture()
        vad = VoiceActivityDetector()
        
        print(f"📡 Listening on: {capture.device}")
        print(f"🎯 Sample Rate: {capture.sample_rate}Hz")
        print()
        
        # Start capturing
        success = capture.start_recording()
        if not success:
            print("❌ Failed to start audio capture")
            return False
        
        print("🎧 Listening for 30 seconds...")
        print("   Play some audio and see if it's detected below:")
        print()
        
        start_time = time.time()
        speech_events = 0
        max_amplitude = 0
        chunk_count = 0
        
        while time.time() - start_time < 30.0:
            chunk = capture.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                chunk_count += 1
                amplitude = np.max(np.abs(chunk))
                max_amplitude = max(max_amplitude, amplitude)
                
                # Check for speech/audio activity
                is_speaking, speech_started, speech_ended = vad.update_speech_state(chunk)
                
                if speech_started:
                    speech_events += 1
                    print(f"  🗣️  Audio detected! (Event #{speech_events})")
                
                # Real-time volume meter
                bars = "█" * int(amplitude * 30)
                elapsed = time.time() - start_time
                status = "🗣️ AUDIO" if is_speaking else "🤫 Quiet"
                print(f"\r  {status} | Vol: [{bars:<30}] {amplitude:.3f} | {elapsed:.1f}s", 
                      end="", flush=True)
        
        print()  # New line
        capture.stop_recording()
        
        # Results
        print("\n" + "=" * 50)
        print("📊 TEST RESULTS:")
        print(f"  🎵 Total chunks: {chunk_count}")
        print(f"  📢 Max volume: {max_amplitude:.3f}")
        print(f"  🗣️  Audio events: {speech_events}")
        
        if speech_events > 0:
            print("\n✅ SUCCESS! Audio routing is working correctly!")
            print("   The agent can hear audio from your applications.")
            print("   🚀 Your Google Meet AI Agent should work now!")
            return True
        elif max_amplitude > 0.01:
            print("\n⚠️  PARTIAL SUCCESS: Audio detected but no speech events")
            print("   Try adjusting VAD sensitivity or play louder audio")
            return False
        else:
            print("\n❌ NO AUDIO DETECTED")
            print("   This means audio routing is not working.")
            print("   📋 Check your Multi-Output Device setup!")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        return False

def main():
    """Run the test."""
    success = test_meeting_audio()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 Ready to run: python main.py")
    else:
        print("🔧 Fix audio routing first, then rerun this test")
    print("=" * 50)

if __name__ == "__main__":
    main() 