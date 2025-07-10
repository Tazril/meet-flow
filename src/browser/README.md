# Browser Automation Module

The `browser` module provides a modular, extensible system for automating Google Meet (and potentially other meeting platforms) using Playwright for browser automation and integration with the audio pipeline. **Now includes Chrome profile support for persistent login!**

## Architecture Overview

```
browser/
├── base_interface.py    # Abstract browser automation interface
├── gmeet_agent.py      # Google Meet specific implementation with Chrome profiles
├── actions.py          # High-level meeting controller
├── av_input.py         # Audio/video injection system
├── av_output.py        # Audio/video capture system
└── __init__.py         # Module exports
```

## Key Components

### 1. BrowserAutomationAgent (base_interface.py)
Abstract base class defining the standard interface for browser automation agents. This allows easy extension to other platforms like Zoom, Teams, etc.

**Key Methods:**
- `join_meeting(url, display_name)` - Join a meeting
- `leave_meeting()` - Leave current meeting
- `toggle_microphone(enabled)` - Control microphone
- `toggle_camera(enabled)` - Control camera
- `send_chat_message(message)` - Send chat messages
- `get_meeting_info()` - Get meeting status

### 2. GMeetAgent (gmeet_agent.py)
Google Meet specific implementation using Playwright for DOM automation with **Chrome profile support**.

**Features:**
- Automatic meeting joining with URL detection
- **Persistent Chrome profile for saved login**
- Microphone and camera control
- Chat message sending
- Robust error handling and DOM selector fallbacks
- Support for both headless and visible browser modes
- **Custom Chrome executable path support**

### 3. MeetingController (actions.py)
High-level orchestration layer that combines browser automation with audio I/O.

**Capabilities:**
- Complete meeting lifecycle management
- Integrated audio capture and injection
- Speech detection and audio file management
- Status monitoring and error recovery
- **Chrome profile configuration**

### 4. AudioVideoInput (av_input.py)
Handles audio injection into meetings via BlackHole virtual audio device.

**Methods:**
- `inject_audio_file(file_path)` - Play audio files
- `inject_audio_data(audio_data)` - Play raw audio data
- `inject_tts_text(text)` - Text-to-speech injection
- `inject_test_tone(frequency, duration)` - Test tones

### 5. AudioVideoOutput (av_output.py)
Manages audio capture from meetings with voice activity detection.

**Methods:**
- `start_audio_capture()` - Begin capturing audio
- `capture_speech_segment()` - Capture speech with VAD
- `save_captured_audio()` - Save audio to files
- `get_vad_stats()` - Voice activity statistics

## 🆕 Chrome Profile Support

### Benefits
- **🔐 Persistent Google login** - No need to authenticate every time
- **⚡ Faster meeting joins** - Skip login prompts and verification
- **🎛️ Saved preferences** - Browser settings, extensions, and shortcuts
- **📊 Meeting history** - Access to previous meetings and contacts
- **🔒 Secure storage** - Credentials managed by Chrome's secure storage

### Setup Process

1. **Run the profile setup script:**
```bash
python profile_setup.py
```

2. **Login to Google** in the browser that opens

3. **Your session is automatically saved** for future use

4. **Update your configuration** (optional):
```env
CHROME_PROFILE_PATH=my_custom_profile
USE_CHROME_PROFILE=true
```

## Usage Examples

### Basic Meeting Join with Profile
```python
from browser import MeetingController

# Initialize with Chrome profile
controller = MeetingController(
    agent_type="gmeet",
    headless=False,  # Profile requires visible browser
    auto_setup_audio=True,
    use_chrome_profile=True,
    chrome_profile_path="chrome_profile"
)

# Join meeting - should be automatically logged in!
success = controller.join_meeting(
    url="https://meet.google.com/abc-defg-hij",
    display_name="AI Assistant"
)

# Use meeting features
controller.toggle_microphone(False)  # Mute
controller.send_chat_message("Hello from AI!")
controller.leave_meeting()
controller.close()
```

### Direct Agent Control with Profile
```python
from browser import GMeetAgent

# Create agent with profile
agent = GMeetAgent(
    headless=False,
    chrome_profile_path="my_profile",
    use_chrome_profile=True
)

# Join and control meeting - no login required!
agent.join_meeting("https://meet.google.com/abc-defg-hij", "AI Bot")
agent.toggle_microphone(True)
agent.send_chat_message("AI agent is now online")

agent.close()
```

