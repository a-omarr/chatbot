from __future__ import annotations

"""Evaluation metrics for the intent classification model.

Comparing predicted intents against a labeled test set to calculate
accuracy and generate detailed classification reports.
"""

from typing import List
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from .intent_engine import IntentExample, get_model, _training_data

def _get_test_dataset() -> List[IntentExample]:
    """Retrieve the labeled test set. Currently reuses training data as a baseline."""
    # TODO: Implement a separate held-out test dataset in data/test_data.json
    return _training_data()

def run_evaluation() -> None:
    """Execute model evaluation and print results to the console."""
    model = get_model()
    data = _get_test_dataset()

    X = [ex.text for ex in data]
    y_true = [ex.label for ex in data]

    y_pred = model.predict(X)

    print("=== Intent Classifier Performance ===")
    print(f"Total Samples: {len(X)}")
    print(f"Overall Accuracy: {accuracy_score(y_true, y_pred):.4f}")
    print("\nClassification Report:")
    print(classification_report(y_true, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_true, y_pred, labels=model.classes_))

if __name__ == "__main__":
    run_evaluation()
