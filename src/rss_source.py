import logging
from datetime import datetime

import feedparser

logger = logging.getLogger(__name__)


def get_articles(rss_url: str, target_date: str) -> list[dict]:
    logger.info(f'Checando RSS: {rss_url}')
    logger.debug(f'Parsing RSS: {rss_url}')
    try:
        feed = feedparser.parse(rss_url)
    except Exception as e:
        logger.error(f'Erro ao parsear RSS: {e}')
        return []

    articles = []
    for entry in feed.entries:
        try:
            dt = datetime(*entry.published_parsed[:6])
            if str(dt.date()) == target_date:
                articles.append({
                    'url': entry.link,
                    'titulo': entry.title,
                    'hora': dt.strftime('%H:%M'),
                })
        except Exception:
            continue

    logger.debug(f'RSS: {len(articles)} artigos encontrados na data {target_date}')
    return articles
