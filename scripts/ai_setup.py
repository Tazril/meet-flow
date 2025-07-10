#!/usr/bin/env python3
"""
Azure OpenAI Setup Script for Google Meet AI Agent

This script helps you set up and test Azure OpenAI integration:
1. Configure environment variables
2. Test connections to all services
3. Validate deployments
4. Run sample AI workflows

Prerequisites:
- Azure OpenAI resource with deployed models
- Appropriate API keys and endpoints
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.utils.config import Config
from src.utils.logger import setup_logger

logger = setup_logger("ai_setup")

def print_banner():
    """Print setup banner."""
    print("\n" + "="*70)
    print("🚀 AZURE OPENAI SETUP FOR GOOGLE MEET AI AGENT")
    print("="*70)
    print("This script will help you configure Azure OpenAI integration.")
    print("Make sure you have:")
    print("• Azure OpenAI resource deployed")
    print("• Whisper, GPT-4o, and TTS models deployed")
    print("• API keys and endpoints ready")
    print("="*70)

def check_env_file():
    """Check if .env file exists and create template if needed."""
    env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists():
        print(f"✅ Found existing .env file: {env_path}")
        return True
    else:
        print(f"⚠️ No .env file found at: {env_path}")
        
        choice = input("Create a new .env file with template? (y/n): ").strip().lower()
        if choice in ['y', 'yes']:
            create_env_template(env_path)
            return True
        else:
            print("❌ Cannot proceed without .env file")
            return False

def create_env_template(env_path):
    """Create .env template file with Azure OpenAI settings."""
    template = """# Google Meet AI Agent Configuration

# Google Meet Settings
GMEET_URL=https://meet.google.com/new
AGENT_NAME=AI Assistant

# Browser Settings
USE_CHROME_PROFILE=true
CHROME_PROFILE_PATH=/Users/$(whoami)/Library/Application Support/Google/Chrome/Default
CHROME_EXECUTABLE_PATH=

# Audio Settings
AUDIO_DEVICE_INPUT=BlackHole 2ch
AUDIO_DEVICE_OUTPUT=BlackHole 2ch
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_SIZE=1024

# Voice Activity Detection
VAD_THRESHOLD=0.5
VAD_MIN_SILENCE_DURATION=1.0
VAD_MIN_SPEECH_DURATION=0.5

# Azure OpenAI Configuration (General - used for GPT)
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-01

# Whisper Configuration (can be separate Azure Cognitive Services)
WHISPER_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
WHISPER_API_KEY=your_whisper_api_key_here
WHISPER_API_VERSION=2024-06-01

# TTS Configuration (can be separate Azure Cognitive Services)
TTS_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
TTS_API_KEY=your_tts_api_key_here
TTS_API_VERSION=2025-03-01-preview

# Model Deployments
WHISPER_DEPLOYMENT_NAME=whisper
GPT_DEPLOYMENT_NAME=gpt-4o
TTS_MODEL=tts

# Whisper Settings
WHISPER_LANGUAGE=en
WHISPER_TEMPERATURE=0.0

# GPT Settings
GPT_MAX_TOKENS=1000
GPT_TEMPERATURE=0.7

# TTS Settings
TTS_VOICE=alloy
TTS_SPEED=1.0
TTS_FORMAT=mp3

# Agent Behavior
RESPONSE_DELAY=0.5
MAX_CONVERSATION_HISTORY=50
CONVERSATION_TIMEOUT=300.0
KEEP_MICROPHONE_ON=true

