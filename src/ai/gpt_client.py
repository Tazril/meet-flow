"""Azure OpenAI GPT client for conversational AI responses."""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from openai import AsyncAzureOpenAI
    from openai.types.chat import ChatCompletionMessageParam
except ImportError:
    AsyncAzureOpenAI = None
    ChatCompletionMessageParam = Any

from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger("ai.gpt")

class GPTClient:
    """Simplified Azure OpenAI GPT client for conversation."""
    
    def __init__(self):
        """Initialize GPT client with Azure OpenAI."""
        if AsyncAzureOpenAI is None:
            raise ImportError("openai package is required. Install with: pip install openai")
        
        # Get config
        config = Config.get_gpt_config()
        
        if not config["azure_endpoint"] or not config["api_key"]:
            raise ValueError("Azure OpenAI endpoint and API key are required")
        
        # Initialize Azure OpenAI client
        self.client = AsyncAzureOpenAI(
            azure_endpoint=config["azure_endpoint"],
            api_key=config["api_key"],
            api_version=config["api_version"]
        )
        
        self.deployment = config["deployment_name"]
        self.max_tokens = config["max_tokens"]
        self.temperature = config["temperature"]
        
        # Conversation context
        self.conversation_history: List[Dict[str, Any]] = []
        self.agent_name = Config.AGENT_NAME
        
        logger.info(f"🧠 GPT client initialized (deployment: {self.deployment})")
    
    async def generate_response(self, 
                              user_input: str,
                              context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate conversational response.
        
        Args:
            user_input: User's message
            context: Additional context
            
        Returns:
            Generated response or None if failed
        """
        try:
            # Build conversation messages
            messages = self._build_conversation_messages(user_input, context)
            
            logger.info(f"💭 Generating response for: {user_input[:50]}...")
            
            # Generate response
            response = await self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,  # type: ignore
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            if not response.choices:
                logger.warning("No response choices returned")
                return None
            
            response_text = response.choices[0].message.content
            if not response_text:
                logger.warning("Empty response generated")
                return None
            
            # Add to conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_input,
                "timestamp": datetime.now()
            })
            self.conversation_history.append({
                "role": "assistant", 
                "content": response_text,
                "timestamp": datetime.now()
            })
            
            # Keep history manageable
            if len(self.conversation_history) > Config.MAX_CONVERSATION_HISTORY * 2:
                self.conversation_history = self.conversation_history[-Config.MAX_CONVERSATION_HISTORY:]
            
            logger.info(f"✅ Response generated: {len(response_text)} chars")
            return response_text.strip()
            
        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            return None
    
    def should_respond(self, text: str, context: Optional[Dict[str, Any]] = None) -> bool:
        """Determine if agent should respond to the text.
        
        Args:
            text: Input text to analyze
            context: Additional context
            
        Returns:
            True if agent should respond
        """
        if not text.strip():
            return False
        
        text_lower = text.lower()
        agent_name_lower = self.agent_name.lower()
        
        # Respond if directly mentioned
        if agent_name_lower in text_lower:
            return True
        
        # Respond to questions
        question_indicators = ["?", "what", "how", "why", "when", "where", "who", "can you"]
        if any(indicator in text_lower for indicator in question_indicators):
            return True
        
        # Respond to greetings
        greetings = ["hello", "hi", "hey", "good morning", "good afternoon"]
        if any(greeting in text_lower for greeting in greetings):
            return True
        
        # Don't respond to very short messages unless they're greetings
        if len(text.split()) < 3:
            return False
        
        return True
    
    def _build_conversation_messages(self, 
                                   user_input: str, 
                                   context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Build conversation messages for the API."""
        messages = []
        
        # System message
        system_prompt = f"""You are {self.agent_name}, an AI assistant in a Google Meet call.

Guidelines:
- Keep responses short and conversational (1-2 sentences max)
- Be helpful and natural
- Respond as if you're speaking in a meeting
- Don't mention that you're an AI unless asked directly

Meeting context: Professional discussion"""
        
        if context:
            if context.get("meeting_topic"):
                system_prompt += f"\nMeeting topic: {context['meeting_topic']}"
            if context.get("participants"):
                system_prompt += f"\nParticipants: {', '.join(context['participants'])}"
        
        messages.append({"role": "system", "content": system_prompt})
        
        # Add recent conversation history
        recent_history = self.conversation_history[-6:] if self.conversation_history else []
        for msg in recent_history:
            if msg["role"] in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user input
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    async def test_connection(self) -> bool:
        """Test connection to Azure OpenAI."""
        try:
            test_response = await self.generate_response("Hello, can you hear me?")
            if test_response:
                logger.info("✅ GPT connection test successful")
                return True
            else:
                logger.warning("⚠️ GPT connection test returned no response")
                return False
        except Exception as e:
            logger.error(f"❌ GPT connection test failed: {e}")
            return False
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        logger.info("🗑️ Conversation history cleared")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation."""
        user_messages = sum(1 for msg in self.conversation_history if msg["role"] == "user")
        assistant_messages = sum(1 for msg in self.conversation_history if msg["role"] == "assistant")
        
        return {
            "total_messages": len(self.conversation_history),
            "user_messages": user_messages,
            "assistant_messages": assistant_messages,
            "last_activity": self.conversation_history[-1]["timestamp"] if self.conversation_history else None
        }
    
    async def close(self):
        """Close the client connection."""
        await self.client.close()
        logger.info("GPT client closed")
    
    async def generate_response_async(self, 
                                    conversation: List[Dict[str, Any]],
                                    context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Generate response from conversation history (async version for backwards compatibility).
        
        Args:
            conversation: List of conversation messages
            context: Additional context
            
        Returns:
            Generated response or None if failed
        """
        if not conversation:
            return None
        
        # Get the last user message
        last_message = conversation[-1]
        if last_message.get("role") == "user":
            user_input = last_message.get("content", "")
            return await self.generate_response(user_input, context)
        
        return None
    
    async def should_respond_async(self, 
                                 text: str, 
                                 conversation: List[Dict[str, Any]],
                                 context: Optional[Dict[str, Any]] = None) -> bool:
        """Determine if agent should respond (async version for backwards compatibility).
        
        Args:
            text: Input text to analyze
            conversation: Conversation history (for context)
            context: Additional context
            
        Returns:
            True if agent should respond
        """
        # Use the synchronous version - no need for async here
        return self.should_respond(text, context) 