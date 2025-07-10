# #!/usr/bin/env python3
# """
# Comprehensive AI Integration Test

# This test validates the complete AI pipeline integration:
# - Azure OpenAI Whisper, GPT, and TTS
# - Conversation management
# - Audio processing integration
# - Error handling and edge cases
# """

# import sys
# import unittest
# import tempfile
# import numpy as np
# from pathlib import Path

# # Add src directory to path
# sys.path.append(str(Path(__file__).parent.parent / "src"))

# from src.ai import WhisperClient, GPTClient, TTSClient, ConversationManager
# from src.ai.conversation_manager import ConversationContext
# from src.utils.config import Config
# from src.utils.logger import setup_logger

# logger = setup_logger("ai_integration_test")

# class TestAIIntegration(unittest.TestCase):
#     """Test suite for AI integration components."""
    
#     @classmethod
#     def setUpClass(cls):
#         """Set up test class."""
#         logger.info("Setting up AI integration tests...")
        
#         # Check if Azure OpenAI is configured
#         if not Config.validate_azure_config():
#             raise unittest.SkipTest("Azure OpenAI not configured - skipping AI tests")
    
#     def setUp(self):
#         """Set up each test."""
#         pass
    
#     def test_whisper_client_basic(self):
#         """Test basic Whisper client functionality."""
#         logger.info("Testing Whisper client...")
        
#         whisper = WhisperClient()
        
#         # Test connection
#         self.assertTrue(whisper.test_connection(), "Whisper connection failed")
        
#         # Test supported languages
#         languages = whisper.get_supported_languages()
#         self.assertIsInstance(languages, list)
#         self.assertIn("en", languages)
        
#         # Test audio transcription with silence
#         sample_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
#         result = whisper.transcribe_audio_data(sample_audio)
        
#         self.assertIsInstance(result, dict)
#         self.assertIn("text", result)
    
#     def test_gpt_client_basic(self):
#         """Test basic GPT client functionality."""
#         logger.info("Testing GPT client...")
        
#         gpt = GPTClient()
        
#         # Test connection
#         self.assertTrue(gpt.test_connection(), "GPT connection failed")
        
#         # Test response generation
#         response = gpt.generate_response("Say hello in one word.")
#         self.assertIsInstance(response, str)
#         if response is not None:
#             self.assertGreater(len(response), 0)
        
#         # Test intent analysis
#         intent = gpt.analyze_conversation_intent("Can you help me?")
#         self.assertIsInstance(intent, dict)
#         self.assertIn("intent", intent)
        
#         # Test response decision
#         should_respond = gpt.should_respond("AI Assistant, are you there?", context={"agent_name": "AI Assistant"})
#         self.assertTrue(should_respond)
        
#         should_not_respond = gpt.should_respond("I'm working on something.", context={"agent_name": "AI Assistant"})
#         # This might be True or False depending on the model's analysis
#         self.assertIsInstance(should_not_respond, bool)
    
#     def test_tts_client_basic(self):
#         """Test basic TTS client functionality."""
#         logger.info("Testing TTS client...")
        
#         tts = TTSClient()
        
#         # Test connection
#         self.assertTrue(tts.test_connection(), "TTS connection failed")
        
#         # Test available voices
#         voices = tts.get_available_voices()
#         self.assertIsInstance(voices, list)
#         self.assertGreater(len(voices), 0)
        
#         # Test text synthesis
#         test_text = "Hello, this is a test."
#         audio_file = tts.synthesize_text(test_text)
        
#         if audio_file:  # TTS might work but file creation might fail
#             self.assertTrue(Path(audio_file).exists())
        
#         # Test duration estimation
#         duration = tts.get_speech_duration_estimate(test_text)
#         self.assertIsInstance(duration, float)
#         self.assertGreater(duration, 0)
        
#         # Test text splitting
#         long_text = "This is a long text. " * 100
#         chunks = tts.split_text_for_synthesis(long_text, max_length=100)
#         self.assertIsInstance(chunks, list)
#         self.assertGreater(len(chunks), 1)
    
