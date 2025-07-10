# #!/usr/bin/env python3
# """Comprehensive test script for browser automation system."""

# import asyncio
# import time
# import sys
# from pathlib import Path

# # Add src to path for imports
# sys.path.append(str(Path(__file__).parent.parent / "src"))

# from src.browser import GMeetAgent, MeetingController, AudioVideoInput, AudioVideoOutput
# from src.utils.config import Config
# from src.utils.logger import setup_logger

# logger = setup_logger("browser_test")

# def test_config_loading():
#     """Test configuration loading."""
#     logger.info("🧪 Testing configuration loading...")
    
#     try:
#         # Print configuration status
#         Config.print_config_status()
        
#         # Validate configuration
#         errors = Config.validate_required_fields()
#         if errors:
#             logger.warning("⚠️  Configuration warnings:")
#             for error in errors:
#                 logger.warning(f"  - {error}")
#         else:
#             logger.info("✅ Configuration validation passed")
        
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ Configuration test failed: {e}")
#         return False

# def test_av_input_output():
#     """Test audio/video input and output systems."""
#     logger.info("🧪 Testing AV Input/Output systems...")
    
#     try:
#         # Test AudioVideoInput
#         logger.info("Testing AudioVideo Input...")
#         av_input = AudioVideoInput()
        
#         input_status = av_input.get_injection_status()
#         logger.info(f"  Input status: {input_status}")
        
#         # Test tone injection
#         logger.info("  Testing test tone injection...")
#         success = av_input.inject_test_tone(frequency=880, duration=1.0)
#         logger.info(f"  Tone injection: {'✅ Success' if success else '❌ Failed'}")
        
#         # Test AudioVideoOutput
#         logger.info("Testing AudioVideo Output...")
#         av_output = AudioVideoOutput()
        
#         output_status = av_output.get_capture_status()
#         logger.info(f"  Output status: {output_status}")
        
#         # Test capture start/stop
#         logger.info("  Testing capture start/stop...")
#         capture_started = av_output.start_audio_capture()
#         logger.info(f"  Capture start: {'✅ Success' if capture_started else '❌ Failed'}")
        
#         time.sleep(1)  # Brief capture
        
#         capture_stopped = av_output.stop_audio_capture()
#         logger.info(f"  Capture stop: {'✅ Success' if capture_stopped else '❌ Failed'}")
        
#         return success and capture_started and capture_stopped
        
#     except Exception as e:
#         logger.error(f"❌ AV Input/Output test failed: {e}")
#         return False

# def test_gmeet_agent_init():
#     """Test GMeet agent initialization without joining a meeting."""
#     logger.info("🧪 Testing GMeet Agent initialization...")
    
#     try:
#         # Test headless mode
#         logger.info("Testing headless initialization...")
#         agent = GMeetAgent(headless=True)
        
#         # Check initial state
#         meeting_info = agent.get_meeting_info()
#         logger.info(f"  Initial state: {meeting_info}")
        
#         # Test status checks
#         in_meeting = agent.is_in_meeting()
#         mic_state = agent.is_microphone_enabled()
#         camera_state = agent.is_camera_enabled()
        
#         logger.info(f"  In meeting: {in_meeting}")
#         logger.info(f"  Mic enabled: {mic_state}")
#         logger.info(f"  Camera enabled: {camera_state}")
        
#         # Clean up
#         agent.close()
#         logger.info("✅ GMeet Agent initialization test passed")
        
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ GMeet Agent test failed: {e}")
#         return False

# def test_meeting_controller():
#     """Test meeting controller without actual meeting."""
#     logger.info("🧪 Testing Meeting Controller...")
    
#     try:
#         # Initialize controller
#         controller = MeetingController(
#             agent_type="gmeet",
#             headless=True,
#             auto_setup_audio=True
#         )
        
#         # Test status
#         status = controller.get_meeting_status()
#         logger.info(f"  Controller status: {status['controller']}")
        
#         # Test audio systems
#         if controller.av_input:
#             logger.info("  AudioVideo Input initialized ✅")
#         else:
#             logger.warning("  AudioVideo Input not initialized ⚠️")
        
#         if controller.av_output:
#             logger.info("  AudioVideo Output initialized ✅")
#         else:
#             logger.warning("  AudioVideo Output not initialized ⚠️")
        
#         # Clean up
#         controller.close()
#         logger.info("✅ Meeting Controller test passed")
        
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ Meeting Controller test failed: {e}")
#         return False

# def test_browser_launch():
#     """Test actual browser launch (non-headless)."""
#     logger.info("🧪 Testing browser launch (visible mode)...")
    
#     try:
#         # Create agent in visible mode
#         agent = GMeetAgent(headless=False)
        
#         logger.info("  Browser launching...")
        
#         # This would normally navigate to a meeting URL
#         # For testing, we'll just verify the browser can be created
#         if hasattr(agent, 'playwright') and agent.playwright is None:
#             logger.info("  Playwright not started yet (expected)")
        
#         # Clean up immediately
#         agent.close()
#         logger.info("✅ Browser launch test passed")
        
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ Browser launch test failed: {e}")
#         return False

# def test_meeting_join_simulation():
#     """Simulate meeting join process (without actual URL)."""
#     logger.info("🧪 Testing meeting join simulation...")
    
