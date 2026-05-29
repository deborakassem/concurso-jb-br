import logging

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


def get_article_links(homepage_url: str) -> list[str]:
    logger.info(f'Checando homepage: {homepage_url}')
    try:
        resp = requests.get(homepage_url, headers=_HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        logger.error(f'Erro ao acessar homepage: {e}')
        return []

    soup = BeautifulSoup(resp.text, 'html.parser')
    seen: set[str] = set()
    links: list[str] = []

    for a in soup.find_all('a', href=True):
        href: str = a['href']
        if (
            href.startswith('http')
            and 'hugogloss.uol.com.br' in href
            and '?' not in href
            and '#' not in href
            and href not in seen
        ):
            seen.add(href)
            links.append(href)

    logger.debug(f'Homepage: {len(links)} links coletados')
    return links
