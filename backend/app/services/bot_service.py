from __future__ import annotations

from typing import Final


class BotService:
    """Service layer for chatbot logic.

    This keeps HTTP/transport concerns out of your core logic so
    it can be reused from REST, websockets, CLI, workers, etc.
    """

    DEFAULT_PREFIX: Final[str] = "You said: "

    def generate_reply(self, message: str) -> str:
        """Generate a bot reply for the given message.

        Replace this placeholder with calls to an LLM, rules engine,
        or any other business logic.
        """
        cleaned = message.strip()
        # Simple deterministic placeholder behavior
        return f"{self.DEFAULT_PREFIX}{cleaned}"


bot_service = BotService()
