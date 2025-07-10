import os
import json
from datetime import datetime

def save_chat_to_history(prompt, response, history_file="history/chat_history.json"):
    os.makedirs(os.path.dirname(history_file), exist_ok=True)
    full_path = history_file


    if os.path.exists(full_path):
        with open(full_path, "r") as f:
            history = json.load(f)
    else:
        history = []

    history.append({
        "timestamp": datetime.now().isoformat(),
        "prompt": prompt,
        "response": response
    })

    with open(full_path, "w") as f:
        json.dump(history, f, indent=4)

    return full_path