#     try:
#         controller = MeetingController(
#             agent_type="gmeet",
#             headless=True,
#             auto_setup_audio=True
#         )
        
#         # Test without URL (should fail gracefully)
#         logger.info("  Testing join without URL (should fail gracefully)...")
#         result = controller.join_meeting(url=None, display_name="Test Agent")
        
#         if not result:
#             logger.info("  ✅ Correctly failed when no URL provided")
#         else:
#             logger.warning("  ⚠️  Unexpectedly succeeded without URL")
        
#         # Test with fake URL (should fail but not crash)
#         logger.info("  Testing join with fake URL (should fail gracefully)...")
#         fake_url = "https://meet.google.com/fake-test-url"
        
#         # This should fail but not crash the system
#         try:
#             result = controller.join_meeting(url=fake_url, display_name="Test Agent")
#             logger.info(f"  Join result: {'Success' if result else 'Failed (expected)'}")
#         except Exception as e:
#             logger.info(f"  Join failed as expected: {e}")
        
#         controller.close()
#         logger.info("✅ Meeting join simulation test passed")
        
#         return True
        
#     except Exception as e:
#         logger.error(f"❌ Meeting join simulation test failed: {e}")
#         return False

# def interactive_browser_test():
#     """Interactive test that requires user input."""
#     logger.info("🧪 Interactive browser test (optional)...")
    
#     try:
#         # Ask user if they want to run interactive test
#         response = input("\n🤖 Run interactive browser test? This will open a visible browser. (y/N): ").strip().lower()
        
#         if response != 'y':
#             logger.info("  Skipping interactive test")
#             return True
        
#         # Check if user has a meeting URL
#         meeting_url = input("Enter Google Meet URL (or press Enter to skip): ").strip()
        
#         if not meeting_url:
#             logger.info("  No URL provided, skipping interactive test")
#             return True
        
#         logger.info("  Opening browser in visible mode...")
#         controller = MeetingController(
#             agent_type="gmeet",
#             headless=False,  # Visible browser
#             auto_setup_audio=True
#         )
        
#         # Attempt to join the meeting
#         logger.info(f"  Attempting to join: {meeting_url}")
#         success = controller.join_meeting(
#             url=meeting_url,
#             display_name="AI Test Agent"
#         )
        
#         if success:
#             logger.info("✅ Successfully joined meeting!")
            
#             # Stay in meeting briefly
#             input("Press Enter to leave meeting...")
            
#             # Test some basic functions
#             logger.info("  Testing microphone toggle...")
#             controller.toggle_microphone(False)  # Mute
#             time.sleep(1)
#             controller.toggle_microphone(True)   # Unmute
            
#             # Leave meeting
#             controller.leave_meeting()
            
#         else:
#             logger.warning("⚠️  Failed to join meeting")
        
#         controller.close()
#         logger.info("✅ Interactive test completed")
        
#         return True
        
#     except KeyboardInterrupt:
#         logger.info("  Interactive test cancelled by user")
#         return True
#     except Exception as e:
#         logger.error(f"❌ Interactive browser test failed: {e}")
#         return False

# def main():
#     """Run all browser automation tests."""
#     logger.info("🚀 Starting browser automation test suite...")
    
#     tests = [
#         ("Configuration Loading", test_config_loading),
#         ("AV Input/Output Systems", test_av_input_output),
#         ("GMeet Agent Initialization", test_gmeet_agent_init),
#         ("Meeting Controller", test_meeting_controller),
#         ("Browser Launch", test_browser_launch),
#         ("Meeting Join Simulation", test_meeting_join_simulation),
#     ]
    
#     results = []
    
#     for test_name, test_func in tests:
#         logger.info(f"\n{'='*60}")
#         logger.info(f"Running: {test_name}")
#         logger.info(f"{'='*60}")
        
#         try:
#             result = test_func()
#             results.append((test_name, result))
            
#             if result:
#                 logger.info(f"✅ {test_name} PASSED")
#             else:
#                 logger.error(f"❌ {test_name} FAILED")
                
#         except Exception as e:
#             logger.error(f"💥 {test_name} CRASHED: {e}")
#             results.append((test_name, False))
    
#     # Run interactive test last
#     logger.info(f"\n{'='*60}")
#     logger.info("Interactive Test (Optional)")
#     logger.info(f"{'='*60}")
#     interactive_result = interactive_browser_test()
#     results.append(("Interactive Browser Test", interactive_result))
    
#     # Print summary
#     logger.info(f"\n{'='*60}")
#     logger.info("TEST SUMMARY")
#     logger.info(f"{'='*60}")
    
#     passed = 0
#     total = len(results)
    
#     for test_name, result in results:
#         status = "✅ PASS" if result else "❌ FAIL"
#         logger.info(f"{status} {test_name}")
#         if result:
#             passed += 1
    
#     logger.info(f"\nResults: {passed}/{total} tests passed")
    
#     if passed == total:
#         logger.info("🎉 All tests passed! Browser automation system is ready.")
#     else:
#         logger.warning(f"⚠️  {total - passed} tests failed. Review issues above.")
    
#     return passed == total

# if __name__ == "__main__":
#     success = main()
#     sys.exit(0 if success else 1) 