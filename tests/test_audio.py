# #!/usr/bin/env python3
# """Test script for audio components."""

# import sys
# import time
# import numpy as np
# from pathlib import Path

# # Add src to path
# sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# from src.audio import AudioCapture, AudioPlayback, VoiceActivityDetector
# from src.utils import Config, setup_logger

# logger = setup_logger("test_audio", "INFO")

# def test_configuration():
#     """Test configuration loading."""
#     logger.info("🧪 Testing Configuration...")
    
#     Config.print_config_status()
    
#     if not Config.validate_azure_config():
#         logger.warning("⚠️  Configuration validation failed - some features may not work")
#         return False
    
#     logger.info("✅ Configuration test passed")
#     return True

# def test_audio_devices():
#     """Test audio device detection."""
#     logger.info("🧪 Testing Audio Device Detection...")
    
#     try:
#         import sounddevice as sd
        
#         logger.info("Available audio devices:")
#         devices = sd.query_devices()
        
#         blackhole_input = None
#         blackhole_output = None
        
#         for i, device in enumerate(devices):
#             if isinstance(device, dict):
#                 device_name = device.get('name', 'Unknown')
#                 max_in = device.get('max_input_channels', 0)
#                 max_out = device.get('max_output_channels', 0)
                
#                 logger.info(f"  [{i}] {device_name} - In: {max_in}, Out: {max_out}")
                
#                 if 'BlackHole' in device_name:
#                     if max_in > 0:
#                         blackhole_input = device_name
#                     if max_out > 0:
#                         blackhole_output = device_name
        
#         if blackhole_input and blackhole_output:
#             logger.info(f"✅ BlackHole devices found:")
#             logger.info(f"   Input: {blackhole_input}")
#             logger.info(f"   Output: {blackhole_output}")
#             return True
#         else:
#             logger.warning("⚠️  BlackHole devices not found - tests will use default devices")
#             return False
            
#     except Exception as e:
#         logger.error(f"❌ Audio device test failed: {e}")
#         return False

# def test_vad():
#     """Test Voice Activity Detection."""
#     logger.info("🧪 Testing Voice Activity Detection...")
    
#     try:
#         vad = VoiceActivityDetector()
        
#         # Test with silence (zeros)
#         silence = np.zeros(16000)  # 1 second of silence
#         is_speech, frame_results = vad.detect_speech(silence)
        
#         logger.info(f"Silence test - Speech detected: {is_speech}")
#         if is_speech:
#             logger.warning("⚠️  VAD detected speech in silence - this might be an issue")
        
#         # Test with synthetic speech-like signal
#         t = np.linspace(0, 1, 16000)
#         speech_like = np.sin(2 * np.pi * 300 * t) * np.random.random(16000) * 0.5
#         is_speech, frame_results = vad.detect_speech(speech_like)
        
#         logger.info(f"Speech-like test - Speech detected: {is_speech}")
        
#         # Test state updates
#         vad.reset_state()
#         is_speaking, started, ended = vad.update_speech_state(speech_like)
#         logger.info(f"State update - Speaking: {is_speaking}, Started: {started}, Ended: {ended}")
        
#         logger.info("✅ VAD test completed")
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ VAD test failed: {e}")
#         return False

# def test_audio_playback():
#     """Test audio playback."""
#     logger.info("🧪 Testing Audio Playback...")
    
#     try:
#         playback = AudioPlayback()
        
#         # Test with a simple tone
#         logger.info("Playing test tone...")
#         success = playback.test_playback(frequency=440, duration=2.0)
        
#         if success:
#             logger.info("✅ Audio playback test passed")
#             return True
#         else:
#             logger.error("❌ Audio playback test failed")
#             return False
            
#     except Exception as e:
#         logger.error(f"❌ Audio playback test failed: {e}")
#         return False

# def test_audio_capture():
#     """Test audio capture."""
#     logger.info("🧪 Testing Audio Capture...")
    
#     try:
#         capture = AudioCapture()
        
#         # Test device info
#         info = capture.get_device_info()
#         logger.info(f"Capture device info: {info}")
        
#         # Test recording for a short period
#         logger.info("Starting 3-second audio capture test...")
#         success = capture.start_recording()
        
#         if not success:
#             logger.error("❌ Failed to start recording")
#             return False
        
#         # Capture for 3 seconds
#         time.sleep(3)
        
#         # Get some audio data
#         audio_data = capture.get_audio_buffer(1.0)  # Get 1 second
        
#         capture.stop_recording()
        
#         if audio_data is not None:
#             logger.info(f"✅ Captured {len(audio_data)} samples ({len(audio_data)/capture.sample_rate:.2f}s)")
            
#             # Test VAD on captured audio
#             vad = VoiceActivityDetector()
#             is_speech, _ = vad.detect_speech(audio_data)
#             logger.info(f"Speech detected in captured audio: {is_speech}")
            
#             return True
#         else:
#             logger.error("❌ No audio data captured")
#             return False
            
#     except Exception as e:
#         logger.error(f"❌ Audio capture test failed: {e}")
#         return False

# def main():
#     """Run all tests."""
#     logger.info("🚀 Starting Audio Component Tests")
#     logger.info("=" * 50)
    
#     tests = [
#         ("Configuration", test_configuration),
#         ("Audio Devices", test_audio_devices),
#         ("Voice Activity Detection", test_vad),
#         ("Audio Playback", test_audio_playback),
#         ("Audio Capture", test_audio_capture),
#     ]
    
#     results = {}
    
#     for test_name, test_func in tests:
#         logger.info("")
#         try:
#             result = test_func()
#             results[test_name] = result
#         except Exception as e:
#             logger.error(f"❌ {test_name} test crashed: {e}")
#             results[test_name] = False
    
#     # Summary
#     logger.info("")
#     logger.info("=" * 50)
#     logger.info("🏁 Test Results Summary:")
    
#     passed = 0
#     total = len(tests)
    
#     for test_name, result in results.items():
#         status = "✅ PASS" if result else "❌ FAIL"
#         logger.info(f"   {test_name}: {status}")
#         if result:
#             passed += 1
    
#     logger.info("")
#     logger.info(f"📊 Overall: {passed}/{total} tests passed")
    
#     if passed == total:
#         logger.info("🎉 All tests passed! Audio components are working correctly.")
#         return True
#     else:
#         logger.warning(f"⚠️  {total - passed} test(s) failed. Check the logs above.")
#         return False

# if __name__ == "__main__":
#     success = main()
#     sys.exit(0 if success else 1) 