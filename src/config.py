import json
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = int(os.getenv('TELEGRAM_CHAT_ID', 0))
TARGET_DATE = os.getenv('TARGET_DATE')
TOTAL_SONGS = int(os.getenv('TOTAL_SONGS', 6))
CHECK_INTERVAL_SECONDS = int(os.getenv('CHECK_INTERVAL_SECONDS', 60))
RSS_URL = os.getenv('RSS_URL', 'https://hugogloss.uol.com.br/feed/')
HOMEPAGE_URL = os.getenv('HOMEPAGE_URL', 'https://hugogloss.uol.com.br/')
_BASE = Path(__file__).parent.parent

with open(_BASE / 'config' / 'musicas.json', encoding='utf-8') as _f:
    MUSICAS = json.load(_f)