#     def test_conversation_manager_basic(self):
#         """Test basic conversation manager functionality."""
#         logger.info("Testing conversation manager...")
        
#         conv_manager = ConversationManager()
        
#         # Test component connectivity
#         results = conv_manager.test_all_components()
#         self.assertIsInstance(results, dict)
#         self.assertIn("whisper", results)
#         self.assertIn("gpt", results)
#         self.assertIn("tts", results)
        
#         # Test conversation lifecycle
#         context = ConversationContext(
#             meeting_title="Test Meeting",
#             participants=["Tester", "AI Assistant"],
#             agent_name="AI Assistant"
#         )
        
#         conv_manager.start_conversation(context)
#         self.assertTrue(conv_manager.is_conversation_active())
        
#         # Test text input processing
#         audio_file = conv_manager.process_text_input("Hello, can you introduce yourself?")
#         # Audio file might be None if response is not generated
        
#         # Check conversation history
#         summary = conv_manager.get_conversation_summary()
#         self.assertIsInstance(summary, dict)
#         self.assertIn("user_messages", summary)
#         self.assertIn("assistant_messages", summary)
#         self.assertGreater(summary["user_messages"], 0)
        
#         conv_manager.stop_conversation()
#         self.assertFalse(conv_manager.is_conversation_active())
    
#     def test_conversation_manager_audio(self):
#         """Test conversation manager with audio input."""
#         logger.info("Testing conversation manager with audio...")
        
#         conv_manager = ConversationManager()
        
#         context = ConversationContext(
#             meeting_title="Audio Test",
#             participants=["Tester", "AI Assistant"],
#             agent_name="AI Assistant"
#         )
        
#         conv_manager.start_conversation(context)
        
#         # Test audio input processing with silence
#         sample_audio = np.zeros(16000, dtype=np.int16)  # 1 second of silence
#         audio_file = conv_manager.process_audio_input(sample_audio)
        
#         # Should return None for silence
#         self.assertIsNone(audio_file)
        
#         conv_manager.stop_conversation()
    
#     def test_conversation_context_management(self):
#         """Test conversation context management."""
#         logger.info("Testing conversation context management...")
        
#         conv_manager = ConversationManager()
        
#         # Test context updates
#         conv_manager.update_context(
#             meeting_title="Updated Meeting",
#             participants=["Alice", "Bob", "Charlie"],
#             meeting_duration="30 minutes"
#         )
        
#         self.assertEqual(conv_manager.context.meeting_title, "Updated Meeting")
#         self.assertEqual(len(conv_manager.context.participants), 3)
#         self.assertEqual(conv_manager.context.meeting_duration, "30 minutes")
        
#         # Test agent name setting
#         conv_manager.set_agent_name("Test Assistant")
#         self.assertEqual(conv_manager.context.agent_name, "Test Assistant")
    
#     def test_error_handling(self):
#         """Test error handling in AI components."""
#         logger.info("Testing error handling...")
        
#         # Test with invalid configuration
#         try:
#             invalid_whisper = WhisperClient(
#                 azure_endpoint="invalid_endpoint",
#                 api_key="invalid_key"
#             )
#             # Connection should fail gracefully
#             result = invalid_whisper.test_connection()
#             self.assertFalse(result)
#         except Exception:
#             # Should not raise exception, but return False
#             pass
        
#         # Test empty text handling
#         tts = TTSClient()
#         audio_file = tts.synthesize_text("")
#         self.assertIsNone(audio_file)
        
#         # Test empty audio handling
#         whisper = WhisperClient()
#         empty_audio = np.array([], dtype=np.int16)
#         result = whisper.transcribe_audio_data(empty_audio)
#         self.assertIn("error", result)
    
#     def test_configuration_integration(self):
#         """Test configuration integration."""
#         logger.info("Testing configuration integration...")
        
