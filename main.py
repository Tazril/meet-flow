#!/usr/bin/env python3
"""
Google Meet AI Agent - Main Entry Point

This is the main agent that integrates all components:
- Browser automation (auto-join GMeet)
- Audio capture and playback
- AI conversation (Whisper + GPT + TTS)

Usage:
    python main.py
"""

import sys
import time
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

# Add src to Python path
sys.path.append(str(Path(__file__).parent / "src"))

from src.utils.config import Config
from src.utils.logger import setup_logger
from src.browser import MeetingController
from src.ai import ConversationManager
from src.audio import AudioCapture, VoiceActivityDetector
from src.ai.conversation_manager import ConversationContext

logger = setup_logger("main")

class GMeetAIAgent:
    """Main Google Meet AI Agent that integrates all components."""
    
    def __init__(self):
        """Initialize the agent."""
        self.meeting_controller: Optional[MeetingController] = None
        self.conversation_manager: Optional[ConversationManager] = None
        self.audio_capture: Optional[AudioCapture] = None
        self.vad: Optional[VoiceActivityDetector] = None
        self.running = False
        self._ignore_audio_until = 0  # Timestamp to ignore audio until (feedback prevention)
        
        logger.info("🤖 GMeet AI Agent initializing...")
        
        # Validate configuration
        if not Config.validate():
            logger.error("❌ Configuration validation failed")
            sys.exit(1)
        
        Config.print_status()
    
    async def initialize(self) -> bool:
        """Initialize all components."""
        try:
            # Initialize conversation manager (AI components)
            logger.info("🧠 Initializing AI components...")
            self.conversation_manager = ConversationManager()
            
            # Test AI components
            ai_test_results = await self.conversation_manager.test_all_components()
            if not all(ai_test_results.values()):
                logger.error(f"❌ AI component tests failed: {ai_test_results}")
                return False
            
            # Initialize meeting controller (browser automation)
            logger.info("🌐 Initializing browser automation...")
            self.meeting_controller = MeetingController(
                agent_type="gmeet",
                headless=False,  # Keep visible for now
                auto_setup_audio=False,  # We'll handle audio separately
                use_chrome_profile=Config.USE_CHROME_PROFILE,
                chrome_profile_path=Config.CHROME_PROFILE_PATH
            )
            
            # Initialize audio components
            logger.info("🎤 Initializing audio system...")
            self.audio_capture = AudioCapture(
                device=Config.AUDIO_DEVICE_INPUT,
                sample_rate=Config.SAMPLE_RATE
            )
            
            self.vad = VoiceActivityDetector(
                sample_rate=Config.SAMPLE_RATE,
                aggressiveness=Config.VAD_AGGRESSIVENESS
            )
            
            logger.info("✅ All components initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False
    
    async def join_meeting(self, url: Optional[str] = None) -> bool:
        """Join a Google Meet meeting."""
        try:
            url = url or Config.GMEET_URL
            if not url or url == "https://meet.google.com/new":
                url = input("Enter Google Meet URL: ").strip()
            
            logger.info(f"🚀 Joining meeting: {url}")
            
            if not self.meeting_controller:
                logger.error("❌ Meeting controller not initialized")
                return False
            
            success = await asyncio.to_thread(
                self.meeting_controller.join_meeting,
                url=url,
                display_name=Config.AGENT_NAME
            )
            
            if not success:
                logger.error("❌ Failed to join meeting")
                return False
            
            # Wait a moment for meeting to settle
            await asyncio.sleep(3)
            
            # Ensure microphone is enabled for speaking and keep it on by default
            self.meeting_controller.toggle_microphone(True)
            if Config.KEEP_MICROPHONE_ON:
                logger.info("🎤 Microphone enabled and will stay on by default for continuous conversation")
            else:
                logger.info("🎤 Microphone enabled (will be managed manually)")
            
            # Announce the agent's presence with TTS
            await self._announce_presence()
            
            logger.info("✅ Successfully joined meeting and ready to participate")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error joining meeting: {e}")
            return False
    
    async def start_conversation_loop(self):
        """Start the main conversation loop."""
        logger.info("🎯 Starting conversation loop...")
        
        if not self.conversation_manager:
            logger.error("❌ Conversation manager not initialized")
            return
        
        if not self.audio_capture:
            logger.error("❌ Audio capture not initialized") 
            return
        
        # Start conversation manager
        context = ConversationContext(
            meeting_title="Google Meet AI Agent Session",
            participants=["Meeting Participants", Config.AGENT_NAME],
            agent_name=Config.AGENT_NAME
        )
        self.conversation_manager.start_conversation(context)
        
        # Set up audio capture callbacks to prevent feedback loops
        self.conversation_manager.set_audio_capture_callback(
            pause_callback=self._pause_audio_capture,
            resume_callback=self._resume_audio_capture
        )
        
        # Start audio capture
        if not self.audio_capture.start_recording():
            logger.error("❌ Failed to start audio recording")
            return
        
        logger.info("🎧 Listening for speech...")
        self.running = True
        
        # Counter for periodic microphone checks (every 30 seconds)
        mic_check_counter = 0
        mic_check_interval = 300  # 30 seconds at 0.1s intervals
        
        try:
            while self.running:
                # Get audio chunk
                audio_chunk = self.audio_capture.get_audio_chunk(timeout=0.5)
                if audio_chunk is None:
                    continue
                
                if not self.vad:
                    logger.error("❌ VAD not initialized")
                    break
                
                # Check if we should ignore audio (during TTS playback)
                if self._should_ignore_audio():
                    continue
                
                # Check for speech activity
                is_speaking, speech_started, speech_ended = self.vad.update_speech_state(audio_chunk)
                
                if speech_ended:
                    # Double-check we're not ignoring audio
                    if self._should_ignore_audio():
                        logger.debug("🔇 Ignoring speech during TTS playback")
                        continue
                    
                    # Get recent audio for transcription
                    logger.info("🗣️ Speech detected, processing...")
                    
                    # Get audio buffer from last 5 seconds to capture full speech
                    speech_audio = self.audio_capture.get_audio_buffer(duration=5.0)
                    if speech_audio is not None:
                        # Process the speech
                        await self._process_speech(speech_audio)
                
                # Periodic microphone check to ensure it stays on (only if configured)
                if Config.KEEP_MICROPHONE_ON:
                    mic_check_counter += 1
                    if mic_check_counter >= mic_check_interval:
                        await self._ensure_microphone_on()
                        mic_check_counter = 0
                
                # Small delay to prevent excessive CPU usage
                await asyncio.sleep(0.1)
                
        except KeyboardInterrupt:
            logger.info("🛑 Conversation loop interrupted by user")
        except Exception as e:
            logger.error(f"❌ Error in conversation loop: {e}")
        finally:
            if self.audio_capture:
                self.audio_capture.stop_recording()
            if self.conversation_manager:
                self.conversation_manager.stop_conversation()
    
    async def _process_speech(self, audio_data):
        """Process detected speech and generate response."""
        try:
            if not self.conversation_manager:
                logger.error("❌ Conversation manager not available")
                return
            
            # Process audio through conversation manager
            response_audio_file = await self.conversation_manager.process_audio_input(
                audio_data,
                Config.SAMPLE_RATE
            )
            
            if response_audio_file:
                logger.info(f"🔊 Playing response: {response_audio_file}")
                
                # Try to ensure microphone is on before speaking (but don't fail if it doesn't work)
                await self._try_enable_microphone()
                
                # Play response through meeting (continue even if mic button issues)
                if self.meeting_controller and self.meeting_controller.av_input:
                    success = self.meeting_controller.av_input.inject_audio_file(response_audio_file)
                    if success:
                        logger.info("✅ Response played successfully")
                    else:
                        logger.warning("⚠️ Failed to play response in meeting")
                else:
                    # Fallback: play audio directly using system audio
                    logger.warning("⚠️ Meeting controller not available, playing audio directly")
                    await self._play_audio_fallback(response_audio_file)
                
                # Clean up temporary audio file
                try:
                    Path(response_audio_file).unlink(missing_ok=True)
                except Exception as e:
                    logger.debug(f"Could not clean up audio file: {e}")
            else:
                logger.debug("🤐 No response generated")
                
        except Exception as e:
            logger.error(f"❌ Error processing speech: {e}")
    
    async def _try_enable_microphone(self):
        """Try to enable microphone, but don't fail if it doesn't work."""
        try:
            if self.meeting_controller and self.meeting_controller.meeting_active:
                # Try to enable microphone, but continue even if it fails
                success = self.meeting_controller.toggle_microphone(True)
                if success:
                    logger.debug("🎤 Microphone enabled for speaking")
                else:
                    logger.warning("⚠️ Could not enable microphone, but continuing with audio playback")
        except Exception as e:
            logger.warning(f"⚠️ Error enabling microphone: {e}, but continuing with audio playback")

    async def _play_audio_fallback(self, audio_file: str):
        """Fallback method to play audio directly using system audio."""
        try:
            import subprocess
            logger.info(f"🔊 Playing audio file directly: {audio_file}")
            
            # Use afplay on macOS to play audio directly to system output
            result = subprocess.run(['afplay', audio_file], capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✅ Audio played successfully using system audio")
            else:
                logger.error(f"❌ Failed to play audio: {result.stderr}")
                
        except Exception as e:
            logger.error(f"❌ Error in audio fallback: {e}")

    def _pause_audio_capture(self):
        """Pause audio capture to prevent feedback during TTS playback."""
        try:
            if self.audio_capture and self.audio_capture.recording:
                logger.info("🔇 Pausing audio capture to prevent TTS feedback")
                # Clear audio buffer to remove any queued audio
                self.audio_capture.clear_buffer()
                # Set a flag to ignore audio during TTS playback
                self._ignore_audio_until = time.time() + 5.0  # Ignore for 5 seconds
        except Exception as e:
            logger.warning(f"⚠️ Error pausing audio capture: {e}")

    def _resume_audio_capture(self):
        """Resume audio capture after TTS playback."""
        try:
            if self.audio_capture and self.audio_capture.recording:
                logger.info("🔊 Audio capture resumed after TTS")
                # Clear buffer again to avoid capturing TTS tail
                self.audio_capture.clear_buffer()
                # Reset ignore flag
                self._ignore_audio_until = 0
        except Exception as e:
            logger.warning(f"⚠️ Error resuming audio capture: {e}")

    def _should_ignore_audio(self) -> bool:
        """Check if we should ignore audio (during TTS playback)."""
        if hasattr(self, '_ignore_audio_until'):
            return time.time() < self._ignore_audio_until
        return False

    async def _ensure_microphone_on(self):
        """Ensure microphone stays on for continuous conversation."""
        try:
            # Only enforce microphone staying on if configured to do so
            if not Config.KEEP_MICROPHONE_ON:
                return
                
            if self.meeting_controller and self.meeting_controller.meeting_active:
                # Check current microphone state
                current_state = None
                if self.meeting_controller.agent:
                    current_state = self.meeting_controller.agent.is_microphone_enabled()
                
                if current_state is False:
                    # Microphone was turned off, turn it back on
                    logger.info("🎤 Microphone was off, turning back on for continuous conversation")
                    self.meeting_controller.toggle_microphone(True)
                elif current_state is None:
                    # Can't determine state, ensure it's on
                    logger.debug("🎤 Ensuring microphone stays on")
                    self.meeting_controller.toggle_microphone(True)
                # If current_state is True, microphone is already on, no action needed
                
        except Exception as e:
            logger.debug(f"Error checking microphone state: {e}")
    
    async def _announce_presence(self):
        """Announce the agent's presence in the meeting using TTS."""
        try:
            logger.info("🔊 Announcing agent presence...")
            
            # Generate greeting message
            greeting_message = f"Hello everyone! {Config.AGENT_NAME} has joined the meeting and is ready to assist."
            
            if not self.conversation_manager:
                logger.error("❌ Conversation manager not available for announcement")
                return
            
            # Generate TTS audio for the greeting
            logger.info(f"🗣️ Generating announcement: {greeting_message}")
            audio_file = self.conversation_manager.tts.synthesize_text(greeting_message)
            
            if audio_file:
                logger.info(f"🎵 Playing announcement: {audio_file}")
                
                # Wait a moment for the meeting to be fully ready
                await asyncio.sleep(2)
                
                # Play announcement through meeting
                if self.meeting_controller and self.meeting_controller.av_input:
                    success = self.meeting_controller.av_input.inject_audio_file(audio_file)
                    if success:
                        logger.info("✅ Announcement played successfully")
                    else:
                        logger.warning("⚠️ Failed to play announcement in meeting")
                
                # Clean up temporary audio file
                try:
                    Path(audio_file).unlink(missing_ok=True)
                except Exception as e:
                    logger.debug(f"Could not clean up announcement audio file: {e}")
            else:
                logger.error("❌ Failed to generate announcement audio")
                
        except Exception as e:
            logger.error(f"❌ Error announcing presence: {e}")
    
    def stop(self):
        """Stop the agent."""
        logger.info("🛑 Stopping agent...")
        self.running = False
        
        if self.audio_capture:
            self.audio_capture.stop_recording()
        
        if self.meeting_controller:
            self.meeting_controller.leave_meeting()
            self.meeting_controller.close()
        
        if self.conversation_manager:
            self.conversation_manager.stop_conversation()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current agent status."""
        return {
            "running": self.running,
            "in_meeting": (self.meeting_controller.agent.is_in_meeting() 
                         if self.meeting_controller and self.meeting_controller.agent else False),
            "conversation_active": (self.conversation_manager.is_active 
                                  if self.conversation_manager else False),
            "audio_recording": (self.audio_capture.recording 
                              if self.audio_capture else False)
        }

async def main():
    """Main function."""
    print("🤖 Google Meet AI Agent")
    print("=" * 40)
    
    agent = GMeetAIAgent()
    
    try:
        # Initialize all components
        if not await agent.initialize():
            logger.error("❌ Agent initialization failed")
            return
        
        # Join meeting
        if not await agent.join_meeting():
            logger.error("❌ Failed to join meeting")
            return
        
        print("\n🎯 Agent is ready! Commands:")
        print("  - Agent will automatically respond to speech")
        print("  - Press Ctrl+C to stop")
        print("=" * 40)
        
        # Start main conversation loop
        await agent.start_conversation_loop()
        
    except KeyboardInterrupt:
        print("\n👋 Stopping agent...")
    except Exception as e:
        logger.error(f"❌ Agent error: {e}")
    finally:
        agent.stop()
        print("✅ Agent stopped")

if __name__ == "__main__":
    asyncio.run(main()) 