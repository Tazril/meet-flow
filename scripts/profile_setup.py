#!/usr/bin/env python3
"""Helper script to set up and manage Chrome profiles for Google Meet AI Agent."""

import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from browser import GMeetAgent
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger("profile_setup")

def setup_chrome_profile():
    """Set up a Chrome profile for Google Meet authentication."""
    logger.info("🔧 Chrome Profile Setup for Google Meet AI Agent")
    logger.info("=" * 60)
    
    # Get profile path
    profile_path = input(f"Enter Chrome profile path (default: {Config.CHROME_PROFILE_PATH}): ").strip()
    if not profile_path:
        profile_path = Config.CHROME_PROFILE_PATH
    
    profile_path = Path(profile_path).resolve()
    logger.info(f"📁 Profile will be saved to: {profile_path}")
    
    # Create profile directory
    profile_path.mkdir(parents=True, exist_ok=True)
    
    # Ask for Google Meet URL for testing (default from .env)
    default_url = Config.GMEET_URL or ""
    if default_url:
        test_url = input(f"Enter a Google Meet URL to test login (default: {default_url}): ").strip()
        if not test_url:
            test_url = default_url
    else:
        test_url = input("Enter a Google Meet URL to test login (optional): ").strip()
    
    logger.info("\n🚀 Starting Chrome with profile...")
    logger.info("INSTRUCTIONS:")
    logger.info("1. Chrome will open with a persistent profile")
    logger.info("2. Log into your Google account")
    logger.info("3. If you provided a Meet URL, join the meeting to test")
    logger.info("4. Close the browser when done - your login will be saved")
    logger.info("5. Press Enter here when ready to continue...")
    
    try:
        # Initialize agent with profile
        agent = GMeetAgent(
            headless=False,  # Must be visible for login
            chrome_profile_path=str(profile_path),
            use_chrome_profile=True
        )
        
        if test_url:
            logger.info(f"🔗 Navigating to test URL: {test_url}")
            success = agent.join_meeting(test_url, "Profile Setup Test")
            
            if success:
                logger.info("✅ Successfully joined meeting with profile!")
                input("Press Enter to leave meeting and finish setup...")
                agent.leave_meeting()
            else:
                logger.warning("⚠️  Could not join meeting - check your login")
                input("Press Enter to finish setup...")
        else:
            # Just open Chrome for manual login
            logger.info("🌐 Opening Chrome for manual login...")
            
            # Start browser and navigate to Google
            agent.playwright = agent.playwright or agent.playwright.__class__().start()
            
            if not agent.browser:
                browser_args = [
                    "--disable-features=Translate",
                    "--no-first-run", 
                    "--no-default-browser-check",
                    f"--user-data-dir={profile_path}"
                ]
                
                agent.browser = agent.playwright.chromium.launch(
                    headless=False,
                    args=browser_args
                )
            
            agent.page = agent.browser.new_page()
            agent.page.goto("https://accounts.google.com")
            
            logger.info("🔐 Please log into your Google account in the browser")
            input("Press Enter when you've finished logging in...")
        
        agent.close()
        
        logger.info("\n✅ Profile setup completed!")
        logger.info(f"📁 Profile saved to: {profile_path}")
        logger.info("\n🎯 Next steps:")
        logger.info("1. Update your .env file with:")
        logger.info(f"   CHROME_PROFILE_PATH={profile_path}")
        logger.info("   USE_CHROME_PROFILE=true")
        logger.info("2. Run your AI agent - it will now use the saved login!")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Setup cancelled by user")
        return False
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        return False

def test_profile():
    """Test an existing Chrome profile."""
    logger.info("🧪 Testing Chrome Profile")
    logger.info("=" * 40)
    
    profile_path = input(f"Enter Chrome profile path to test (default: {Config.CHROME_PROFILE_PATH}): ").strip()
    if not profile_path:
        profile_path = Config.CHROME_PROFILE_PATH
    
    profile_path = Path(profile_path)
    
    if not profile_path.exists():
        logger.error(f"❌ Profile path does not exist: {profile_path}")
        return False
    
    default_url = Config.GMEET_URL or ""
    if default_url:
        test_url = input(f"Enter Google Meet URL to test (default: {default_url}): ").strip()
        if not test_url:
            test_url = default_url
    else:
        test_url = input("Enter Google Meet URL to test: ").strip()
    
    if not test_url:
        logger.error("❌ No test URL provided")
        return False
    
    try:
        logger.info("🚀 Testing profile with Google Meet...")
        
        agent = GMeetAgent(
            headless=False,
            chrome_profile_path=str(profile_path),
            use_chrome_profile=True
        )
        
        success = agent.join_meeting(test_url, "Profile Test")
        
        if success:
            logger.info("✅ Profile test successful! You're logged in.")
            input("Press Enter to leave meeting...")
            agent.leave_meeting()
        else:
            logger.warning("⚠️  Profile test failed - may need to re-login")
        
        agent.close()
        return success
        
    except Exception as e:
        logger.error(f"❌ Profile test failed: {e}")
        return False

def list_profiles():
    """List available Chrome profiles."""
    logger.info("📋 Available Chrome Profiles")
    logger.info("=" * 40)
    
    # Check default location
    default_path = Path(Config.CHROME_PROFILE_PATH)
    if default_path.exists():
        logger.info(f"✅ Default profile: {default_path}")
        logger.info(f"   Size: {sum(f.stat().st_size for f in default_path.rglob('*') if f.is_file()) / 1024 / 1024:.1f} MB")
    else:
        logger.info(f"❌ Default profile not found: {default_path}")
    
    # Check for other common profile locations
    common_locations = [
        "~/Library/Application Support/Google/Chrome/Default",  # macOS
        "~/.config/google-chrome/Default",  # Linux
        "~/AppData/Local/Google/Chrome/User Data/Default",  # Windows
    ]
    
    logger.info("\n🔍 Common Chrome profile locations:")
    for location in common_locations:
        path = Path(location).expanduser()
        if path.exists():
            logger.info(f"✅ Found: {path}")
        else:
            logger.info(f"❌ Not found: {path}")

def main():
    """Main menu for profile management."""
    logger.info("🔧 Google Meet AI Agent - Chrome Profile Manager")
    logger.info("=" * 60)
    
    while True:
        print("\n📋 Options:")
        print("1. Set up new Chrome profile")
        print("2. Test existing profile") 
        print("3. List available profiles")
        print("4. Exit")
        
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            setup_chrome_profile()
        elif choice == "2":
            test_profile()
        elif choice == "3":
            list_profiles()
        elif choice == "4":
            logger.info("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-4.")

if __name__ == "__main__":
    main() 