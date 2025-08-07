import json
import hashlib
import os

def load_data(filename):
    try:
        with open(f"data/{filename}.json", "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(filename, data):
    os.makedirs("data", exist_ok=True)
    with open(f"data/{filename}.json", "w") as f:
        json.dump(data, f)

def get_subject_color(subject):
    """Generate a consistent color for each subject"""
    color_hash = hashlib.md5(subject.encode()).hexdigest()[:6]
    return f"#{color_hash}"