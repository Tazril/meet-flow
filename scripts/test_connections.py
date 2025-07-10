#!/usr/bin/env python3
"""Connection test script for Google Meet AI Agent."""

import asyncio
import sys
import os
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from src.utils.config import Config
from src.ai.whisper_client import WhisperClient
from src.ai.gpt_client import GPTClient
from src.ai.tts_client import TTSClient

async def test_whisper_connection():
    """Test Whisper connection and basic functionality."""
    print("\n🎤 Testing Whisper Connection...")
    print("-" * 50)
    
    try:
        # Create Whisper client
        client = WhisperClient()
        
        # Test connection
        success = await client.test_connection()
        
        if success:
            print("✅ Whisper connection successful!")
            
            # Test with a sample audio file (if available)
            print("📝 Testing transcription...")
            
            # Note: This would need an actual audio file to test transcription
            print("ℹ️  Transcription test requires an audio file")
            
        else:
            print("❌ Whisper connection failed!")
            return False
        
        await client.close()
        return success
        
    except Exception as e:
        print(f"❌ Whisper test error: {e}")
        return False

async def test_gpt_connection():
    """Test GPT connection and basic functionality."""
    print("\n🧠 Testing GPT Connection...")
    print("-" * 50)
    
    try:
        # Create GPT client
        client = GPTClient()
        
        # Test connection
        success = await client.test_connection()
        
        if success:
            print("✅ GPT connection successful!")
            
            # Test conversation
            print("💬 Testing conversation...")
            
            conversation = [
                {"role": "user", "content": "Say hello and confirm you're working correctly."}
            ]
            
            response = await client.generate_response_async(conversation)
            if response:
                print(f"🤖 GPT Response: {response}")
                
                # Test response decision making
                should_respond = await client.should_respond_async(
                    "Hello everyone!", 
                    conversation,
                    context={"recent_messages": conversation}
                )
                print(f"🤔 Should respond to greeting: {'Yes' if should_respond else 'No'}")
                
            else:
                print("❌ No response generated")
                return False
                
        else:
            print("❌ GPT connection failed!")
            return False
        
        await client.close()
        return success
        
    except Exception as e:
        print(f"❌ GPT test error: {e}")
        return False

async def test_tts_connection():
    """Test TTS connection and basic functionality."""
    print("\n🗣️ Testing TTS Connection...")
    print("-" * 50)
    
    try:
        # Create TTS client
        client = TTSClient()
        
        # Test connection
        success = await client.test_connection()
        
        if success:
            print("✅ TTS connection successful!")
            
            # Test speech synthesis
            print("🎵 Testing speech synthesis...")
            
            test_text = "Hello, this is a test of the text-to-speech system."
            audio_data = await client.synthesize_speech(test_text)
            
            if audio_data:
                print(f"🎶 Generated {len(audio_data)} bytes of audio")
                
                # Save test audio file
                test_file = "test_tts_output.mp3"
                with open(test_file, "wb") as f:
                    f.write(audio_data)
                print(f"💾 Test audio saved as {test_file}")
                
            else:
                print("❌ No audio generated")
                return False
                
        else:
            print("❌ TTS connection failed!")
            return False
        
        await client.close()
        return success
        
    except Exception as e:
        error_msg = str(e)
        print(f"❌ TTS test error: {e}")
        
        # Provide specific guidance for common errors
        if "Invalid model" in error_msg and "tts" in error_msg:
            print("💡 Fix: Change TTS_MODEL=tts to TTS_MODEL=tts-1 in your .env file")
        
        return False

async def test_full_conversation_pipeline():
    """Test the complete conversation pipeline."""
    print("\n🔄 Testing Full Conversation Pipeline...")
    print("-" * 50)
    
    try:
        # Create all clients
        print("🔧 Initializing clients...")
        gpt_client = GPTClient()
        tts_client = TTSClient()
        
        # Simulate a conversation flow
        print("💭 Simulating conversation flow...")
        
        # 1. Simulate received speech (we'll skip Whisper for this test)
        simulated_speech = "Hello AI assistant, how are you today?"
        print(f"👤 Simulated user input: {simulated_speech}")
        
        # 2. Generate response with GPT
        conversation = [
            {"role": "user", "content": simulated_speech}
        ]
        
        response = await gpt_client.generate_response_async(conversation)
        if not response:
            print("❌ Failed to generate response")
            return False
        
        print(f"🤖 AI Response: {response}")
        
        # 3. Convert response to speech
        audio_data = await tts_client.synthesize_speech(response)
        if not audio_data:
            print("❌ Failed to synthesize speech")
            return False
        
        print(f"🎶 Generated {len(audio_data)} bytes of audio for response")
        
        # Save the complete conversation audio
        pipeline_file = "test_pipeline_output.mp3"
        with open(pipeline_file, "wb") as f:
            f.write(audio_data)
        print(f"💾 Pipeline test audio saved as {pipeline_file}")
        
        print("✅ Full conversation pipeline test successful!")
        
        # Clean up
        await gpt_client.close()
        await tts_client.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Pipeline test error: {e}")
        return False

