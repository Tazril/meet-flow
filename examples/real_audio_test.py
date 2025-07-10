#!/usr/bin/env python3
"""
A script for real-world testing of audio capture and playback.

This script allows you to:
1. Record audio from your microphone and save it to a file.
2. Play an audio file through your speakers.

This helps verify that the core audio components are working correctly
with your system's audio devices, including virtual ones like BlackHole.
"""

import sys
import time
from pathlib import Path

# Add the 'src' directory to the Python path to find our modules
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))

try:
    from audio import AudioCapture, AudioPlayback
    from utils import Config, setup_logger
except ImportError as e:
    print(f"Error: Couldn't import modules. Make sure you're running this from the project root.")
    print(f"Details: {e}")
    sys.exit(1)


logger = setup_logger("real_audio_test", "INFO")

def record_audio_to_file(duration: int = 5, filename: str = "test_recording.wav"):
    """Records audio and saves it to a WAV file."""
    logger.info("-" * 50)
    logger.info(f"🎤 Starting a {duration}-second recording...")
    logger.info("   Speak into your microphone now.")
    logger.info("   (Or, if testing BlackHole, play some audio on your Mac)")
    logger.info("-" * 50)

    try:
        # Use AudioCapture as a context manager to handle start/stop
        with AudioCapture() as capture:
            # We get the full buffer after the recording duration
            audio_data = capture.get_audio_buffer(duration)

        if audio_data is not None and audio_data.size > 0:
            saved_file = capture.save_audio_to_wav(audio_data, filename)
            logger.info(f"✅ Audio successfully recorded and saved to: {saved_file}")
            logger.info("   You can now play it back using the 'play' command.")
            return saved_file
        else:
            logger.error("❌ No audio was captured. Is your microphone selected and working?")
            return None
    except Exception as e:
        logger.error(f"❌ An error occurred during recording: {e}", exc_info=True)
        return None


def play_audio_from_file(filename: str):
    """Plays an audio file through the configured playback device."""
    logger.info("-" * 50)
    logger.info(f"🔊 Attempting to play audio from file: {filename}")
    logger.info("-" * 50)
    
    if not Path(filename).exists():
        logger.error(f"❌ File not found: {filename}")
        logger.error("   Please record an audio file first using the 'record' command.")
        return

    try:
        playback = AudioPlayback()
        success = playback.play_audio_file(filename, blocking=True)
        
        if success:
            logger.info("✅ Playback finished successfully.")
        else:
            logger.error("❌ Playback failed. See logs for details.")

    except Exception as e:
        logger.error(f"❌ An error occurred during playback: {e}", exc_info=True)


def main():
    """Main function to handle command-line arguments."""
    if len(sys.argv) < 2:
        print("\nUsage: python real_audio_test.py [record|play]")
        print("  - record: Records 5 seconds of audio to 'test_recording.wav'")
        print("  - play [filename]: Plays an audio file (defaults to 'test_recording.wav')")
        print("\nExample:")
        print("  python real_audio_test.py record")
        print("  python real_audio_test.py play")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "record":
        record_audio_to_file()
    elif command == "play":
        # Use a default filename if one isn't provided
        filename = sys.argv[2] if len(sys.argv) > 2 else "test_recording.wav"
        play_audio_from_file(filename)
    else:
        logger.error(f"Unknown command: '{command}'")
        sys.exit(1)

if __name__ == "__main__":
    main() 