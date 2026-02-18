# Toros Yazilim Chatbot - Testing Workflow & Quality Assurance

This document outlines the comprehensive testing strategy, tools, and workflows implemented to ensure the reliability and accuracy of the multilingual chatbot.

---

## 1. Testing Strategy

Our testing approach is divided into three layers to cover all aspects of the bot's behavior:

| Layer | Focus | Tool |
|-------|-------|------|
| **Unit Tests** | Individual ML model predictions and logic functions | `pytest` |
| **Integration Tests** | API endpoint responses and language mismatch logic | `pytest` |
| **System Tests** | Exhaustive multilingual sanity checks for all KB topics | `system_test.py` |

---

## 2. Test Components

### 2.1 Intent Classifier Validation
The `backend/tests/test_bot_scenarios.py` file contains the logic to verify that the intent classifier correctly identifies user inquiries with high confidence. It tests:
- **Keyword Overlap**: Ensuring "Who is..." correctly predicts `company_overview`.
- **Multilingual Support**: Verification that the model handles TR, AR, and RU characters accurately.
- **Confidence Thresholds**: Ensuring the model hits at least 10% confidence for trained topics.

### 2.2 API Flow Validation
Tests the `POST /api/v1/bot/chat` endpoint to ensure:
- Dynamic language detection works when no hint is provided.
- **Language Mismatch Warning** is generated when the user types in a language different from the UI selection.
- Safe fallbacks are used for nonsensical input.

### 2.3 Exhaustive Multilingual System Tests
The `backend/tests/system_test.py` script performs a full scan of the knowledge base across all 4 languages. It simulates a user asking about:
- Company history and mission.
- Products (KIYOS, AuthNAC, SIEM).
- Services (IT Consultancy, Custom Software).
- Human Resources (Jobs, Internships).
- Contact Info (Phone, Office location).

---

## 3. Running All Tests

A unified test runner is provided at the project root for ease of use.

### Prerequisites
Ensure your backend virtual environment is set up and dependencies are installed.

### Execution
```bash
chmod +x run_tests.sh
./run_tests.sh
```

This script will sequentially run:
1. `pytest` for unit and integration logic.
2. `system_test.py` for comprehensive multilingual verification.

---

## 4. Active Learning Workflow

When the bot encounters a message it cannot resolve with high confidence, it enters the **Active Learning Loop**:

1. **Failure Logging**: The query is logged to `backend/app/data/failed_examples.jsonl`.
2. **Review**: Developers review these logs to identify new user needs or model weaknesses.
3. **Training Update**: New examples are added to `backend/app/ml/intent_classifier.py`.
4. **Retraining**: The model is automatically retrained on the next startup.

---

## 5. Summary of System Coverage

| Language | Test Cases | Target Pass Rate |
|----------|------------|------------------|
| English (EN) | 11 | 100% |
| Turkish (TR) | 13 | 100% |
| Arabic (AR) | 7 | 100% |
| Russian (RU) | 6 | 100% |
| **Total** | **37** | **100%** |

*Last tested: February 18, 2026*
