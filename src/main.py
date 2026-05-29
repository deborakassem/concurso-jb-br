import asyncio
import logging
import signal

from .logger_setup import setup_logger
from . import config, monitor
from .telegram_bot import get_application, notify_song_found, notify_all_found, notify_article, notify_bot_started, notify_bot_stopped

logger = logging.getLogger(__name__)


async def _main() -> None:
    setup_logger()

    logger.info('=' * 60)
    logger.info(f'Bot iniciado. Data alvo: {config.TARGET_DATE}')
    logger.info('=' * 60)

    app = get_application()
    stop_event = asyncio.Event()
    loop = asyncio.get_event_loop()

    def _handle_signal() -> None:
        logger.info('Sinal de interrupção recebido. Encerrando...')
        stop_event.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, _handle_signal)

    async with app:
        await app.start()
        await app.updater.start_polling()
        logger.info('Telegram bot iniciado e polling ativo.')

        from . import state as _state
        musicas_ja = _state.load_sync().get('musicas', [])
        await notify_bot_started(config.TARGET_DATE, musicas_ja)

        try:
            await monitor.run(notify_song_found, notify_all_found, notify_article, stop_event)
        finally:
            logger.info('Encerrando bot...')
            await notify_bot_stopped()
            await app.updater.stop()
            await app.stop()
            logger.info('Telegram bot encerrado.')

    logger.info('Bot encerrado. Até a próxima!')


def main() -> None:
    try:
        asyncio.run(_main())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
