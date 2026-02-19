
import json
import os
from typing import Any

def load_json_data(filename: str) -> Any:
    """Load JSON data from the app/data directory."""
    # Base path relative to this file: backend/app/core/loader.py
    # Data path: backend/app/data/
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_path = os.path.join(base_dir, "data", filename)
    
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
        
    with open(data_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_config() -> dict:
    return load_json_data("config.json")

def get_knowledge_base() -> dict:
    return load_json_data("knowledge_base.json")

def get_training_data() -> list:
    return load_json_data("training_data.json")