def print_configuration_info():
    """Print current configuration information."""
    print("\n⚙️ Configuration Information:")
    print("=" * 60)
    
    config = Config()
    
    # Print Azure OpenAI services status
    print("\n🔗 Azure OpenAI Services:")
    
    # Whisper
    if config.WHISPER_ENDPOINT and config.WHISPER_API_KEY:
        print(f"  Whisper: ✅ Configured")
        print(f"    Endpoint: {config.WHISPER_ENDPOINT}")
        print(f"    Deployment: {config.WHISPER_DEPLOYMENT_NAME}")
        print(f"    API Version: {config.WHISPER_API_VERSION}")
    else:
        print(f"  Whisper: ❌ Not configured")
    
    # GPT
    if hasattr(config, 'GPT_ENDPOINT') and config.GPT_ENDPOINT and hasattr(config, 'GPT_API_KEY') and config.GPT_API_KEY:
        print(f"  GPT: ✅ Configured (Azure OpenAI)")
        print(f"    Endpoint: {config.GPT_ENDPOINT}")
        print(f"    Deployment: {config.GPT_DEPLOYMENT_NAME}")
        print(f"    API Version: {config.GPT_API_VERSION}")
    elif config.OPENAI_API_KEY:
        print(f"  GPT: ✅ Configured (OpenAI)")
        print(f"    Model: {config.GPT_DEPLOYMENT_NAME}")
    else:
        print(f"  GPT: ❌ Not configured")
    
    # TTS
    if config.TTS_ENDPOINT and config.TTS_API_KEY:
        print(f"  TTS: ✅ Configured")
        print(f"    Endpoint: {config.TTS_ENDPOINT}")
        print(f"    Model: {config.TTS_MODEL}")
        print(f"    Voice: {config.TTS_VOICE}")
        print(f"    API Version: {config.TTS_API_VERSION}")
    else:
        print(f"  TTS: ❌ Not configured")
    
    print("\n📋 Agent Configuration:")
    print(f"  Agent Name: {config.AGENT_NAME}")
    print(f"  Response Delay: {config.RESPONSE_DELAY}s")
    print(f"  Max Conversation History: {config.MAX_CONVERSATION_HISTORY}")
    
    print("\n🔊 Audio Configuration:")
    print(f"  Sample Rate: {config.SAMPLE_RATE} Hz")
    print(f"  Channels: {config.CHANNELS}")

async def main():
    """Main test function."""
    print("🚀 Google Meet AI Agent - Connection Tests")
    print("=" * 60)
    
    # Print configuration info
    print_configuration_info()
    
    # Run individual tests
    results = {}
    
    # Test Whisper
    results['whisper'] = await test_whisper_connection()
    
    # Test GPT
    results['gpt'] = await test_gpt_connection()
    
    # Test TTS
    results['tts'] = await test_tts_connection()
    
    # Test full pipeline if all individual tests pass
    if all(results.values()):
        results['pipeline'] = await test_full_conversation_pipeline()
    else:
        print("\n⚠️ Skipping pipeline test due to individual test failures")
        results['pipeline'] = False
    
    # Print final results
    print("\n📊 Test Results Summary:")
    print("=" * 60)
    
    for service, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {service.upper()}: {status}")
    
    all_passed = all(results.values())
    print(f"\n🎯 Overall Status: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    
    if not all_passed:
        print("\n💡 Troubleshooting Tips:")
        if not results['whisper']:
            print("  - Check WHISPER_ENDPOINT and WHISPER_API_KEY in .env")
        if not results['gpt']:
            print("  - Check GPT_ENDPOINT and GPT_API_KEY in .env, or OPENAI_API_KEY")
        if not results['tts']:
            print("  - Check TTS_ENDPOINT and TTS_API_KEY in .env")
        print("  - Verify API keys are valid and have necessary permissions")
        print("  - Check network connectivity to Azure endpoints")
    
    # Clean up test files
    for test_file in ["test_tts_output.mp3", "test_pipeline_output.mp3"]:
        if os.path.exists(test_file):
            try:
                os.remove(test_file)
                print(f"🧹 Cleaned up {test_file}")
            except:
                pass
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 