# Logging
LOG_LEVEL=INFO
"""
    
    try:
        with open(env_path, 'w') as f:
            f.write(template)
        print(f"✅ Created .env template at: {env_path}")
        print("\n📝 Please edit the .env file with your Azure OpenAI details:")
        print("  - AZURE_OPENAI_ENDPOINT")
        print("  - AZURE_OPENAI_KEY")
        print("  - Model deployment names")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def interactive_azure_setup():
    """Interactive setup for Azure OpenAI configuration."""
    print("\n🔧 INTERACTIVE AZURE OPENAI SETUP")
    print("-" * 40)
    
    print("This setup supports separate endpoints for different services.")
    print("You can use the same or different Azure resources for each service.\n")
    
    # Get Whisper configuration
    print("🎤 WHISPER CONFIGURATION:")
    whisper_endpoint = input("Whisper Endpoint (e.g., https://your-resource.cognitiveservices.azure.com/): ").strip()
    if not whisper_endpoint:
        print("❌ Whisper endpoint is required")
        return False
    
    whisper_api_key = input("Whisper API Key: ").strip()
    if not whisper_api_key:
        print("❌ Whisper API key is required")
        return False
    
    # Get TTS configuration
    print("\n🔊 TTS CONFIGURATION:")
    use_same_as_whisper = input("Use same endpoint as Whisper? (y/n) [n]: ").strip().lower()
    
    if use_same_as_whisper == 'y':
        tts_endpoint = whisper_endpoint
        tts_api_key = whisper_api_key
    else:
        tts_endpoint = input("TTS Endpoint (e.g., https://your-resource.cognitiveservices.azure.com/): ").strip()
        if not tts_endpoint:
            print("❌ TTS endpoint is required")
            return False
        
        tts_api_key = input("TTS API Key: ").strip()
        if not tts_api_key:
            print("❌ TTS API key is required")
            return False
    
    # Get GPT configuration
    print("\n🤖 GPT CONFIGURATION:")
    gpt_endpoint = input("GPT Endpoint (e.g., https://your-resource.openai.azure.com/) [same as Whisper]: ").strip()
    if not gpt_endpoint:
        gpt_endpoint = whisper_endpoint
    
    gpt_api_key = input("GPT API Key [same as Whisper]: ").strip()
    if not gpt_api_key:
        gpt_api_key = whisper_api_key
    
    # Model deployments
    print("\nModel deployments (press Enter for defaults):")
    whisper_deployment = input("Whisper deployment name [whisper]: ").strip() or "whisper"
    gpt_deployment = input("GPT deployment name [gpt-4o]: ").strip() or "gpt-4o"
    
    # TTS settings
    print("\nTTS configuration:")
    voices = ["alloy", "echo", "fable", "onyx", "nova", "shimmer"]
    print(f"Available voices: {', '.join(voices)}")
    tts_voice = input("TTS voice [alloy]: ").strip() or "alloy"
    
    if tts_voice not in voices:
        print(f"⚠️ Warning: '{tts_voice}' is not a standard voice")
    
    # Agent settings
    agent_name = input("Agent name [AI Assistant]: ").strip() or "AI Assistant"
    
    # Update .env file
    env_path = Path(__file__).parent.parent / ".env"
    
    try:
        # Read existing .env
        if env_path.exists():
            with open(env_path, 'r') as f:
                content = f.read()
        else:
            content = ""
        
        # Update values
        updates = {
            # Whisper configuration
            "WHISPER_ENDPOINT": whisper_endpoint,
            "WHISPER_API_KEY": whisper_api_key,
            "WHISPER_DEPLOYMENT_NAME": whisper_deployment,
            # TTS configuration
            "TTS_ENDPOINT": tts_endpoint,
            "TTS_API_KEY": tts_api_key,
            "TTS_VOICE": tts_voice,
            # GPT configuration
            "AZURE_OPENAI_ENDPOINT": gpt_endpoint,
            "AZURE_OPENAI_KEY": gpt_api_key,
            "GPT_DEPLOYMENT_NAME": gpt_deployment,
            # Agent configuration
            "AGENT_NAME": agent_name
        }
        
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            updated = False
            for key, value in updates.items():
                if line.startswith(f"{key}="):
                    updated_lines.append(f"{key}={value}")
                    updated = True
                    break
            if not updated:
                updated_lines.append(line)
        
        # Add missing variables
        existing_keys = {line.split('=')[0] for line in lines if '=' in line}
        for key, value in updates.items():
            if key not in existing_keys:
                updated_lines.append(f"{key}={value}")
        
        # Write updated .env
        with open(env_path, 'w') as f:
            f.write('\n'.join(updated_lines))
        
        print(f"✅ Updated configuration in {env_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update .env file: {e}")
        return False

def test_azure_connections():
    """Test connections to all Azure OpenAI services."""
    print("\n🧪 TESTING AZURE OPENAI CONNECTIONS")
    print("-" * 40)
    
    # Reload configuration
    from importlib import reload
    from src.utils import config
    reload(config)
    
    # Test configuration validity
    if not Config.validate():
        print("❌ Azure OpenAI configuration invalid")
        return False
    
    print("✅ Configuration valid")
    
    # Test individual components
    try:
        from src.ai import WhisperClient, GPTClient, TTSClient
        
        # Test Whisper
        print("\n1. Testing Whisper connection...")
        whisper = WhisperClient()
        if whisper.test_connection():
            print("✅ Whisper connection successful")
        else:
            print("❌ Whisper connection failed")
            return False
        
        # Test GPT
        print("\n2. Testing GPT connection...")
        gpt = GPTClient()
        if gpt.test_connection():
            print("✅ GPT connection successful")
        else:
            print("❌ GPT connection failed")
            return False
        
        # Test TTS
        print("\n3. Testing TTS connection...")
        tts = TTSClient()
        if tts.test_connection():
            print("✅ TTS connection successful")
        else:
            print("❌ TTS connection failed")
            return False
        
        print("\n🎉 All Azure OpenAI connections successful!")
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False

async def run_sample_workflow():
    """Run a sample AI workflow to demonstrate functionality."""
    print("\n🤖 RUNNING SAMPLE AI WORKFLOW")
    print("-" * 40)
    
    try:
        from src.ai import ConversationManager
        from src.ai.conversation_manager import ConversationContext
        
        # Initialize conversation manager
        print("Initializing conversation manager...")
        conv_manager = ConversationManager()
        
        # Test all components
        results = await conv_manager.test_all_components()
        if not all(results.values()):
            print(f"❌ Component test failed: {results}")
            return False
        
        # Set up context
        context = ConversationContext(
            meeting_title="Azure OpenAI Setup Test",
            participants=["Setup User", Config.AGENT_NAME],
            agent_name=Config.AGENT_NAME
        )
        
        # Start conversation
        conv_manager.start_conversation(context)
        
        # Sample workflow
        test_messages = [
            "Hello, can you introduce yourself?",
            "What are your capabilities?",
            "How can you help in meetings?"
        ]
        
        print("Running sample conversation...")
        for i, message in enumerate(test_messages, 1):
            print(f"\n[{i}] User: {message}")
            
            # Process message
            audio_file = conv_manager.process_text_input(message)
            
            # Get AI response
            for msg in reversed(conv_manager.conversation_history):
                if msg.role == "assistant":
                    print(f"[{i}] AI: {msg.content}")
                    break
            
            if audio_file:
                print(f"[{i}] Audio: {audio_file}")
        
        # Get summary
        summary = conv_manager.get_conversation_summary()
        print(f"\n📊 Workflow Summary:")
        print(f"  Messages: {summary['user_messages']} user, {summary['assistant_messages']} AI")
        print(f"  Duration: {summary.get('session_duration', 0):.1f}s")
        
        conv_manager.stop_conversation()
        print("✅ Sample workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Sample workflow failed: {e}")
        return False

def show_deployment_guide():
    """Show guide for Azure OpenAI model deployments."""
    print("\n📚 AZURE OPENAI DEPLOYMENT GUIDE")
    print("-" * 40)
    print("""
