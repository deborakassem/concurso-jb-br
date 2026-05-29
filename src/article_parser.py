import logging
import re
import unicodedata

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    )
}


def normalize_hashtag(tag: str) -> str:
    tag = tag.lower()
    tag = unicodedata.normalize('NFD', tag)
    tag = ''.join(c for c in tag if unicodedata.category(c) != 'Mn')
    tag = re.sub(r'[^a-z0-9]', '', tag)
    return tag


def parse_article(url: str) -> dict | None:
    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.warning(f'Erro ao baixar artigo {url}: {e}')
        return None

    soup = BeautifulSoup(resp.text, 'html.parser')

    title = ''
    og_title = soup.find('meta', property='og:title')
    if og_title:
        title = og_title.get('content', '')
    elif soup.title:
        title = soup.title.string or ''

    hora = ''
    for attr in ('article:published_time', 'og:article:published_time'):
        pub = soup.find('meta', property=attr) or soup.find('meta', attrs={'name': attr})
        if pub:
            content = pub.get('content', '')
            if 'T' in content:
                hora = content.split('T')[1][:5]
            break
    if not hora:
        time_tag = soup.find('time', attrs={'datetime': True})
        if time_tag:
            dt = time_tag['datetime']
            if 'T' in dt:
                hora = dt.split('T')[1][:5]

    body = (
        soup.find('div', class_='entry-content')
        or soup.find('article')
        or soup.find('main')
        or soup.body
    )
    text = body.get_text(' ', strip=True) if body else soup.get_text(' ', strip=True)

    raw_tags = re.findall(r'#(\w+)', text)
    hashtags = list({normalize_hashtag(t) for t in raw_tags if t})

    logger.info(f'Hashtags extraídas ({len(hashtags)}): {hashtags}')
    return {'titulo': title, 'hora': hora, 'hashtags': hashtags}