#         # Test configuration methods
#         whisper_config = Config.get_whisper_config()
#         gpt_config = Config.get_gpt_config()
#         tts_config = Config.get_tts_config()
#         conv_config = Config.get_conversation_config()
        
#         self.assertIsInstance(whisper_config, dict)
#         self.assertIsInstance(gpt_config, dict)
#         self.assertIsInstance(tts_config, dict)
#         self.assertIsInstance(conv_config, dict)
        
#         # Test that clients can be initialized with config
#         whisper = WhisperClient(**whisper_config)
#         gpt = GPTClient(**gpt_config)
#         tts = TTSClient(**tts_config)
        
#         self.assertIsNotNone(whisper)
#         self.assertIsNotNone(gpt)
#         self.assertIsNotNone(tts)
    
#     def test_end_to_end_conversation(self):
#         """Test end-to-end conversation flow."""
#         logger.info("Testing end-to-end conversation flow...")
        
#         conv_manager = ConversationManager()
        
#         # Set up conversation
#         context = ConversationContext(
#             meeting_title="End-to-End Test",
#             participants=["Human", "AI Assistant"],
#             agent_name="AI Assistant"
#         )
        
#         conv_manager.start_conversation(context)
        
#         # Simulate a short conversation
#         messages = [
#             "Hello AI Assistant",
#             "What can you help me with?",
#             "Thank you for the assistance"
#         ]
        
#         response_count = 0
        
#         for message in messages:
#             audio_file = conv_manager.process_text_input(message)
            
#             # Count responses (some might not generate responses)
#             if audio_file:
#                 response_count += 1
#                 self.assertTrue(Path(audio_file).exists())
        
#         # Check final state
#         summary = conv_manager.get_conversation_summary()
#         self.assertEqual(summary["user_messages"], len(messages))
#         self.assertGreaterEqual(summary["assistant_messages"], 0)
        
#         conv_manager.stop_conversation()

# class TestAIIntegrationSkipped(unittest.TestCase):
#     """Tests that are skipped when Azure OpenAI is not configured."""
    
#     @unittest.skipUnless(Config.validate_azure_config(), "Azure OpenAI not configured")
#     def test_all_components_working(self):
#         """Test that all AI components are working together."""
#         logger.info("Testing all components working together...")
        
#         # This test runs only if Azure OpenAI is properly configured
#         conv_manager = ConversationManager()
#         results = conv_manager.test_all_components()
        
#         # All components should be working
#         self.assertTrue(all(results.values()), f"Some components failed: {results}")

# def run_integration_tests():
#     """Run the integration test suite."""
#     print("🧪 RUNNING AI INTEGRATION TESTS")
#     print("=" * 50)
    
#     # Check configuration first
#     if not Config.validate_azure_config():
#         print("⚠️ Azure OpenAI not configured - running limited tests")
#         print("To run full tests, configure Azure OpenAI in .env file")
#     else:
#         print("✅ Azure OpenAI configured - running full test suite")
    
#     # Run tests
#     loader = unittest.TestLoader()
#     suite = unittest.TestSuite()
    
#     # Add test classes
#     suite.addTests(loader.loadTestsFromTestCase(TestAIIntegration))
#     suite.addTests(loader.loadTestsFromTestCase(TestAIIntegrationSkipped))
    
#     # Run with verbose output
#     runner = unittest.TextTestRunner(verbosity=2)
#     result = runner.run(suite)
    
#     # Print summary
#     print("\n" + "=" * 50)
#     if result.wasSuccessful():
#         print("✅ All tests passed!")
#     else:
#         print(f"❌ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
        
#         if result.failures:
#             print("\nFailures:")
#             for test, traceback in result.failures:
#                 print(f"  - {test}: {traceback.split(chr(10))[-2]}")
        
#         if result.errors:
#             print("\nErrors:")
#             for test, traceback in result.errors:
#                 print(f"  - {test}: {traceback.split(chr(10))[-2]}")
    
#     return result.wasSuccessful()

# if __name__ == "__main__":
#     run_integration_tests() 