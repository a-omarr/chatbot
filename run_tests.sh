#!/bin/bash

# Configuration
PROJECT_ROOT=$(pwd)
BACKEND_DIR="$PROJECT_ROOT/backend"
VENV_PATH="$BACKEND_DIR/.venv"

echo "===================================================="
echo "    Toros Yazilim Chatbot - Test Runner"
echo "===================================================="

# 1. Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Error: Virtual environment not found at $VENV_PATH"
    echo "Please run the setup first or update the VENV_PATH in this script."
    exit 1
fi

# 2. Run Unit/Integration Tests (Pytest)
echo -e "\n\033[1m[1/2] Running Unit & Intent Prediction Tests (Pytest)...\033[0m"
PYTHONPATH=$PROJECT_ROOT:$BACKEND_DIR $VENV_PATH/bin/pytest $BACKEND_DIR/tests/test_bot_scenarios.py -v

PYTEST_STATUS=$?

# 3. Run Multilingual System Tests
echo -e "\n\033[1m[2/2] Running Multilingual System Tests (Exhaustive)...\033[0m"
PYTHONPATH=$PROJECT_ROOT $VENV_PATH/bin/python $BACKEND_DIR/tests/system_test.py

SYSTEM_TEST_STATUS=$?

echo -e "\n===================================================="
if [ $PYTEST_STATUS -eq 0 ] && [ $SYSTEM_TEST_STATUS -eq 0 ]; then
    echo -e "✅ \033[92mALL TESTS PASSED SUCCESSFULLY!\033[0m"
    exit 0
else
    echo -e "❌ \033[91mSOME TESTS FAILED. Please review the logs above.\033[0m"
    exit 1
fi
echo "===================================================="
