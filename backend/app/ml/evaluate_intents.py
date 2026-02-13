from __future__ import annotations

"""Offline evaluation script for the intent classifier.

Run with:

    cd backend
    python -m app.ml.evaluate_intents

This prints accuracy and a confusion matrix over a small labeled test set.
Extend TEST_SET with more real queries as you collect them.
"""

from typing import List, Tuple

from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from .intent_classifier import IntentExample, get_model, _training_data


def _test_set() -> List[IntentExample]:
    # For now we just reuse the training data to demonstrate the pipeline.
    # In a real project you would keep a separate held‑out test set.
    return _training_data()


def main() -> None:
    model = get_model()
    data = _test_set()

    X = [ex.text for ex in data]
    y_true = [ex.label for ex in data]

    y_pred = model.predict(X)

    print("Accuracy:", accuracy_score(y_true, y_pred))
    print()
    print("Classification report:")
    print(classification_report(y_true, y_pred))

    print("Confusion matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_true, y_pred, labels=model.classes_))


if __name__ == "__main__":  # pragma: no cover
    main()
