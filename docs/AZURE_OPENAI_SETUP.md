# Azure OpenAI Setup Guide

This guide walks you through setting up Azure OpenAI integration for the Google Meet AI Agent.

## Prerequisites

1. **Azure Subscription** with access to Azure OpenAI services
2. **Azure OpenAI Resource** deployed in a supported region
3. **Model Deployments** for Whisper, GPT-4o, and TTS

## Required Models

### 1. Whisper (Speech-to-Text)
- **Model**: `whisper`
- **Purpose**: Convert speech to text for meeting transcription
- **Deployment**: Required in Azure OpenAI Studio
- **Recommended Name**: `whisper`

### 2. GPT-4o (Conversation AI)
- **Model**: `gpt-4o` (recommended) or `gpt-4`
- **Purpose**: Generate intelligent responses and conversation
- **Deployment**: Required in Azure OpenAI Studio
- **Recommended Name**: `gpt-4o`

### 3. TTS (Text-to-Speech)
- **Model**: `tts-1` or `tts-1-hd`
- **Purpose**: Convert AI responses to speech
- **Deployment**: Not required (use model name directly)
- **Available Voices**: alloy, echo, fable, onyx, nova, shimmer

## Setup Steps

### Step 1: Deploy Azure OpenAI Resource

1. Go to [Azure Portal](https://portal.azure.com)
2. Create a new **Azure OpenAI** resource
3. Choose a supported region (e.g., East US, West Europe)
4. Configure the resource settings
5. Wait for deployment to complete

### Step 2: Deploy Models

1. Go to [Azure OpenAI Studio](https://oai.azure.com)
2. Select your resource
3. Navigate to **Deployments**
4. Create new deployments:

   **Whisper Deployment:**
   - Model: `whisper`
   - Deployment name: `whisper`
   - Version: Latest available

   **GPT Deployment:**
   - Model: `gpt-4o` or `gpt-4`
   - Deployment name: `gpt-4o`
   - Version: Latest available

### Step 3: Get Credentials

1. In Azure OpenAI Studio, go to **Chat playground**
2. Click **View code**
3. Copy the **Endpoint** and **API Key**

### Step 4: Configure Environment

1. Update your `.env` file with the Azure OpenAI details:

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_KEY=your_api_key_here
AZURE_OPENAI_API_VERSION=2024-02-01

# Model Deployments
WHISPER_DEPLOYMENT_NAME=whisper
GPT_DEPLOYMENT_NAME=gpt-4o
TTS_MODEL=tts-1

# Optional: Customize TTS voice
TTS_VOICE=alloy  # Options: alloy, echo, fable, onyx, nova, shimmer
```

### Step 5: Test Configuration

Run the setup script to verify everything works:

```bash
python scripts/ai_setup.py
```

Or test individual components:

```bash
python examples/ai_component_examples.py
```

## Configuration Options

### Whisper Settings
```bash
WHISPER_LANGUAGE=en           # Language code (auto-detect if empty)
WHISPER_TEMPERATURE=0.0       # Transcription randomness (0.0-1.0)
```

### GPT Settings
```bash
GPT_MAX_TOKENS=1000          # Maximum response length
GPT_TEMPERATURE=0.7          # Response creativity (0.0-2.0)
```

### TTS Settings
```bash
TTS_VOICE=alloy              # Voice selection
TTS_SPEED=1.0                # Speech speed (0.25-4.0)
TTS_FORMAT=mp3               # Audio format
```

### Agent Behavior
```bash
AGENT_NAME=AI Assistant      # How the agent identifies itself
RESPONSE_DELAY=0.5           # Delay before responding (seconds)
MAX_CONVERSATION_HISTORY=50  # Messages to remember
CONVERSATION_TIMEOUT=300.0   # Session timeout (seconds)
```

## Testing Your Setup

### 1. Quick Test
```bash
python scripts/ai_setup.py
# Select option 3: Test Azure connections
```

### 2. Component Tests
```bash
python examples/ai_component_examples.py
# Test individual components
```

### 3. Full Demo
```bash
python demos/ai_integration_demo.py
# Complete integration demonstration
```

## Troubleshooting

### Common Issues

**❌ "Azure OpenAI endpoint and API key are required"**
- Verify `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_KEY` in `.env`
- Ensure no extra spaces or quotes in the values

**❌ "Model deployment not found"**
- Check deployment names in Azure OpenAI Studio
- Verify `WHISPER_DEPLOYMENT_NAME` and `GPT_DEPLOYMENT_NAME` match

**❌ "Connection failed"**
- Verify API key is valid and active
- Check if resource is in a supported region
- Ensure quota limits aren't exceeded

**❌ "Rate limit exceeded"**
- Check your Azure OpenAI quota and usage
- Increase the `RESPONSE_DELAY` setting
- Consider upgrading your Azure OpenAI tier

### Verification Steps

1. **Check Resource Status**
   - Ensure Azure OpenAI resource is running
   - Verify models are deployed and online

2. **Test API Access**
   - Use Azure OpenAI Studio playground
   - Verify API keys work in the web interface

3. **Check Network**
   - Ensure no firewall blocking Azure OpenAI endpoints
   - Verify DNS resolution works

## Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files to version control
   - Use environment-specific `.env` files

2. **API Key Management**
   - Rotate API keys regularly
   - Use Azure Key Vault for production deployments
   - Monitor API usage and set alerts

3. **Access Control**
   - Limit Azure OpenAI resource access
   - Use Azure RBAC for fine-grained permissions
   - Enable logging and monitoring

## Performance Optimization

### Response Time
- Use `tts-1` instead of `tts-1-hd` for faster synthesis
- Reduce `GPT_MAX_TOKENS` for quicker responses
- Lower `GPT_TEMPERATURE` for more deterministic responses

### Quality
- Use `tts-1-hd` for higher quality speech
- Increase `GPT_MAX_TOKENS` for more detailed responses
- Tune `WHISPER_TEMPERATURE` for transcription accuracy

### Cost Optimization
- Monitor token usage in Azure portal
- Use shorter conversation history (`MAX_CONVERSATION_HISTORY`)
- Implement response caching for common queries

## Advanced Configuration

### Custom System Prompts
```python
from ai import GPTClient

gpt = GPTClient()
gpt.set_system_prompt("You are a specialized meeting assistant for technical teams...")
```

### Voice Customization
```python
from ai import TTSClient

tts = TTSClient()
tts.set_voice("nova")      # Change voice
tts.set_speed(1.2)         # Increase speed
```

### Context-Aware Transcription
```python
from ai import WhisperClient

whisper = WhisperClient()
result = whisper.transcribe_speech_segment(
    audio_data, 
    context="Previous meeting discussion about project deadlines"
)
```

## Next Steps

After setting up Azure OpenAI:

1. **Test the Integration**: Run demos and examples
2. **Customize Agent Behavior**: Modify prompts and settings
3. **Set Up Audio Routing**: Configure BlackHole for meeting audio
4. **Run Full Agent**: Integrate with browser automation
5. **Monitor Usage**: Track API costs and performance

For complete system integration, see the main [README.md](../README.md). 