### Profile Management
```python
# Setup a new profile
python profile_setup.py

# Test existing profile
from browser import GMeetAgent
agent = GMeetAgent(
    chrome_profile_path="test_profile",
    use_chrome_profile=True
)
# Browser will open with saved login
```

## Configuration

The system uses environment variables for configuration:

```env
# Browser Settings
GMEET_URL=https://meet.google.com/your-meeting-id
AGENT_NAME=AI Assistant
BROWSER_HEADLESS=false
BROWSER_TIMEOUT=30

# Chrome Profile Settings (NEW!)
CHROME_PROFILE_PATH=chrome_profile  # Path to profile directory
USE_CHROME_PROFILE=true             # Enable persistent profiles
CHROME_EXECUTABLE_PATH=             # Optional: custom Chrome path

# Meeting Behavior
AUTO_JOIN_ENABLED=true
AUTO_MUTE_ON_JOIN=true
CAMERA_ENABLED=false
SPEECH_DETECTION_TIMEOUT=3.0
```

## Testing

Run the comprehensive test suite:
```bash
python test_browser_automation.py
```

Run the enhanced demo with profiles:
```bash
python browser_demo_with_profile.py
```

Set up Chrome profiles:
```bash
python profile_setup.py
```

## Dependencies

- `playwright` - Browser automation
- `sounddevice` - Audio I/O
- `numpy` - Audio processing
- `webrtcvad` - Voice activity detection

## Platform Support

Currently supports:
- ✅ Google Meet (with Chrome profiles)
- 🔄 Zoom (planned)
- 🔄 Microsoft Teams (planned)

## Chrome Profile Details

### Profile Storage
- **Default location**: `./chrome_profile/`
- **Contents**: Login cookies, preferences, history, bookmarks
- **Security**: Uses Chrome's built-in encryption
- **Size**: Typically 10-50MB depending on usage

### Profile Lifecycle
1. **Creation**: `profile_setup.py` creates new profile
2. **Authentication**: Manual Google login in browser
3. **Storage**: Chrome saves encrypted credentials
4. **Reuse**: Automatic login on subsequent runs
5. **Updates**: Profile evolves with usage

### Troubleshooting Profiles
- **Profile corruption**: Delete profile directory and re-setup
- **Login expired**: Run profile setup again
- **Permission issues**: Check directory permissions
- **Chrome version conflicts**: Update Playwright browsers

## Integration with Audio Pipeline

The browser automation seamlessly integrates with the existing audio pipeline:

1. **Audio Capture**: Uses BlackHole input device to capture meeting audio
2. **Voice Activity Detection**: Intelligent speech segment detection
3. **Audio Injection**: Routes generated audio through BlackHole output to meeting microphone
4. **File Management**: Automatic saving and loading of audio files

## Error Handling

The system includes robust error handling:
- Graceful fallbacks for DOM selector changes
- Automatic recovery from connection issues
- Profile corruption detection and recovery
- Comprehensive logging for debugging
- Clean resource cleanup on exit

## Extension Points

To add support for new meeting platforms:

1. Create new agent class inheriting from `BrowserAutomationAgent`
2. Implement required abstract methods
3. Add platform-specific DOM selectors and logic
4. Add profile support for the platform
5. Update `MeetingController` to support new agent type

Example:
```python
class ZoomAgent(BrowserAutomationAgent):
    def __init__(self, chrome_profile_path=None, use_chrome_profile=True):
        # Zoom-specific profile setup
        pass
    
    def join_meeting(self, url, display_name=None):
        # Zoom-specific implementation with profile
        pass
```

## Security Considerations

- Browser runs with minimal permissions
- Audio devices are isolated through BlackHole
- Chrome profiles use platform encryption
- No persistent data storage by default (except profiles)
- Optional headless mode for server deployments
- Profile data isolated from system Chrome

## Performance

- Efficient DOM polling with intelligent timeouts
- Optimized audio buffer management
- Minimal resource usage in headless mode
- Parallel audio I/O operations
- Fast meeting joins with saved profiles
- Reduced authentication overhead 