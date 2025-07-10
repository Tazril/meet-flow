"""Google Meet specific browser automation agent."""

import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from playwright.sync_api import sync_playwright, Browser, Page, Playwright

from .base_interface import BrowserAutomationAgent

try:
    from ..utils.config import Config
    from ..utils.logger import setup_logger
except ImportError:
    # Handle direct module execution
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent))
    from utils.config import Config
    from utils.logger import setup_logger

logger = setup_logger("browser.gmeet")

class GMeetAgent(BrowserAutomationAgent):
    """Google Meet implementation of browser automation agent."""
    
    def __init__(self, 
                 headless: bool = False,
                 chrome_profile_path: Optional[str] = None,
                 use_chrome_profile: bool = True,
                 chrome_executable_path: Optional[str] = None):
        """Initialize Google Meet agent.
        
        Args:
            headless: Whether to run browser in headless mode
            chrome_profile_path: Path to Chrome profile directory
            use_chrome_profile: Whether to use persistent Chrome profile
            chrome_executable_path: Path to Chrome executable (optional)
        """
        self.headless = headless
        self.chrome_profile_path = chrome_profile_path or Config.CHROME_PROFILE_PATH
        self.use_chrome_profile = use_chrome_profile and Config.USE_CHROME_PROFILE
        self.chrome_executable_path = chrome_executable_path or Config.CHROME_EXECUTABLE_PATH
        
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.browser_context = None  # For persistent context (profiles)
        self.page: Optional[Page] = None
        self.meeting_url: Optional[str] = None
        self.in_meeting = False
        
        logger.info(f"🌐 GMeet Agent initialized (headless={headless}, profile={self.use_chrome_profile})")
    
    def join_meeting(self, url: str, display_name: Optional[str] = None) -> bool:
        """Join a Google Meet meeting.
        
        Args:
            url: Google Meet URL
            display_name: Name to display in meeting
            
        Returns:
            True if successfully joined
        """
        try:
            logger.info(f"🚀 Joining Google Meet: {url}")
            
            # Start Playwright if not already started
            if not self.playwright:
                self.playwright = sync_playwright().start()
            
            # Launch browser with appropriate flags for media access
            if not self.browser:
                browser_args = [
                    "--use-fake-ui-for-media-stream",  # Auto-approve media permissions
                    "--disable-features=Translate",   # Disable translation bar
                    "--disable-web-security",         # Allow media access
                    "--allow-running-insecure-content",
                    "--autoplay-policy=no-user-gesture-required",  # Allow autoplay
                    "--disable-blink-features=AutomationControlled",  # Hide automation
                    "--disable-extensions-except=",  # Disable extensions except allowed ones
                    "--disable-plugins-discovery",   # Disable plugin discovery
                ]
                
                # Handle Chrome profile vs regular browser launch
                if self.use_chrome_profile and not self.headless:
                    # Create profile directory if it doesn't exist
                    profile_path = Path(self.chrome_profile_path).resolve()
                    profile_path.mkdir(parents=True, exist_ok=True)
                    
                    # Add profile-specific args (without --user-data-dir)
                    browser_args.extend([
                        "--no-first-run",
                        "--no-default-browser-check",
                    ])
                    
                    # Use launch_persistent_context for profiles
                    launch_options = {
                        "headless": self.headless,
                        "args": browser_args
                    }
                    
                    # Add Chrome executable path if specified
                    if self.chrome_executable_path:
                        launch_options["executable_path"] = self.chrome_executable_path
                        logger.info(f"🔧 Using Chrome executable: {self.chrome_executable_path}")
                    
                    logger.info(f"📁 Using Chrome profile: {profile_path}")
                    
                    # Launch persistent context with profile
                    self.browser_context = self.playwright.chromium.launch_persistent_context(
                        user_data_dir=str(profile_path),
                        **launch_options
                    )
                    # Note: with persistent context, we use context.pages[0] instead of browser.new_page()
                    
                else:
                    # Use fake devices for testing when no profile
                    browser_args.append("--use-fake-device-for-media-stream")
                    
                    launch_options = {
                        "headless": self.headless,
                        "args": browser_args
                    }
                    
                    # Add Chrome executable path if specified
                    if self.chrome_executable_path:
                        launch_options["executable_path"] = self.chrome_executable_path
                        logger.info(f"🔧 Using Chrome executable: {self.chrome_executable_path}")
                    
                    self.browser = self.playwright.chromium.launch(**launch_options)
            
            # Create new page if needed
            if not self.page:
                if self.browser_context:
                    # Using persistent context (profile) - get existing page or create new one
                    if self.browser_context.pages:
                        self.page = self.browser_context.pages[0]
                    else:
                        self.page = self.browser_context.new_page()
                    
                    # Grant media permissions
                    self.browser_context.grant_permissions(["camera", "microphone"])
                else:
                    # Using regular browser
                    if not self.browser:
                        logger.error("Browser not available for creating new page")
                        return False
                    self.page = self.browser.new_page()
                    
                    # Grant media permissions
                    context = self.page.context
                    context.grant_permissions(["camera", "microphone"])
            
            # Navigate to meeting URL
            self.meeting_url = url
            self.page.goto(url)
            
            # Wait for page to load
            logger.info("⏳ Waiting for Google Meet to load...")
            self.page.wait_for_timeout(3000)
            
            # Set display name if provided
            if display_name:
                self._set_display_name(display_name)
            
            # Handle camera and microphone setup
            self._setup_media_devices()
            
            # Join the meeting
            success = self._click_join_button()
            
            if success:
                self.in_meeting = True
                logger.info("✅ Successfully joined Google Meet")
                return True
            else:
                logger.error("❌ Failed to join Google Meet")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error joining meeting: {e}")
            return False
    
    def leave_meeting(self) -> bool:
        """Leave the current Google Meet meeting."""
        try:
            if not self.page or not self.in_meeting:
                logger.warning("Not currently in a meeting")
                return True
            
            logger.info("👋 Leaving Google Meet...")
            
            # Try to find and click leave button
            leave_selectors = [
                "[aria-label*='Leave call']",
                "[aria-label*='End call']", 
                "button[data-call-leave]",
                ".DPvwYc",  # Google Meet leave button class
            ]
            
            for selector in leave_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        logger.info("✅ Successfully left meeting")
                        self.in_meeting = False
                        return True
                except Exception:
                    continue
            
            # If we can't find leave button, just close the page
            logger.warning("Could not find leave button, closing page")
            self.page.close()
            self.in_meeting = False
            return True
            
        except Exception as e:
            logger.error(f"❌ Error leaving meeting: {e}")
            return False
    
    def toggle_microphone(self, enabled: bool) -> bool:
        """Toggle microphone on/off."""
        try:
            if not self.page or not self.in_meeting:
                logger.warning("Not in a meeting")
                return False
            
            # Google Meet microphone button selectors
            mic_selectors = [
                "[aria-label*='microphone']",
                "[aria-label*='Microphone']", 
                "[data-tooltip*='microphone']",
                "div[role='button'][aria-label*='Turn']",
                "[data-tooltip*='Mute']",
                "[data-tooltip*='Unmute']",
                "[aria-label*='Mute']",
                "[aria-label*='Unmute']",
            ]
            
            current_state = self.is_microphone_enabled()
            if current_state == enabled:
                logger.info(f"Microphone already {'enabled' if enabled else 'disabled'}")
                return True
            
            for selector in mic_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        logger.info(f"🎤 Microphone {'enabled' if enabled else 'disabled'}")
                        return True
                except Exception:
                    continue
            
            # Don't treat this as a critical error - log as warning and return False
            logger.warning("Could not find microphone button - continuing without mic control")
            return False
            
        except Exception as e:
            logger.warning(f"⚠️ Error toggling microphone: {e} - continuing without mic control")
            return False
    
    def toggle_camera(self, enabled: bool) -> bool:
        """Toggle camera on/off."""
        try:
            if not self.page or not self.in_meeting:
                logger.warning("Not in a meeting")
                return False
            
            # Google Meet camera button selectors
            camera_selectors = [
                "[aria-label*='camera']",
                "[aria-label*='Camera']",
                "[data-tooltip*='camera']",
                "div[role='button'][aria-label*='Turn'][aria-label*='camera']",
            ]
            
            current_state = self.is_camera_enabled()
            if current_state == enabled:
                logger.info(f"Camera already {'enabled' if enabled else 'disabled'}")
                return True
            
            for selector in camera_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        logger.info(f"📹 Camera {'enabled' if enabled else 'disabled'}")
                        return True
                except Exception:
                    continue
            
            logger.error("Could not find camera button")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error toggling camera: {e}")
            return False
    
    def is_microphone_enabled(self) -> Optional[bool]:
        """Check if microphone is enabled."""
        try:
            if not self.page:
                return None
            
            # Look for muted/unmuted indicators
            muted_selectors = [
                "[aria-label*='Turn on microphone']",
                "[aria-label*='Unmute']",
                ".wuLiOc"  # Muted state class
            ]
            
            unmuted_selectors = [
                "[aria-label*='Turn off microphone']", 
                "[aria-label*='Mute']"
            ]
            
            # Check if muted
            for selector in muted_selectors:
                if self.page.is_visible(selector):
                    return False
            
            # Check if unmuted
            for selector in unmuted_selectors:
                if self.page.is_visible(selector):
                    return True
            
            return None
            
        except Exception:
            return None
    
    def is_camera_enabled(self) -> Optional[bool]:
        """Check if camera is enabled."""
        try:
            if not self.page:
                return None
            
            # Look for camera on/off indicators
            off_selectors = [
                "[aria-label*='Turn on camera']",
                "[aria-label*='camera off']"
            ]
            
            on_selectors = [
                "[aria-label*='Turn off camera']",
                "[aria-label*='camera on']"
            ]
            
            # Check if camera is off
            for selector in off_selectors:
                if self.page.is_visible(selector):
                    return False
            
            # Check if camera is on
            for selector in on_selectors:
                if self.page.is_visible(selector):
                    return True
            
            return None
            
        except Exception:
            return None
    
    def is_in_meeting(self) -> bool:
        """Check if currently in a meeting."""
        return self.in_meeting and self.page is not None
    
    def get_meeting_info(self) -> Dict[str, Any]:
        """Get information about the current meeting."""
        return {
            "url": self.meeting_url,
            "in_meeting": self.in_meeting,
            "microphone_enabled": self.is_microphone_enabled(),
            "camera_enabled": self.is_camera_enabled(),
            "platform": "Google Meet"
        }
    
    def get_participants(self) -> List[str]:
        """Get list of meeting participants."""
        try:
            if not self.page or not self.in_meeting:
                return []
            
            # This is challenging to implement reliably as Google Meet
            # doesn't always show participant names in accessible DOM
            # Would need more complex DOM parsing
            logger.warning("Participant list extraction not fully implemented")
            return []
            
        except Exception as e:
            logger.error(f"Error getting participants: {e}")
            return []
    
    def send_chat_message(self, message: str) -> bool:
        """Send a message to the meeting chat."""
        try:
            if not self.page or not self.in_meeting:
                logger.warning("Not in a meeting")
                return False
            
            # Open chat if not already open
            chat_button_selectors = [
                "[aria-label*='Chat']",
                "[aria-label*='chat']",
                "button[data-tooltip*='Chat']"
            ]
            
            # Find and click chat button
            for selector in chat_button_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        break
                except Exception:
                    continue
            
            # Wait for chat to open
            self.page.wait_for_timeout(1000)
            
            # Find chat input
            chat_input_selectors = [
                "textarea[placeholder*='message']",
                "input[placeholder*='message']",
                ".chat-input",
                "[aria-label*='Type a message']"
            ]
            
            for selector in chat_input_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.fill(selector, message)
                        self.page.press(selector, "Enter")
                        logger.info(f"💬 Sent chat message: {message[:50]}...")
                        return True
                except Exception:
                    continue
            
            logger.error("Could not find chat input")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error sending chat message: {e}")
            return False
    
    def close(self) -> None:
        """Clean up and close browser."""
        try:
            if self.in_meeting:
                self.leave_meeting()
            
            if self.page:
                self.page.close()
                self.page = None
            
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            logger.info("🔒 GMeet Agent closed")
            
        except Exception as e:
            logger.error(f"Error closing GMeet Agent: {e}")
    
    def _set_display_name(self, name: str) -> None:
        """Set display name before joining."""
        try:
            if not self.page:
                logger.warning("Page not available for setting display name")
                return
                
            name_input_selectors = [
                "input[placeholder*='name']",
                "input[aria-label*='name']",
                "input[type='text']"
            ]
            
            for selector in name_input_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.fill(selector, name)
                        logger.info(f"📝 Set display name: {name}")
                        return
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Could not set display name: {e}")
    
    def _setup_media_devices(self) -> None:
        """Configure camera and microphone before joining."""
        try:
            if not self.page:
                logger.warning("Page not available for setting up media devices")
                return
                
            # Wait for media setup UI
            self.page.wait_for_timeout(2000)
            
            # Disable camera by default (for privacy)
            camera_off_selectors = [
                "[aria-label*='Turn off camera']",
                "button[aria-label*='camera off']"
            ]
            
            for selector in camera_off_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        logger.info("📹 Camera disabled for privacy")
                        break
                except Exception:
                    continue
            
            # Ensure microphone is ready (but muted initially)
            mic_mute_selectors = [
                "[aria-label*='Turn off microphone']",
                "button[aria-label*='microphone off']"
            ]
            
            for selector in mic_mute_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        logger.info("🎤 Microphone muted initially")
                        break
                except Exception:
                    continue
                    
        except Exception as e:
            logger.warning(f"Error setting up media devices: {e}")
    
    def _click_join_button(self) -> bool:
        """Find and click the join button."""
        try:
            if not self.page:
                logger.error("Page not available for clicking join button")
                return False
                
            # Wait for join button to be available
            self.page.wait_for_timeout(2000)
            
            join_button_selectors = [
                "text=Join now",
                "text=Ask to join", 
                "[aria-label*='Join']",
                "button:has-text('Join')",
                ".VfPpkd-LgbsSe",  # Google button class
                "[jsname='Qx7uuf']"  # Google Meet join button
            ]
            
            for selector in join_button_selectors:
                try:
                    if self.page.is_visible(selector):
                        self.page.click(selector)
                        logger.info("🚪 Clicked join button")
                        
                        # Wait for meeting to load
                        self.page.wait_for_timeout(5000)
                        return True
                except Exception:
                    continue
            
            # If no explicit join button, try Enter key
            try:
                self.page.press("body", "Enter")
                logger.info("⌨️  Pressed Enter to join")
                self.page.wait_for_timeout(5000)
                return True
            except Exception:
                pass
            
            logger.error("Could not find join button")
            return False
            
        except Exception as e:
            logger.error(f"Error clicking join button: {e}")
            return False
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close() 