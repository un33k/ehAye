"""Chat interface and conversation management."""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..core.config import get_config
from ..core.logging import get_logger
from .generation import GenerationConfig, generate_text, generate_text_stream
from .prompts import format_conversation, format_prompt

logger = get_logger("llm.chat")


class Conversation:
    """Represents a chat conversation."""
    
    def __init__(
        self,
        conversation_id: Optional[str] = None,
        system_prompt: Optional[str] = None
    ):
        self.conversation_id = conversation_id or self._generate_id()
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = []
        self.created_at = None
        self.updated_at = None
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation."""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": self._get_timestamp()
        })
        self.updated_at = self._get_timestamp()
    
    def add_user_message(self, content: str) -> None:
        """Add a user message."""
        self.add_message("user", content)
    
    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message."""
        self.add_message("assistant", content)
    
    def get_context_messages(self, max_messages: Optional[int] = None) -> List[Dict[str, str]]:
        """Get messages for context (excluding timestamps)."""
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages
        ]
        
        if max_messages:
            return messages[-max_messages:]
        return messages
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        return {
            "conversation_id": self.conversation_id,
            "system_prompt": self.system_prompt,
            "messages": self.messages,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Conversation":
        """Create from dictionary."""
        conv = cls(
            conversation_id=data["conversation_id"],
            system_prompt=data.get("system_prompt")
        )
        conv.messages = data.get("messages", [])
        conv.created_at = data.get("created_at")
        conv.updated_at = data.get("updated_at")
        return conv
    
    def _generate_id(self) -> str:
        """Generate unique conversation ID."""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


class ChatSession:
    """Manages a chat session with model interaction."""
    
    def __init__(
        self,
        model_id: str,
        generation_config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None
    ):
        self.model_id = model_id
        self.generation_config = generation_config or GenerationConfig()
        self.conversation = Conversation(system_prompt=system_prompt)
        self.config = get_config()
    
    def send_message(self, message: str, streaming: bool = False) -> str:
        """Send a message and get response."""
        # Add user message
        self.conversation.add_user_message(message)
        
        # Format prompt
        if len(self.conversation.messages) == 1 and not self.conversation.system_prompt:
            # Single message, use simple format
            prompt = format_prompt(message, self.model_id)
        else:
            # Multi-turn conversation
            context_messages = self.conversation.get_context_messages()
            prompt = format_conversation(
                context_messages, 
                self.model_id, 
                self.conversation.system_prompt
            )
        
        # Generate response
        if streaming:
            response_stream = generate_text_stream(
                prompt, 
                self.model_id, 
                self.generation_config
            )
            # For streaming, we need to collect the response
            response = ""
            for chunk in response_stream:
                response += chunk
                yield chunk
        else:
            response = generate_text(prompt, self.model_id, self.generation_config)
        
        # Add assistant response
        self.conversation.add_assistant_message(response)
        
        if not streaming:
            return response
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation.get_context_messages()
    
    def clear_conversation(self) -> None:
        """Clear conversation history."""
        system_prompt = self.conversation.system_prompt
        self.conversation = Conversation(system_prompt=system_prompt)
    
    def save_conversation(self) -> bool:
        """Save conversation to file."""
        if not self.config.chat.save_conversations:
            return False
        
        try:
            conversations_dir = self.config.paths.config_dir / "conversations"
            conversations_dir.mkdir(exist_ok=True)
            
            file_path = conversations_dir / f"{self.conversation.conversation_id}.json"
            
            with open(file_path, 'w') as f:
                json.dump(self.conversation.to_dict(), f, indent=2)
            
            logger.debug(f"Saved conversation to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save conversation: {e}")
            return False
    
    def load_conversation(self, conversation_id: str) -> bool:
        """Load conversation from file."""
        try:
            conversations_dir = self.config.paths.config_dir / "conversations"
            file_path = conversations_dir / f"{conversation_id}.json"
            
            if not file_path.exists():
                return False
            
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            self.conversation = Conversation.from_dict(data)
            logger.debug(f"Loaded conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load conversation: {e}")
            return False


class ChatManager:
    """Manages multiple chat sessions and conversations."""
    
    def __init__(self):
        self.config = get_config()
        self.active_sessions: Dict[str, ChatSession] = {}
    
    def create_session(
        self,
        model_id: str,
        session_id: Optional[str] = None,
        generation_config: Optional[GenerationConfig] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """Create a new chat session."""
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())[:8]
        
        session = ChatSession(
            model_id=model_id,
            generation_config=generation_config,
            system_prompt=system_prompt
        )
        
        self.active_sessions[session_id] = session
        logger.debug(f"Created chat session {session_id} with model {model_id}")
        
        return session_id
    
    def get_session(self, session_id: str) -> Optional[ChatSession]:
        """Get an active session."""
        return self.active_sessions.get(session_id)
    
    def close_session(self, session_id: str, save: bool = True) -> bool:
        """Close a session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
        
        if save:
            session.save_conversation()
        
        del self.active_sessions[session_id]
        logger.debug(f"Closed session {session_id}")
        return True
    
    def list_conversations(self) -> List[Dict[str, str]]:
        """List saved conversations."""
        conversations = []
        
        try:
            conversations_dir = self.config.paths.config_dir / "conversations"
            
            if not conversations_dir.exists():
                return conversations
            
            for file_path in conversations_dir.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    conversations.append({
                        "id": data["conversation_id"],
                        "created_at": data.get("created_at", "Unknown"),
                        "updated_at": data.get("updated_at", "Unknown"),
                        "message_count": len(data.get("messages", [])),
                        "has_system_prompt": bool(data.get("system_prompt"))
                    })
                    
                except Exception as e:
                    logger.error(f"Error reading conversation {file_path}: {e}")
            
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
        
        return sorted(conversations, key=lambda x: x["updated_at"], reverse=True)


# Global chat manager
chat_manager = ChatManager()


def create_chat_session(
    model_id: str,
    generation_config: Optional[GenerationConfig] = None,
    system_prompt: Optional[str] = None
) -> str:
    """Create a new chat session."""
    return chat_manager.create_session(model_id, None, generation_config, system_prompt)


def get_chat_session(session_id: str) -> Optional[ChatSession]:
    """Get a chat session."""
    return chat_manager.get_session(session_id)