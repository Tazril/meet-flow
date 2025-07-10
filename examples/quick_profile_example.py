#!/usr/bin/env python3
"""Quick example of using Chrome profiles with Google Meet AI Agent."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.browser import MeetingController
from src.utils.config import Config

def main():
    """Quick Chrome profile example."""
    print("🚀 Quick Chrome Profile Example")
    print("=" * 40)
    
    # Show current configuration
    print(f"\n📋 Current Configuration:")
    print(f"  GMEET_URL: {Config.GMEET_URL or '(not set)'}")
    print(f"  CHROME_PROFILE_PATH: {Config.CHROME_PROFILE_PATH}")
    print(f"  USE_CHROME_PROFILE: {Config.USE_CHROME_PROFILE}")
    
    # Example 1: Basic setup with default profile
    print("\n📋 Example 1: Default Profile Setup")
    controller = MeetingController(
        agent_type="gmeet",
        headless=False,  # Profile needs visible browser
        auto_setup_audio=False,  # Skip audio for quick demo
        use_chrome_profile=True  # Use default profile path
    )
    
    print("✅ Controller created with Chrome profile enabled")
    profile_path = getattr(controller.agent, 'chrome_profile_path', '(not available)')
    profile_enabled = getattr(controller.agent, 'use_chrome_profile', False)
    print(f"   Profile path: {profile_path}")
    print(f"   Profile enabled: {profile_enabled}")
    
    controller.close()
    
    # Example 2: Custom profile path
    print("\n📋 Example 2: Custom Profile Path")
    custom_controller = MeetingController(
        agent_type="gmeet",
        headless=False,
        auto_setup_audio=False,
        use_chrome_profile=True,
        chrome_profile_path="my_custom_profile"
    )
    
    print("✅ Controller created with custom profile path")
    custom_path = getattr(custom_controller.agent, 'chrome_profile_path', '(not available)')
    print(f"   Custom path: {custom_path}")
    
    custom_controller.close()
    
    print("\n🎯 Next Steps:")
    print("1. Run: python profile_setup.py")
    print("2. Login to Google in the browser")
    print("3. Use the saved profile for automatic login!")
    
    if Config.GMEET_URL:
        print(f"\n🔗 Your default meeting URL: {Config.GMEET_URL}")
        print("   (Scripts will use this URL as default)")
    else:
        print("\n💡 Tip: Set GMEET_URL in your .env file for convenience:")
        print("   GMEET_URL=https://meet.google.com/your-meeting-id")
    
    print("\n💡 Benefits:")
    print("• No manual login required")
    print("• Faster meeting joins")
    print("• Persistent browser preferences")
    print("• Secure credential storage")
    print("• Default URL from .env configuration")

if __name__ == "__main__":
    main() 