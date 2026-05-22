"""Conversation manager — session-based memory for multi-turn RAG conversations."""

from datetime import datetime
from typing import Optional

from loguru import logger


class ConversationManager:
    """Manage per-session LangChain conversation memory.

    Each session is identified by a session_id string and maintains
    an independent ConversationBufferWindowMemory.
    """

    def __init__(self, config: dict) -> None:
        """Initialise from config dict.

        Args:
            config: Full application config dict.
        """
        self.config = config
        conv_cfg = config.get("conversation", {})
        self.window_size: int = conv_cfg.get("window_size", 10)
        self.max_history: int = conv_cfg.get("max_history", 50)
        self.return_messages: bool = conv_cfg.get("return_messages", True)

        # session_id → {memory, created_at, message_count}
        self._sessions: dict[str, dict] = {}

    # ─────────────────────────────────────────────────────────────────────────
    # Session lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def create_session(self, session_id: str):
        """Create a new conversation session.

        Args:
            session_id: Unique identifier for the session.

        Returns:
            LangChain ConversationBufferWindowMemory object.
        """
        from langchain.memory import ConversationBufferWindowMemory

        memory = ConversationBufferWindowMemory(
            k=self.window_size,
            memory_key="chat_history",
            return_messages=self.return_messages,
            output_key="answer",
        )
        self._sessions[session_id] = {
            "memory": memory,
            "created_at": datetime.now().isoformat(),
            "message_count": 0,
            "last_active": datetime.now().isoformat(),
            "sources_used": [],
        }
        logger.debug(f"Created session: {session_id}")
        return memory

    def get_session(self, session_id: str):
        """Get or create a session memory object.

        Args:
            session_id: Session identifier.

        Returns:
            LangChain memory object for this session.
        """
        if session_id not in self._sessions:
            return self.create_session(session_id)
        return self._sessions[session_id]["memory"]

    def get_memory_object(self, session_id: str):
        """Return the raw LangChain memory object.

        Args:
            session_id: Session identifier.

        Returns:
            ConversationBufferWindowMemory instance.
        """
        return self.get_session(session_id)

    # ─────────────────────────────────────────────────────────────────────────
    # Message management
    # ─────────────────────────────────────────────────────────────────────────

    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Manually add a message to a session's history.

        Args:
            session_id: Session identifier.
            role: 'human' or 'ai'.
            content: Message text.
        """
        session = self._sessions.get(session_id)
        if session is None:
            self.create_session(session_id)
            session = self._sessions[session_id]

        memory = session["memory"]
        if role == "human":
            memory.chat_memory.add_user_message(content)
        else:
            memory.chat_memory.add_ai_message(content)

        session["message_count"] += 1
        session["last_active"] = datetime.now().isoformat()

    def get_history(self, session_id: str) -> list[dict]:
        """Return formatted conversation history.

        Args:
            session_id: Session identifier.

        Returns:
            List of {role, content, timestamp} dicts.
        """
        session = self._sessions.get(session_id)
        if not session:
            return []

        messages = session["memory"].chat_memory.messages
        history = []
        for msg in messages:
            role = "human" if msg.type == "human" else "ai"
            history.append({"role": role, "content": msg.content})
        return history

    def add_source_to_session(self, session_id: str, source: str) -> None:
        """Track which source documents were referenced in this session."""
        session = self._sessions.get(session_id)
        if session and source not in session["sources_used"]:
            session["sources_used"].append(source)

    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session.

        Args:
            session_id: Session identifier.
        """
        if session_id in self._sessions:
            self._sessions[session_id]["memory"].clear()
            self._sessions[session_id]["message_count"] = 0
            logger.debug(f"Cleared session: {session_id}")

    def delete_session(self, session_id: str) -> None:
        """Fully remove a session from memory."""
        self._sessions.pop(session_id, None)
        logger.debug(f"Deleted session: {session_id}")

    def list_sessions(self) -> list[str]:
        """Return all active session IDs."""
        return list(self._sessions.keys())

    # ─────────────────────────────────────────────────────────────────────────
    # Export & stats
    # ─────────────────────────────────────────────────────────────────────────

    def export_session(self, session_id: str) -> dict:
        """Export a session as a structured dict.

        Args:
            session_id: Session identifier.

        Returns:
            Dict with messages, timestamps, and metadata.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {"error": f"Session '{session_id}' not found."}

        return {
            "session_id": session_id,
            "created_at": session["created_at"],
            "last_active": session["last_active"],
            "message_count": session["message_count"],
            "sources_used": session["sources_used"],
            "messages": self.get_history(session_id),
        }

    def get_session_stats(self, session_id: str) -> dict:
        """Return statistics for a session.

        Args:
            session_id: Session identifier.

        Returns:
            Stats dict with message count, duration, and avg response length.
        """
        session = self._sessions.get(session_id)
        if not session:
            return {}

        messages = self.get_history(session_id)
        ai_messages = [m["content"] for m in messages if m["role"] == "ai"]
        avg_len = int(sum(len(m) for m in ai_messages) / len(ai_messages)) if ai_messages else 0

        created = datetime.fromisoformat(session["created_at"])
        duration_s = (datetime.now() - created).total_seconds()

        return {
            "session_id": session_id,
            "message_count": session["message_count"],
            "questions_asked": len(ai_messages),
            "avg_response_length": avg_len,
            "session_duration_s": round(duration_s),
            "sources_used": session["sources_used"],
            "created_at": session["created_at"],
        }
