# 🔐 Chrome Profile Guide for Google Meet AI Agent

## Overview

Chrome profiles allow your Google Meet AI Agent to maintain persistent login sessions, eliminating the need to authenticate with Google every time you start the system. This significantly improves the user experience and reduces setup time.

## 🎯 Benefits

- **🔐 Persistent Google Login** - Stay logged in across sessions
- **⚡ Faster Meeting Joins** - Skip authentication prompts
- **🎛️ Saved Browser Preferences** - Custom settings and shortcuts
- **📊 Meeting History Access** - Previous meetings and contacts
- **🔒 Secure Credential Storage** - Chrome's encrypted credential store
- **🛡️ Isolated Environment** - Separate from your main Chrome profile

## 🚀 Quick Setup

### Step 1: Run Profile Setup
```bash
python profile_setup.py
```

### Step 2: Login to Google
- Chrome will open with a new profile
- Navigate to Google accounts and login
- Your credentials will be automatically saved

### Step 3: Test the Profile
```bash
python quick_profile_example.py
```

### Step 4: Configure Your Agent
```python
from browser import MeetingController

controller = MeetingController(
    agent_type="gmeet",
    headless=False,  # Profile requires visible browser
    use_chrome_profile=True,
    chrome_profile_path="chrome_profile"  # Optional custom path
)
```

## 📋 Configuration Options

### Environment Variables (.env)
```env
# Chrome Profile Settings
CHROME_PROFILE_PATH=chrome_profile     # Profile directory path
USE_CHROME_PROFILE=true               # Enable/disable profiles
CHROME_EXECUTABLE_PATH=               # Optional: custom Chrome path
```

### Code Configuration
```python
# Method 1: Using MeetingController
controller = MeetingController(
    use_chrome_profile=True,
    chrome_profile_path="my_profile"
)

# Method 2: Direct GMeetAgent
from browser import GMeetAgent
agent = GMeetAgent(
    chrome_profile_path="custom_profile",
    use_chrome_profile=True,
    chrome_executable_path="/path/to/chrome"  # Optional
)
```

## 🛠️ Management Tools

### Profile Setup Script
```bash
python profile_setup.py
```
**Features:**
- Create new profiles
- Test existing profiles
- List available profiles
- Interactive setup wizard

### Quick Example Script
```bash
python quick_profile_example.py
```
**Features:**
- Test profile configuration
- Verify setup
- Example usage patterns

### Enhanced Demo
```bash
python browser_demo_with_profile.py
```
**Features:**
- Full meeting automation demo
- Profile vs non-profile comparison
- Interactive testing

## 📁 Profile Structure

```
chrome_profile/                    # Profile directory
├── Default/                      # Chrome user data
│   ├── Cookies                   # Login cookies (encrypted)
│   ├── Preferences              # Browser settings
│   ├── Login Data               # Saved passwords (encrypted)
│   └── ...                      # Other Chrome data
├── Local State                  # Profile metadata
└── ...                         # Additional Chrome files
```

**Typical Size:** 10-50MB depending on usage

## 🔒 Security Features

- **Encryption**: All credentials encrypted by Chrome
- **Isolation**: Profile isolated from system Chrome
- **Permissions**: Minimal required permissions only
- **Cleanup**: Automatic resource cleanup on exit
- **Sandboxing**: Browser runs in sandboxed environment

## 🐛 Troubleshooting

### Profile Not Working
```bash
# Delete and recreate profile
rm -rf chrome_profile
python profile_setup.py
```

### Login Expired
```bash
# Re-run setup to refresh login
python profile_setup.py
```

### Permission Issues
```bash
# Check directory permissions
ls -la chrome_profile
chmod -R 755 chrome_profile
```

### Chrome Version Issues
```bash
# Update Playwright browsers
python -m playwright install chromium
```

### Import Errors
```bash
# Verify Python path
python -c "import sys; sys.path.append('src'); from browser import GMeetAgent"
```

## 💡 Best Practices

### 1. Profile Naming
- Use descriptive names: `gmeet_production`, `testing_profile`
- Avoid spaces and special characters
- Use relative paths for portability

