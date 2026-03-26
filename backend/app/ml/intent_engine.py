from __future__ import annotations

"""Intent classification engine for the Toros Yazilim chatbot.

This module handles the training and prediction of user intents using 
a TF-IDF vectorizer and Logistic Regression classifier.
"""

import logging
from dataclasses import dataclass
from typing import List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from app.core.loader import get_training_data, get_config

logger = logging.getLogger(__name__)

@dataclass
class IntentExample:
    """A single training example with text and its corresponding intent label."""
    text: str
    label: str

def _load_training_examples() -> List[IntentExample]:
    """Load and parse training examples from JSON data."""
    raw_data = get_training_data()
    return [IntentExample(text=ex["text"], label=ex["label"]) for ex in raw_data]

def _get_intent_labels() -> List[str]:
    """Retrieve the list of supported intent labels from configuration."""
    # We could also derive these from training data, but config is safer
    config = get_config()
    # If config doesn't have it, we can fallback to a fixed list or derived list
    return config.get("intent_labels", [
        "company_overview", "services", "products", "contact_info", 
        "employees", "cybersecurity", "business_clients", "public_sector", 
        "career_info", "greeting", "makscyber_siem", "authnac_info", 
        "identity_management", "custom_software", "it_consultancy", 
        "kiyos_features", "ari_konaklama", "personal_data_protection", 
        "privacy_policy", "user_agreement", "info_security_policy", 
        "references", "research_development", "sales_team", "request_demo", 
        "phone_number", "other"
    ])

def build_pipeline() -> Pipeline:
    """Initialize the machine learning pipeline (TF-IDF + Logistic Regression)."""
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 5),
        min_df=1,
    )
    clf = LogisticRegression(
        max_iter=200, 
        multi_class="auto", 
        class_weight="balanced"
    )
    return Pipeline([("vec", vectorizer), ("clf", clf)])

# Global model instance for lazy loading
_MODEL: Pipeline | None = None

def train_model() -> Pipeline:
    """Train the intent classification model using the current training data."""
    global _MODEL
    
    logger.info("Training intent classification model...")
    examples = _load_training_examples()
    X = [ex.text for ex in examples]
    y = [ex.label for ex in examples]

    model = build_pipeline()
    model.fit(X, y)

    _MODEL = model
    logger.info(f"Model trained successfully with {len(examples)} examples.")
    return model

def get_model() -> Pipeline:
    """Get the trained model, training it first if necessary."""
    global _MODEL
    if _MODEL is None:
        _MODEL = train_model()
    return _MODEL

def predict_intent(text: str) -> Tuple[str, float]:
    """Predict the intent and confidence score for a given user message."""
    results = predict_top_k(text, k=1)
    return results[0]

def predict_top_k(text: str, k: int = 2) -> List[Tuple[str, float]]:
    """Predict the top K intents and their confidence scores."""
    model = get_model()
    proba = model.predict_proba([text])[0]
    
    # Get indices of top K probabilities
    top_indices = proba.argsort()[-k:][::-1]
    
    results = []
    for idx in top_indices:
        label = str(model.classes_[idx])
        score = float(proba[idx])
        results.append((label, score))
        
    return results

def debug_intent(text: str) -> None:
    """Print detailed prediction probabilities for debugging purposes."""
    model = get_model()
    proba = model.predict_proba([text])[0]
    print(f"Debug results for: '{text}'")
    for label, p in zip(model.classes_, proba):
        print(f"  {label:25s}: {p:.3f}")

# Expose IntentExample for external use (e.g. testing)
_training_data = _load_training_examples
