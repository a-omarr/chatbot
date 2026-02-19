from __future__ import annotations

"""Data collection service for chatbot performance monitoring.

Logs queries that the bot failed to answer correctly for later use in
active learning workflows to improve the model.
"""

import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class FailedExample:
    """Represents a user query that resulted in a low-confidence or incorrect response."""
    text: str
    predicted_intent: str
    language: str
    model_confidence: float
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

def log_failed_example(example: FailedExample) -> None:
    """Save a failed query example to a local JSONL file for future training data updates."""
    # Ensure data directory exists
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    
    file_path = os.path.join(data_dir, "failed_examples.jsonl")
    
    try:
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(example), ensure_ascii=False) + "\n")
        logger.info(f"Logged failed example: {example.text[:30]}...")
    except Exception as e:
        logger.error(f"Failed to log example: {e}")
