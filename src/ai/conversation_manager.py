"""Conversation manager that orchestrates Whisper, GPT, and TTS for natural conversation flow."""

import time
import asyncio
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path
import numpy as np
import tempfile
import wave

from .whisper_client import WhisperClient
from .gpt_client import GPTClient
from .tts_client import TTSClient
from ..utils.logger import setup_logger

logger = setup_logger("ai.conversation")

@dataclass
class ConversationMessage:
    """Represents a single message in the conversation."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ConversationContext:
    """Current conversation context and state."""
    meeting_title: Optional[str] = None
    participants: List[str] = field(default_factory=list)
    meeting_duration: Optional[str] = None
    current_time: Optional[str] = None
    recent_topics: List[str] = field(default_factory=list)
    agent_name: str = "AI Assistant"

class ConversationManager:
    """Manages the complete conversation flow from speech-to-text to text-to-speech."""
    
    def __init__(self,
                 whisper_client: Optional[WhisperClient] = None,
                 gpt_client: Optional[GPTClient] = None,
                 tts_client: Optional[TTSClient] = None,
                 max_history_length: int = 50,
                 response_delay: float = 0.5,
                 conversation_timeout: float = 300.0):
        """Initialize conversation manager.
        
        Args:
            whisper_client: Whisper client for STT
            gpt_client: GPT client for conversation
            tts_client: TTS client for speech synthesis
            max_history_length: Maximum conversation history to keep
            response_delay: Delay before responding (seconds)
            conversation_timeout: Timeout for conversation session (seconds)
        """
        # Initialize AI clients
        self.whisper = whisper_client or WhisperClient()
        self.gpt = gpt_client or GPTClient()
        self.tts = tts_client or TTSClient()
        
        # Conversation state
        self.conversation_history: List[ConversationMessage] = []
        self.context = ConversationContext()
        self.max_history_length = max_history_length
        self.response_delay = response_delay
        self.conversation_timeout = conversation_timeout
        
        # Callbacks for external integration
        self.on_speech_detected: Optional[Callable[[str], None]] = None
        self.on_response_generated: Optional[Callable[[str], None]] = None
        self.on_audio_ready: Optional[Callable[[str], None]] = None
        self.on_error: Optional[Callable[[Exception], None]] = None
        
        # State tracking
        self.is_active = False
        self.last_activity_time = time.time()
        self.session_start_time = None
        
        logger.info("🤖 Conversation manager initialized")
    
    def start_conversation(self, context: Optional[ConversationContext] = None):
        """Start a new conversation session.
        
        Args:
            context: Initial conversation context
        """
        self.is_active = True
        self.session_start_time = time.time()
        self.last_activity_time = time.time()
        self.conversation_history.clear()
        
        if context:
            self.context = context
        
        # Add system message
        system_msg = ConversationMessage(
            role="system",
            content=f"Conversation started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            metadata={"event": "session_start"}
        )
        self.conversation_history.append(system_msg)
        
        logger.info(f"🚀 Conversation session started (agent: {self.context.agent_name})")
    
    def stop_conversation(self):
        """Stop the current conversation session."""
        self.is_active = False
        
        if self.session_start_time:
            duration = time.time() - self.session_start_time
            logger.info(f"🛑 Conversation session ended (duration: {duration:.1f}s)")
        
        # Add system message
        system_msg = ConversationMessage(
            role="system",
            content=f"Conversation ended at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            metadata={"event": "session_end"}
        )
        self.conversation_history.append(system_msg)
    
    async def process_audio_input(self, audio_data: np.ndarray, sample_rate: int) -> Optional[str]:
        """Process audio input and generate response.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Sample rate of audio data
            
        Returns:
            Path to generated response audio file, or None if no response
        """
        if not self.is_active:
            return None
        
        try:
            # Update activity time
            self.last_activity_time = time.time()
            
            logger.info("🎙️ Processing audio input...")
            
            # Save captured audio for debugging
            timestamp = int(time.time())
            recordings_dir = Path("recordings")
            recordings_dir.mkdir(exist_ok=True)
            
            input_audio_file = recordings_dir / f"captured_{timestamp}.wav"
            self._save_audio_to_wav(audio_data, sample_rate, str(input_audio_file))
            logger.info(f"💾 Captured audio saved to: {input_audio_file}")
            
            # Create temporary file for transcription
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
                temp_audio_file = temp_file.name
            
            # Save audio data to temporary file for transcription
            self._save_audio_to_wav(audio_data, sample_rate, temp_audio_file)
            
            # Step 1: Transcribe audio using Whisper
            logger.info("🎙️ Processing audio input...")
            
            # Get conversation context for better transcription
            context_text = self._get_transcription_context()
            
            transcribed_text = self.whisper.transcribe_speech_segment(
                audio_data, 
                sample_rate, 
                context=context_text
            )
            
            if not transcribed_text.strip():
                logger.debug("No speech detected in audio")
                return None
            
            logger.info(f"📝 Transcribed: {transcribed_text}")
            
            # Trigger callback
            if self.on_speech_detected:
                self.on_speech_detected(transcribed_text)
            
            # Step 2: Add to conversation history
            user_msg = ConversationMessage(
                role="user",
                content=transcribed_text,
                metadata={"source": "audio_input"}
            )
            self._add_message(user_msg)
            
            # Step 3: Decide if we should respond
            should_respond = self.gpt.should_respond(
                transcribed_text,
                {"agent_name": self.context.agent_name}
            )
            
            if not should_respond:
                logger.info("🤐 Deciding not to respond to this message")
                return None
            
            # Step 4: Generate response using GPT
            response_text = await self._generate_response(transcribed_text)
            
            if not response_text or not response_text.strip():
                return None
            
            # Step 5: Convert response to speech using TTS
            audio_file = self._synthesize_response(response_text)
            
            return audio_file
            
        except Exception as e:
            logger.error(f"❌ Error processing audio input: {e}")
            if self.on_error:
                self.on_error(e)
            return None
    
    async def process_text_input(self, text: str) -> Optional[str]:
        """Process text input and generate response.
        
        Args:
            text: Input text message
            
        Returns:
            Path to generated response audio file, or None if no response
        """
        if not self.is_active:
            return None
        
        try:
            # Update activity time
            self.last_activity_time = time.time()
            
            logger.info(f"💬 Processing text input: {text}")
            
            # Trigger callback
            if self.on_speech_detected:
                self.on_speech_detected(text)
            
            # Add to conversation history
            user_msg = ConversationMessage(
                role="user",
                content=text,
                metadata={"source": "text_input"}
            )
            self._add_message(user_msg)
            
            # Decide if we should respond
            should_respond = self.gpt.should_respond(
                text,
                {"agent_name": self.context.agent_name}
            )
            
            if not should_respond:
                logger.info("🤐 Deciding not to respond to this message")
                return None
            
            # Generate response
            response_text = await self._generate_response(text)
            
            if not response_text or not response_text.strip():
                return None
            
            # Convert to speech
            audio_file = self._synthesize_response(response_text)
            
            return audio_file
            
        except Exception as e:
            logger.error(f"❌ Error processing text input: {e}")
            if self.on_error:
                self.on_error(e)
            return None
    
    async def _generate_response(self, input_text: str) -> Optional[str]:
        """Generate response text using GPT.
        
        Args:
            input_text: Input text to respond to
            
        Returns:
            Generated response text or None if failed
        """
        try:
            # Add response delay
            if self.response_delay > 0:
                await asyncio.sleep(self.response_delay)
            
            # Build context
            context_dict = {
                "meeting_title": self.context.meeting_title,
                "participants": self.context.participants,
                "meeting_duration": self.context.meeting_duration,
                "current_time": datetime.now().strftime("%H:%M"),
                "recent_topics": self.context.recent_topics
            }
            
            # Generate response using async GPT client
            response_text = await self.gpt.generate_response(
                input_text,
                context=context_dict
            )
            
            if not response_text:
                logger.warning("No response generated by GPT")
                return None
            
            logger.info(f"🧠 Generated response: {response_text}")
            
            # Trigger callback
            if self.on_response_generated:
                self.on_response_generated(response_text)
            
            # Add to conversation history
            assistant_msg = ConversationMessage(
                role="assistant",
                content=response_text,
                metadata={"source": "gpt_response"}
            )
            self._add_message(assistant_msg)
            
            # Update recent topics
            self._update_recent_topics(input_text, response_text)
            
            return response_text
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return "I'm sorry, I'm having trouble responding right now."
    
    def _synthesize_response(self, response_text: str) -> Optional[str]:
        """Synthesize response text to speech.
        
        Args:
            response_text: Text to synthesize
            
        Returns:
            Path to generated audio file
        """
        try:
            logger.info("🔇 Pausing audio capture to prevent feedback during TTS synthesis...")
            
            # Pause audio capture to prevent feedback loop
            if hasattr(self, 'pause_audio_capture') and self.pause_audio_capture:
                self.pause_audio_capture()
            
            # Check if text is too long and split if necessary
            text_chunks = self.tts.split_text_for_synthesis(response_text)
            
            if len(text_chunks) == 1:
                # Single chunk
                audio_file = self.tts.synthesize_text(response_text)
            else:
                # Multiple chunks - synthesize separately and use first one
                # (In a more advanced implementation, you could concatenate them)
                logger.info(f"📝 Splitting response into {len(text_chunks)} chunks")
                audio_file = self.tts.synthesize_text(text_chunks[0])
                
                # Optionally synthesize remaining chunks
                if len(text_chunks) > 1:
                    logger.warning(f"⚠️ Response too long, using only first chunk")
            
            if audio_file:
                logger.info(f"🔊 Response audio ready: {audio_file}")
                
                # Trigger callback
                if self.on_audio_ready:
                    self.on_audio_ready(audio_file)
            
            return audio_file
            
        except Exception as e:
            logger.error(f"❌ Error synthesizing response: {e}")
            return None
        finally:
            # Always resume audio capture after TTS synthesis
            logger.info("🔊 Resuming audio capture after TTS synthesis...")
            if hasattr(self, 'resume_audio_capture') and self.resume_audio_capture:
                # Resume immediately for now (delay will be handled during playback)
                self.resume_audio_capture()
    
    def _add_message(self, message: ConversationMessage):
        """Add message to conversation history with length management.
        
        Args:
            message: Message to add
        """
        self.conversation_history.append(message)
        
        # Keep only recent messages (excluding system messages)
        non_system_messages = [
            msg for msg in self.conversation_history 
            if msg.role != "system"
        ]
        
        if len(non_system_messages) > self.max_history_length:
            # Remove oldest non-system messages
            messages_to_remove = len(non_system_messages) - self.max_history_length
            removed_count = 0
            
            for i, msg in enumerate(self.conversation_history):
                if msg.role != "system" and removed_count < messages_to_remove:
                    self.conversation_history.pop(i)
                    removed_count += 1
    
    def _get_conversation_messages(self) -> List[Dict[str, str]]:
        """Get conversation messages in format expected by GPT client.
        
        Returns:
            List of conversation messages
        """
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat()
            }
            for msg in self.conversation_history
            if msg.role in ["user", "assistant"]  # Exclude system messages
        ]
    
    def _get_transcription_context(self) -> Optional[str]:
        """Get recent conversation context for better transcription.
        
        Returns:
            Recent conversation text for context
        """
        recent_messages = self.conversation_history[-5:]  # Last 5 messages
        context_parts = []
        
        for msg in recent_messages:
            if msg.role in ["user", "assistant"]:
                context_parts.append(msg.content)
        
        if context_parts:
            return " ".join(context_parts)
        return None
    
    def _update_recent_topics(self, input_text: str, response_text: str):
        """Update recent topics based on conversation.
        
        Args:
            input_text: User input
            response_text: Assistant response
        """
        try:
            # Simple topic extraction - get key words
            combined_text = f"{input_text} {response_text}".lower()
            words = combined_text.split()
            
            # Filter for meaningful words (simple approach)
            meaningful_words = [
                word for word in words 
                if len(word) > 3 and word.isalpha()
            ]
            
            # Add to recent topics (keep unique)
            for word in meaningful_words[:3]:  # Top 3 words
                if word not in self.context.recent_topics:
                    self.context.recent_topics.append(word)
            
            # Keep only recent topics
            if len(self.context.recent_topics) > 10:
                self.context.recent_topics = self.context.recent_topics[-10:]
                
        except Exception as e:
            logger.debug(f"Error updating topics: {e}")
    
    def update_context(self, 
                      meeting_title: Optional[str] = None,
                      participants: Optional[List[str]] = None,
                      meeting_duration: Optional[str] = None):
        """Update conversation context.
        
        Args:
            meeting_title: Meeting title
            participants: List of participant names
            meeting_duration: Meeting duration string
        """
        if meeting_title is not None:
            self.context.meeting_title = meeting_title
        
        if participants is not None:
            self.context.participants = participants
        
        if meeting_duration is not None:
            self.context.meeting_duration = meeting_duration
        
        logger.info("📋 Conversation context updated")
    
    def set_agent_name(self, name: str):
        """Set the agent name for conversation.
        
        Args:
            name: Agent name
        """
        self.context.agent_name = name
        logger.info(f"🏷️ Agent name set to: {name}")
    
    def is_conversation_active(self) -> bool:
        """Check if conversation is still active.
        
        Returns:
            True if conversation is active
        """
        if not self.is_active:
            return False
        
        # Check timeout
        if time.time() - self.last_activity_time > self.conversation_timeout:
            logger.info("⏰ Conversation timed out")
            self.stop_conversation()
            return False
        
        return True
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation.
        
        Returns:
            Conversation summary
        """
        user_messages = len([m for m in self.conversation_history if m.role == "user"])
        assistant_messages = len([m for m in self.conversation_history if m.role == "assistant"])
        
        duration = None
        if self.session_start_time:
            duration = time.time() - self.session_start_time
        
        return {
            "is_active": self.is_active,
            "session_duration": duration,
            "total_messages": len(self.conversation_history),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "recent_topics": self.context.recent_topics.copy(),
            "context": {
                "meeting_title": self.context.meeting_title,
                "participants": self.context.participants.copy(),
                "agent_name": self.context.agent_name
            }
        }
    
    async def test_all_components(self) -> Dict[str, bool]:
        """Test all AI components.
        
        Returns:
            Test results for each component
        """
        logger.info("🧪 Testing all AI components...")
        
        results = {
            "whisper": False,
            "gpt": False,
            "tts": False
        }
        
        try:
            results["whisper"] = await self.whisper.test_connection()
        except Exception as e:
            logger.error(f"Whisper test failed: {e}")
        
        try:
            results["gpt"] = await self.gpt.test_connection()
        except Exception as e:
            logger.error(f"GPT test failed: {e}")
        
        try:
            results["tts"] = await self.tts.test_connection()
        except Exception as e:
            logger.error(f"TTS test failed: {e}")
        
        all_working = all(results.values())
        if all_working:
            logger.info("✅ All AI components working correctly")
        else:
            logger.warning(f"⚠️ Some components failed: {results}")
        
        return results 

    def _save_audio_to_wav(self, audio_data: np.ndarray, sample_rate: int, file_path: str, amplify: bool = True):
        """Save audio data as WAV file with optional amplification.
        
        Args:
            audio_data: Audio data as numpy array
            sample_rate: Audio sample rate  
            file_path: Output file path
            amplify: Whether to amplify quiet audio
        """
        try:
            # Amplify audio if it's too quiet
            if amplify:
                audio_data = self._amplify_audio(audio_data)
            
            # Ensure audio data is in the right format
            if audio_data.dtype != np.int16:
                # Convert float to int16
                if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
                    audio_data = (audio_data * 32767).astype(np.int16)
                else:
                    audio_data = audio_data.astype(np.int16)
            
            # Write WAV file
            with wave.open(file_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_data.tobytes())
                
        except Exception as e:
            logger.error(f"❌ Failed to save audio as WAV: {e}")
            raise

    def _amplify_audio(self, audio_data: np.ndarray, target_rms: float = 0.1) -> np.ndarray:
        """Amplify audio to target RMS level if it's too quiet.
        
        Args:
            audio_data: Audio data as numpy array
            target_rms: Target RMS level (0.0 to 1.0)
            
        Returns:
            Amplified audio data
        """
        try:
            # Calculate current RMS
            if audio_data.dtype == np.int16:
                audio_float = audio_data.astype(np.float32) / 32767.0
            else:
                audio_float = audio_data.astype(np.float32)
            
            current_rms = np.sqrt(np.mean(audio_float ** 2))
            
            if current_rms > 0.001:  # Only amplify if there's actual audio
                # Calculate amplification factor
                amplification = min(target_rms / current_rms, 10.0)  # Cap at 10x amplification
                
                if amplification > 1.5:  # Only amplify if significantly quiet
                    audio_float = audio_float * amplification
                    
                    # Prevent clipping
                    audio_float = np.clip(audio_float, -1.0, 1.0)
                    
                    logger.info(f"🔊 Audio amplified by {amplification:.1f}x (RMS: {current_rms:.4f} → {np.sqrt(np.mean(audio_float ** 2)):.4f})")
                    
                    return audio_float
            
            return audio_float
            
        except Exception as e:
            logger.warning(f"⚠️ Audio amplification failed: {e}")
            return audio_data

    def set_audio_capture_callback(self, pause_callback: Optional[Callable[[], None]], resume_callback: Optional[Callable[[], None]]):
        """Set callbacks to pause/resume audio capture during TTS playback.
        
        Args:
            pause_callback: Function to pause audio capture
            resume_callback: Function to resume audio capture
        """
        self.pause_audio_capture = pause_callback
        self.resume_audio_capture = resume_callback
        logger.info("🎛️ Audio capture callbacks set for feedback prevention")

    async def _delayed_resume_capture(self):
        """Resume audio capture after a delay to prevent capturing TTS playback."""
        try:
            # Wait for TTS audio to finish playing (estimate based on duration)
            await asyncio.sleep(2.0)  # 2 second delay to ensure TTS playback completes
            
            if hasattr(self, 'resume_audio_capture') and self.resume_audio_capture:
                self.resume_audio_capture()
                logger.info("✅ Audio capture resumed after TTS delay")
        except Exception as e:
            logger.warning(f"⚠️ Error in delayed resume: {e}") 