### 2. Security
- Don't share profile directories
- Use separate profiles for different environments
- Regularly update profiles (monthly)

### 3. Performance
- Keep profiles clean and minimal
- Remove unused profiles periodically
- Monitor profile size growth

### 4. Development
- Use separate profiles for testing vs production
- Version control ignore profile directories
- Document profile requirements in README

## 🔄 Profile Lifecycle

```
1. Creation     → profile_setup.py creates directory
2. Authentication → Manual Google login in browser  
3. Storage      → Chrome encrypts and saves credentials
4. Usage        → Automatic login on subsequent runs
5. Maintenance  → Periodic refresh/cleanup
6. Cleanup      → Delete when no longer needed
```

## 📊 Comparison: With vs Without Profiles

| Feature | Without Profile | With Profile |
|---------|----------------|--------------|
| Login Required | Every session | Once only |
| Setup Time | 30-60 seconds | 3-5 seconds |
| User Interaction | Manual auth | Fully automated |
| Meeting History | Not available | Full access |
| Preferences | Reset each time | Persistent |
| Security | Session-based | Encrypted storage |

## 🎯 Use Cases

### Development & Testing
```python
# Testing profile - clean state
test_controller = MeetingController(
    chrome_profile_path="test_profile",
    use_chrome_profile=True
)
```

### Production Deployment
```python
# Production profile - stable login
prod_controller = MeetingController(
    chrome_profile_path="/secure/prod_profile", 
    use_chrome_profile=True
)
```

### Multiple Accounts
```python
# Account A
controller_a = MeetingController(
    chrome_profile_path="account_a_profile"
)

# Account B  
controller_b = MeetingController(
    chrome_profile_path="account_b_profile"
)
```

## 🔧 Advanced Configuration

### Custom Chrome Executable
```python
agent = GMeetAgent(
    chrome_executable_path="/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
    use_chrome_profile=True
)
```

### Profile Migration
```bash
# Copy profile to new location
cp -r old_profile new_profile

# Update configuration
export CHROME_PROFILE_PATH=new_profile
```

### Backup and Restore
```bash
# Backup profile
tar -czf profile_backup.tar.gz chrome_profile/

# Restore profile
tar -xzf profile_backup.tar.gz
```

## 🎮 Integration Examples

### Basic Integration
```python
from browser import MeetingController

# Initialize with profile
controller = MeetingController(use_chrome_profile=True)

# Join meeting (no login required!)
controller.join_meeting("https://meet.google.com/abc-defg-hij", "AI Bot")

# Agent is automatically authenticated
controller.toggle_microphone(True)
controller.send_chat_message("AI agent online")
```

### Error Handling
```python
try:
    controller = MeetingController(use_chrome_profile=True)
    success = controller.join_meeting(url, name)
    
    if not success:
        # Fallback: try without profile
        controller.close()
        controller = MeetingController(use_chrome_profile=False)
        success = controller.join_meeting(url, name)
        
except Exception as e:
    logger.error(f"Profile error: {e}")
    # Handle profile corruption or issues
```

### Configuration Validation
```python
from utils.config import Config
from pathlib import Path

# Check profile configuration
if Config.USE_CHROME_PROFILE:
    profile_path = Path(Config.CHROME_PROFILE_PATH)
    if not profile_path.exists():
        print("❌ Profile not found, run: python profile_setup.py")
    else:
        print(f"✅ Profile ready: {profile_path}")
```

## 📞 Support

If you encounter issues:

1. **Check the logs** - Look for profile-related error messages
2. **Run the test scripts** - Use `profile_setup.py` to diagnose
3. **Verify permissions** - Ensure profile directory is writable
4. **Update browsers** - Run `python -m playwright install`
5. **Clean restart** - Delete profile and recreate if corrupted

## 🔄 Updates and Maintenance

- **Weekly**: Check profile login status
- **Monthly**: Clear profile cache and cookies if needed
- **Quarterly**: Update Chrome and Playwright versions
- **As needed**: Recreate profiles for security or corruption issues

The Chrome profile system significantly enhances the Google Meet AI Agent by providing seamless, persistent authentication and improved user experience. 