To use this AI agent, you need the following models deployed in Azure OpenAI:

1. WHISPER MODEL
   - Model: whisper
   - Deployment name: whisper (or custom name)
   - Used for: Speech-to-text transcription

2. GPT MODEL  
   - Model: gpt-4o (recommended) or gpt-4
   - Deployment name: gpt-4o (or custom name)
   - Used for: Conversation and response generation

3. TTS MODEL
   - Model: tts-1 or tts-1-hd
   - No deployment needed (use model name directly)
   - Used for: Text-to-speech synthesis

SETUP STEPS:
1. Go to Azure OpenAI Studio
2. Create deployments for Whisper and GPT models
3. Note the deployment names and endpoint
4. Generate API keys
5. Update your .env file with the details

CURRENT CONFIGURATION:
""")
    Config.print_status()

def main():
    """Main setup function."""
    print_banner()
    
    # Check environment
    if not check_env_file():
        return
    
    # Main setup menu
    while True:
        print("\n🔧 SETUP MENU")
        print("-" * 20)
        print("1. Show current configuration")
        print("2. Interactive Azure OpenAI setup")
        print("3. Test Azure connections")
        print("4. Run sample AI workflow")
        print("5. Show deployment guide")
        print("6. Install dependencies")
        print("0. Exit")
        
        choice = input("\nSelect option (0-6): ").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            Config.print_status()
        elif choice == "2":
            interactive_azure_setup()
        elif choice == "3":
            test_azure_connections()
        elif choice == "4":
            asyncio.run(run_sample_workflow())
        elif choice == "5":
            show_deployment_guide()
        elif choice == "6":
            install_dependencies()
        else:
            print("Invalid choice, please try again.")
    
    print("\n👋 Setup completed!")

def install_dependencies():
    """Install required dependencies."""
    print("\n📦 INSTALLING DEPENDENCIES")
    print("-" * 30)
    
    import subprocess
    
    try:
        print("Installing/updating required packages...")
        result = subprocess.run([
            sys.executable, "-m", "pip", "install", "-r", 
            str(Path(__file__).parent.parent / "requirements.txt")
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print(f"❌ Installation failed: {result.stderr}")
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")

if __name__ == "__main__":
    main() 