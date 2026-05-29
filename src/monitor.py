import asyncio
import logging
from datetime import datetime
from typing import Callable, Awaitable

from . import config, state, article_parser, song_matcher, rss_source, homepage_source

logger = logging.getLogger(__name__)


async def run(
    notify_song: Callable[[dict, int], Awaitable[None]],
    notify_all_found: Callable[[list[dict]], Awaitable[None]],
    notify_article: Callable[[str, str, str, list[str], dict | None], Awaitable[None]],
    stop_event: asyncio.Event,
) -> None:
    logger.info(
        f'Monitor iniciado. Intervalo: {config.CHECK_INTERVAL_SECONDS}s | Data alvo: {config.TARGET_DATE}'
    )

    while not stop_event.is_set():
        try:
            done = await _check_once(notify_song, notify_all_found, notify_article)
            if done:
                break
        except Exception as e:
            logger.error(f'Erro no monitor: {e}')

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=config.CHECK_INTERVAL_SECONDS)
            break
        except asyncio.TimeoutError:
            pass

    logger.info('Loop encerrado.')


async def _check_once(notify_song, notify_all_found, notify_article) -> bool:
    current = state.load_sync()

    if current.get('enviado') or current.get('cancelado'):
        return True

    urls_vistas: set[str] = set(current['urls_vistas'])
    musicas_encontradas: list[dict] = current['musicas']
    hashtags_encontradas: set[str] = {m['hashtag'] for m in musicas_encontradas}

    novos_rss = await asyncio.to_thread(rss_source.get_articles, config.RSS_URL, config.TARGET_DATE)
    homepage_links = await asyncio.to_thread(homepage_source.get_article_links, config.HOMEPAGE_URL)

    # (url, titulo_hint, hora_hint, verbose)
    queue: list[tuple[str, str | None, str | None, bool]] = []
    for artigo in novos_rss:
        if artigo['url'] not in urls_vistas:
            queue.append((artigo['url'], artigo['titulo'], artigo['hora'], True))
    for link in homepage_links:
        if link not in urls_vistas:
            queue.append((link, None, None, False))

    for url, titulo_hint, hora_hint, verbose in queue:
        if url in urls_vistas:
            continue
        urls_vistas.add(url)
        current['urls_vistas'] = list(urls_vistas)
        state.save_sync(current)

        parsed = await asyncio.to_thread(article_parser.parse_article, url)
        if not parsed:
            continue

        titulo = titulo_hint or parsed.get('titulo', '')
        hora = hora_hint or parsed.get('hora', '')

        if verbose:
            logger.info(f'Nova matéria: [{hora}] {titulo}')

        musicas_restantes = [
            m for m in config.MUSICAS if m['hashtag'] not in hashtags_encontradas
        ]
        matches = song_matcher.find_matches(parsed['hashtags'], musicas_restantes)
        musica_encontrada = matches[0] if matches else None

        if verbose:
            await notify_article(titulo, url, hora, parsed['hashtags'], musica_encontrada)

        if not musica_encontrada:
            continue

        for musica in matches:
            if musica['hashtag'] in hashtags_encontradas:
                continue
            hashtags_encontradas.add(musica['hashtag'])

            nova = {
                'hashtag': musica['hashtag'],
                'nome': musica['nome'],
                'url': url,
                'titulo': titulo,
                'hora': hora or datetime.now().strftime('%H:%M'),
            }
            musicas_encontradas.append(nova)
            current['musicas'] = musicas_encontradas
            state.save_sync(current)

            n = len(musicas_encontradas)
            logger.info(f'🎵 Música {n}/{config.TOTAL_SONGS}: {musica["nome"]} (#{musica["hashtag"]})')
            await notify_song(nova, n)

            if n >= config.TOTAL_SONGS:
                logger.info('Todas as músicas encontradas. Monitor encerrado.')
                await notify_all_found(musicas_encontradas)
                return True

    return False
