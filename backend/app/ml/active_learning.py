from __future__ import annotations

"""Skeleton utilities for active learning.

The idea:
- when the bot falls back to a low‑quality reply (e.g. echo), log the
  question + current prediction into a JSONL file
- later, a human labels the correct intent (and optionally the answer)
- you merge those examples back into the training data and retrain

This file only defines helper functions and logging locations; wiring it
fully into the API is left light so you can adapt it to your ops setup.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Literal


FeedbackIntent = Literal[
    "company_overview",
    "services",
    "products",
    "contact",
    "employees",
    "other",
]


@dataclass
class FailedExample:
    text: str
    predicted_intent: str
    language: str
    model_confidence: float


ACTIVE_LEARNING_DIR = Path(__file__).resolve().parent.parent / "data"
ACTIVE_LEARNING_FILE = ACTIVE_LEARNING_DIR / "failed_examples.jsonl"


def log_failed_example(example: FailedExample) -> None:
    ACTIVE_LEARNING_DIR.mkdir(parents=True, exist_ok=True)
    with ACTIVE_LEARNING_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(example), ensure_ascii=False) + "\n")


# In a more complete system you would also add helpers such as:
# - load_failed_examples()
# - export_for_labeling()
# - merge_labeled_feedback_into_dataset()
