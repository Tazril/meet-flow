#!/usr/bin/env python3
"""Audio Diagnostics Script for Google Meet AI Agent

This script helps diagnose and fix audio listening issues by:
1. Checking BlackHole installation and device detection
2. Testing audio input/output routing
3. Verifying Voice Activity Detection
4. Testing audio capture and processing
5. Providing system audio setup guidance
"""

import sys
import time
import numpy as np
import sounddevice as sd
from pathlib import Path
from queue import Queue, Empty
import threading
import os

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.audio.capture import AudioCapture
from src.audio.vad import VoiceActivityDetector

logger = setup_logger("audio_diagnostics")

def print_header(title):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_result(test_name, passed, details=""):
    """Print test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status} {test_name}")
    if details:
        print(f"    {details}")

def check_blackhole_installation():
    """Check if BlackHole is installed and available."""
    print_header("BlackHole Installation Check")
    
    devices = sd.query_devices()
    blackhole_devices = []
    
    print("All Audio Devices:")
    for i, device in enumerate(devices):
        if isinstance(device, dict):
            name = device.get('name', 'Unknown')
            max_in = device.get('max_input_channels', 0)
            max_out = device.get('max_output_channels', 0)
            print(f"  [{i:2d}] {name}")
            print(f"       Input: {max_in} channels, Output: {max_out} channels")
            
            if 'BlackHole' in name:
                blackhole_devices.append({
                    'index': i,
                    'name': name,
                    'input_channels': max_in,
                    'output_channels': max_out
                })
    
    if blackhole_devices:
        print_result("BlackHole Detection", True, f"Found {len(blackhole_devices)} BlackHole device(s)")
        for device in blackhole_devices:
            print(f"    - {device['name']}: {device['input_channels']} in, {device['output_channels']} out")
        return True
    else:
        print_result("BlackHole Detection", False, "No BlackHole devices found")
        print("\n🔧 To install BlackHole:")
        print("  1. Download from: https://existential.audio/blackhole/")
        print("  2. Install the 2ch version")
        print("  3. Restart your computer")
        print("  4. Configure macOS audio routing")
        return False

def check_system_audio_routing():
    """Check macOS audio routing configuration."""
    print_header("macOS Audio Routing Check")
    
    print("Current audio configuration from Config:")
    print(f"  Input Device:  {Config.AUDIO_DEVICE_INPUT}")
    print(f"  Output Device: {Config.AUDIO_DEVICE_OUTPUT}")
    print(f"  Sample Rate:   {Config.SAMPLE_RATE}Hz")
    print(f"  Buffer Size:   {Config.BUFFER_SIZE}")
    
    print("\n🔧 Required macOS Audio Setup:")
    print("  1. Open Audio MIDI Setup (Applications > Utilities)")
    print("  2. Create a Multi-Output Device:")
    print("     - Include your speakers AND BlackHole 2ch")
    print("     - Set as default output device")
    print("  3. Set Google Meet output to this Multi-Output Device")
    print("  4. This allows you to hear AND capture meeting audio")
    
    return True

def test_audio_capture():
    """Test audio capture functionality."""
    print_header("Audio Capture Test")
    
    try:
        # Test with current config
        capture = AudioCapture()
        device_info = capture.get_device_info()
        
        print("Audio Capture Configuration:")
        print(f"  Device: {capture.device}")
        print(f"  Sample Rate: {capture.sample_rate}Hz")
        print(f"  Buffer Size: {capture.buffer_size}")
        
        if device_info:
            print(f"  Device Info: {device_info}")
        
        # Test recording
        print("\n🎤 Testing 5-second audio capture...")
        print("  (Make some noise - speak, clap, play music)")
        
        success = capture.start_recording()
        if not success:
            print_result("Audio Capture Start", False, "Failed to start recording")
            return False
        
        print_result("Audio Capture Start", True)
        
        # Capture for 5 seconds and analyze
        chunks = []
        start_time = time.time()
        max_amplitude = 0
        chunk_count = 0
        
        while time.time() - start_time < 5.0:
            chunk = capture.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                chunks.append(chunk)
                chunk_count += 1
                amplitude = np.max(np.abs(chunk))
                max_amplitude = max(max_amplitude, amplitude)
                
                # Show real-time feedback
                bars = "█" * int(amplitude * 50)
                print(f"\r  Volume: [{bars:<50}] {amplitude:.3f}", end="", flush=True)
        
        print()  # New line after volume meter
        capture.stop_recording()
        
        if chunks:
            total_samples = sum(len(chunk) for chunk in chunks)
            duration = total_samples / capture.sample_rate
            print_result("Audio Data Collection", True, 
                        f"Captured {chunk_count} chunks, {total_samples} samples ({duration:.2f}s)")
            print(f"    Max amplitude: {max_amplitude:.3f}")
            
            # Analyze if we got meaningful audio
            if max_amplitude > 0.001:  # Threshold for detecting audio
                print_result("Audio Signal Detection", True, "Audio signal detected")
                return True
            else:
                print_result("Audio Signal Detection", False, "No significant audio detected")
                print("    💡 This suggests audio routing issues")
                return False
        else:
            print_result("Audio Data Collection", False, "No audio chunks received")
            return False
            
    except Exception as e:
        print_result("Audio Capture Test", False, f"Exception: {e}")
        return False

def test_voice_activity_detection():
    """Test Voice Activity Detection."""
    print_header("Voice Activity Detection Test")
    
    try:
        vad = VoiceActivityDetector()
        
        print("VAD Configuration:")
        print(f"  Sample Rate: {vad.sample_rate}Hz")
        print(f"  Aggressiveness: {vad.aggressiveness}")
        print(f"  Frame Duration: {vad.frame_duration_ms}ms")
        print(f"  Frame Size: {vad.frame_size} samples")
        
        # Test with silence
        silence = np.zeros(int(vad.sample_rate * 1.0))  # 1 second of silence
        is_speech, frame_results = vad.detect_speech(silence)
        print_result("Silence Test", not is_speech, f"Speech detected in silence: {is_speech}")
        
        # Test with synthetic speech-like signal
        t = np.linspace(0, 1, vad.sample_rate)
        # Create a more realistic speech-like signal
        speech_signal = (np.sin(2 * np.pi * 300 * t) + 
                        0.5 * np.sin(2 * np.pi * 800 * t) + 
                        0.3 * np.sin(2 * np.pi * 1200 * t)) * 0.3
        # Add some noise and modulation
        speech_signal += np.random.normal(0, 0.05, len(speech_signal))
        speech_signal *= (1 + 0.3 * np.sin(2 * np.pi * 5 * t))  # Amplitude modulation
        
        is_speech, frame_results = vad.detect_speech(speech_signal)
        speech_frames = sum(frame_results)
        print_result("Synthetic Speech Test", is_speech, 
                    f"{speech_frames}/{len(frame_results)} frames detected as speech")
        
        return True
        
    except Exception as e:
        print_result("VAD Test", False, f"Exception: {e}")
        return False

def test_real_time_detection():
    """Test real-time speech detection with live audio."""
    print_header("Real-Time Speech Detection Test")
    
    try:
        capture = AudioCapture()
        vad = VoiceActivityDetector()
        
        print("🎤 Starting 10-second real-time test...")
        print("  Speak into your microphone to test speech detection")
        print("  Watch for speech detection indicators below")
        
        success = capture.start_recording()
        if not success:
            print_result("Real-Time Test Setup", False, "Failed to start recording")
            return False
        
        start_time = time.time()
        speech_detected_count = 0
        total_chunks = 0
        
        while time.time() - start_time < 10.0:
            chunk = capture.get_audio_chunk(timeout=0.1)
            if chunk is not None:
                total_chunks += 1
                
                # Check for speech
                is_speaking, speech_started, speech_ended = vad.update_speech_state(chunk)
                
                if speech_started:
                    speech_detected_count += 1
                    print(f"\n  🗣️  Speech detected! (#{speech_detected_count})")
                elif speech_ended:
                    print(f"  🤐 Speech ended")
                
                # Show real-time status
                status = "🗣️ SPEAKING" if is_speaking else "🤫 Quiet"
                amplitude = np.max(np.abs(chunk)) if len(chunk) > 0 else 0
                bars = "█" * int(amplitude * 20)
                elapsed = time.time() - start_time
                print(f"\r  {status} | Vol: [{bars:<20}] {amplitude:.3f} | {elapsed:.1f}s", 
                      end="", flush=True)
        
        print()  # New line
        capture.stop_recording()
        
        print_result("Real-Time Detection", speech_detected_count > 0, 
                    f"Detected {speech_detected_count} speech events in {total_chunks} chunks")
        
        return speech_detected_count > 0
        
    except Exception as e:
        print_result("Real-Time Test", False, f"Exception: {e}")
        return False

def provide_setup_guidance():
    """Provide setup guidance based on test results."""
    print_header("Setup Guidance & Troubleshooting")
    
    print("🔧 Complete Google Meet Audio Setup:")
    print()
    print("1. 📥 INSTALL BLACKHOLE:")
    print("   - Download from: https://existential.audio/blackhole/")
    print("   - Install BlackHole 2ch")
    print("   - Restart your Mac")
    print()
    print("2. 🔊 CONFIGURE MACOS AUDIO:")
    print("   - Open 'Audio MIDI Setup' (Applications > Utilities)")
    print("   - Create a 'Multi-Output Device':")
    print("     * Include your speakers/headphones")
    print("     * Include BlackHole 2ch")
    print("     * Set it as your default output device")
    print()
    print("3. 🎬 CONFIGURE GOOGLE MEET:")
    print("   - In Google Meet settings:")
    print("     * Speakers: Multi-Output Device (from step 2)")
    print("     * Microphone: Your regular microphone")
    print("   - This routes meeting audio through BlackHole for capture")
    print()
    print("4. 🤖 CONFIGURE THE AI AGENT:")
    print("   - Audio Input: BlackHole 2ch (to capture meeting audio)")
    print("   - Audio Output: BlackHole 2ch (to inject responses)")
    print("   - The agent listens to meeting participants via BlackHole")
    print()
    print("5. 🔄 AUDIO FLOW:")
    print("   Meeting Participants → Google Meet → Multi-Output → BlackHole → AI Agent")
    print("   AI Agent → BlackHole → Google Meet → Meeting Participants")
    print()
    print("💡 TROUBLESHOOTING TIPS:")
    print("   - Ensure BlackHole shows up in 'Sound' preferences")
    print("   - Test by playing music - you should see volume in BlackHole")
    print("   - Check microphone permissions for Terminal/Cursor")
    print("   - Restart Chrome/Meet after audio changes")

def main():
    """Run comprehensive audio diagnostics."""
    print("🤖 Google Meet AI Agent - Audio Diagnostics")
    print("=" * 60)
    print("This script will diagnose audio listening issues and provide setup guidance.")
    
    # Run all diagnostic tests
    tests = [
        ("BlackHole Installation", check_blackhole_installation),
        ("System Audio Routing", check_system_audio_routing), 
        ("Audio Capture", test_audio_capture),
        ("Voice Activity Detection", test_voice_activity_detection),
        ("Real-Time Detection", test_real_time_detection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print(f"\n⏹️  Test interrupted by user")
            break
        except Exception as e:
            print_result(test_name, False, f"Test crashed: {e}")
            results[test_name] = False
    
    # Show summary
    print_header("Diagnostic Summary")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed < total:
        print(f"\n⚠️  {total - passed} test(s) failed - audio listening may not work correctly")
    else:
        print(f"\n🎉 All tests passed - audio system should work correctly!")
    
    # Always show setup guidance
    provide_setup_guidance()

if __name__ == "__main__":
    main() 