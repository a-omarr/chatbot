from __future__ import annotations

import time
import logging
from collections import deque
from dataclasses import dataclass, field
from typing import Dict, List

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    role: str  # "user" or "assistant"
    content: str

@dataclass
class ChatSession:
    history: deque[ConversationTurn] = field(default_factory=lambda: deque(maxlen=5))
    last_accessed: float = field(default_factory=time.time)

class MemoryStore:
    """In-memory store for chat history sessions."""
    
    def __init__(self, ttl_seconds: int = 1800):
        self._sessions: Dict[str, ChatSession] = {}
        self._ttl = ttl_seconds

    def _cleanup_expired(self) -> None:
        """Remove sessions that haven't been accessed in a while."""
        now = time.time()
        expired_ids = [
            sid for sid, session in self._sessions.items()
            if now - session.last_accessed > self._ttl
        ]
        for sid in expired_ids:
            del self._sessions[sid]
            logger.debug(f"MemoryStore: session {sid} expired.")

    def get_history(self, session_id: str) -> List[dict]:
        """Retrieve recent conversation turns for a session."""
        self._cleanup_expired()
        
        if session_id not in self._sessions:
            return []
        
        session = self._sessions[session_id]
        session.last_accessed = time.time()
        return [{"role": turn.role, "content": turn.content} for turn in session.history]

    def add_turn(self, session_id: str, role: str, content: str) -> None:
        """Append a new turn (user/assistant) to the session history."""
        if not session_id:
            return
            
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatSession()
            
        session = self._sessions[session_id]
        session.history.append(ConversationTurn(role=role, content=content))
        session.last_accessed = time.time()
        
        logger.debug(f"MemoryStore: added {role} turn to session {session_id}.")

# Singleton store instance
memory_store = MemoryStore()
