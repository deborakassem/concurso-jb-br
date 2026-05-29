import json
import os

STATE_FILE = 'data/state.json'


def _default():
    return {'urls_vistas': [], 'musicas': []}


def load_sync():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    return _default()


def save_sync(state):
    os.makedirs('data', exist_ok=True)
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
