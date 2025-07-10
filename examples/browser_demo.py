#!/usr/bin/env python3
"""Demo script showcasing the Google Meet browser automation system."""

import time
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from browser import MeetingController
from utils.config import Config
from utils.logger import setup_logger

logger = setup_logger("browser_demo")

def demo_browser_automation():
    """Demonstrate browser automation capabilities."""
    logger.info("🎬 Google Meet Browser Automation Demo")
    logger.info("=" * 60)
    
    # Show configuration
    logger.info("📋 Current Configuration:")
    config_info = Config.print_config()
    for section, values in config_info.items():
        logger.info(f"  {section}: {values}")
    
    # Ask user for meeting URL
    print("\n" + "=" * 60)
    print("🤖 BROWSER AUTOMATION DEMO")
    print("=" * 60)
    
    meeting_url = input("Enter Google Meet URL (or press Enter to use config): ").strip()
    if not meeting_url:
        meeting_url = Config.GMEET_URL
    
    if not meeting_url:
        logger.error("❌ No meeting URL provided. Please set GMEET_URL in .env or provide one above.")
        return False
    
    display_name = input("Enter display name (or press Enter for 'AI Assistant'): ").strip()
    if not display_name:
        display_name = Config.AGENT_NAME or "AI Assistant"
    
    # Ask about headless mode
    headless_response = input("Run in headless mode? (y/N): ").strip().lower()
    headless = headless_response == 'y'
    
    print(f"\n🚀 Starting demo with:")
    print(f"  URL: {meeting_url}")
    print(f"  Name: {display_name}")
    print(f"  Headless: {headless}")
    print()
    
    try:
        # Initialize Meeting Controller
        logger.info("🎬 Initializing Meeting Controller...")
        controller = MeetingController(
            agent_type="gmeet",
            headless=headless,
            auto_setup_audio=True
        )
        
        # Join the meeting
        logger.info("🚀 Joining Google Meet...")
        success = controller.join_meeting(
            url=meeting_url,
            display_name=display_name
        )
        
        if not success:
            logger.error("❌ Failed to join meeting")
            return False
        
        logger.info("✅ Successfully joined meeting!")
        
        # Demo basic functionality
        logger.info("\n🎯 Demonstrating basic controls...")
        
        # Show meeting status
        status = controller.get_meeting_status()
        logger.info(f"📊 Meeting Status: {status['controller']}")
        
        # Test microphone controls
        logger.info("🎤 Testing microphone controls...")
        logger.info("  Muting microphone...")
        controller.toggle_microphone(False)
        time.sleep(2)
        
        logger.info("  Unmuting microphone...")
        controller.toggle_microphone(True)
        time.sleep(2)
        
        # Test audio injection
        logger.info("🎵 Testing audio injection...")
        logger.info("  Playing test tone...")
        success = controller.av_input.inject_test_tone(frequency=440, duration=2.0)
        logger.info(f"  Audio injection: {'✅ Success' if success else '❌ Failed'}")
        
        # Test speech capture
        logger.info("🗣️  Testing speech capture...")
        logger.info("  Listening for 5 seconds...")
        audio_result = controller.listen_for_speech(
            max_duration=5.0,
            silence_timeout=2.0,
            save_to_file=True
        )
        
        if audio_result:
            logger.info(f"  ✅ Captured speech and saved to: {audio_result}")
        else:
            logger.info("  ⚠️  No speech detected")
        
        # Interactive menu
        while True:
            print(f"\n{'='*40}")
            print("🎮 INTERACTIVE DEMO MENU")
            print("=" * 40)
            print("1. Toggle microphone")
            print("2. Toggle camera") 
            print("3. Send chat message")
            print("4. Play test tone")
            print("5. Listen for speech")
            print("6. Show meeting status")
            print("7. Leave meeting")
            print("=" * 40)
            
            choice = input("Enter choice (1-7): ").strip()
            
            if choice == "1":
                # Toggle microphone
                current_state = controller.agent.is_microphone_enabled()
                new_state = not current_state if current_state is not None else True
                controller.toggle_microphone(new_state)
                logger.info(f"🎤 Microphone {'enabled' if new_state else 'disabled'}")
                
            elif choice == "2":
                # Toggle camera
                current_state = controller.agent.is_camera_enabled()
                new_state = not current_state if current_state is not None else True
                controller.toggle_camera(new_state)
                logger.info(f"📹 Camera {'enabled' if new_state else 'disabled'}")
                
            elif choice == "3":
                # Send chat message
                message = input("Enter chat message: ").strip()
                if message:
                    success = controller.send_chat_message(message)
                    logger.info(f"💬 Chat message: {'✅ Sent' if success else '❌ Failed'}")
                
            elif choice == "4":
                # Play test tone
                freq = input("Enter frequency (default 440): ").strip()
                duration = input("Enter duration (default 2.0): ").strip()
                
                try:
                    freq = float(freq) if freq else 440.0
                    duration = float(duration) if duration else 2.0
                except ValueError:
                    freq, duration = 440.0, 2.0
                
                success = controller.av_input.inject_test_tone(freq, duration)
                logger.info(f"🎵 Test tone: {'✅ Played' if success else '❌ Failed'}")
                
            elif choice == "5":
                # Listen for speech
                max_dur = input("Max duration (default 10s): ").strip()
                silence_timeout = input("Silence timeout (default 3s): ").strip()
                
                try:
                    max_dur = float(max_dur) if max_dur else 10.0
                    silence_timeout = float(silence_timeout) if silence_timeout else 3.0
                except ValueError:
                    max_dur, silence_timeout = 10.0, 3.0
                
                logger.info(f"🗣️  Listening for speech (max {max_dur}s, silence {silence_timeout}s)...")
                result = controller.listen_for_speech(max_dur, silence_timeout, save_to_file=True)
                
                if result:
                    logger.info(f"✅ Speech captured: {result}")
                else:
                    logger.info("⚠️  No speech detected")
                
            elif choice == "6":
                # Show status
                status = controller.get_meeting_status()
                logger.info("📊 Meeting Status:")
                for section, data in status.items():
                    logger.info(f"  {section}: {data}")
                
            elif choice == "7":
                # Leave meeting
                logger.info("👋 Leaving meeting...")
                break
                
            else:
                print("❌ Invalid choice. Please enter 1-7.")
        
        # Leave meeting
        controller.leave_meeting()
        logger.info("✅ Demo completed successfully!")
        
        return True
        
    except KeyboardInterrupt:
        logger.info("\n⏹️  Demo interrupted by user")
        if 'controller' in locals():
            controller.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Demo failed: {e}")
        if 'controller' in locals():
            controller.close()
        return False

def main():
    """Run the browser automation demo."""
    try:
        success = demo_browser_automation()
        print("\n" + "=" * 60)
        if success:
            print("🎉 Browser automation demo completed!")
            print("\n✨ Phase 2.2: Browser Automation is ready!")
            print("\n📋 Next Steps:")
            print("  • Phase 2.3: Whisper Integration (Speech-to-Text)")
            print("  • Phase 2.4: GPT-4o Integration (AI Responses)")
            print("  • Phase 2.5: TTS Integration (Text-to-Speech)")
            print("  • Phase 3: Complete Agent Loop")
        else:
            print("❌ Demo encountered issues. Check the logs above.")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"💥 Demo crashed: {e}")
        return False

if __name__ == "__main__":
    main() 