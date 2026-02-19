"""Root conftest.py – ensures the backend/ directory is on sys.path.

This allows pytest (when run from the repo root or from backend/) to resolve
`app.*` and `api.*` imports without installing the package.
"""
import sys
import os

# Insert backend/ directory at the front of the search path so that
# `from app.xxx` and `from api.xxx` work in all test modules.
sys.path.insert(0, os.path.dirname(__file__))
