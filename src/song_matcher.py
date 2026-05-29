import re
import unicodedata


def normalize(text: str) -> str:
    text = str(text).lower()
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-z0-9]', '', text)
    return text


def find_matches(hashtags: list[str], musicas: list[dict]) -> list[dict]:
    normalized = {normalize(h) for h in hashtags}
    return [m for m in musicas if normalize(m['hashtag']) in normalized]
