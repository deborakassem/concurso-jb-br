import logging
from datetime import datetime

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
)

from . import config, state

logger = logging.getLogger(__name__)

_app: Application | None = None
_pending_limpar: dict[int, float] = {}


def get_application() -> Application:
    global _app
    if _app is None:
        _app = (
            Application.builder()
            .token(config.TELEGRAM_BOT_TOKEN)
            .get_updates_read_timeout(3)
            .get_updates_write_timeout(3)
            .get_updates_connect_timeout(3)
            .get_updates_pool_timeout(3)
            .build()
        )
        _app.add_handler(CommandHandler('status', cmd_status))
        _app.add_handler(CommandHandler('remover', cmd_remover))
        _app.add_handler(CommandHandler('adicionar', cmd_adicionar))
        _app.add_handler(CommandHandler('limpar', cmd_limpar))
        _app.add_handler(CommandHandler('exportar', cmd_exportar))
        _app.add_handler(CommandHandler('help', cmd_help))
    return _app


# ── Notificações de ciclo de vida ─────────────────────────────────────────────

async def notify_bot_started(target_date: str, musicas: list[dict]) -> None:
    app = get_application()
    n = len(musicas)
    if n > 0:
        lista = '\n'.join(f'- {m["nome"]} ({m["hora"]})' for m in musicas)
        text = (
            f'🔄 *Bot reiniciado*\n'
            f'Progresso atual: {n}/{config.TOTAL_SONGS} músicas\n'
            f'{lista}\n'
            f'Voltando a monitorar...'
        )
    else:
        text = (
            f'🔄 *Bot reiniciado*\n'
            f'Progresso atual: 0/{config.TOTAL_SONGS} músicas\n'
            f'Voltando a monitorar...'
        )
    await app.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text=text, parse_mode='Markdown')


async def notify_bot_stopped() -> None:
    app = get_application()
    await app.bot.send_message(chat_id=config.TELEGRAM_CHAT_ID, text='🔴 *Bot encerrado.*', parse_mode='Markdown')


# ── Notificações (chamadas pelo monitor) ──────────────────────────────────────

async def notify_article(titulo: str, url: str, hora: str, hashtags: list[str], musica: dict | None) -> None:
    app = get_application()
    if musica:
        cabecalho = f'📰 Nova matéria (🎵 *{musica["nome"]}* encontrada!)'
    else:
        cabecalho = '📰 Nova matéria (sem música identificada)'

    tags_str = ' '.join(f'#{h}' for h in hashtags) if hashtags else 'N/A'

    text = (
        f'{cabecalho}\n\n'
        f'*Título:* {titulo}\n'
        f'*Publicada:* {hora}\n'
        f'*Hashtags:* {tags_str}\n'
        f'*Link:* {url}'
    )
    await app.bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID, text=text, parse_mode='Markdown',
        disable_web_page_preview=True,
    )


async def notify_song_found(musica: dict, total: int) -> None:
    app = get_application()
    text = (
        f'🎵 Música {total}/{config.TOTAL_SONGS} encontrada!\n'
        f'*{musica["nome"]}*\n'
        f'🕐 {musica["hora"]} — {musica["titulo"]}\n'
        f'🔗 {musica["url"]}'
    )
    await app.bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID, text=text, parse_mode='Markdown'
    )


async def notify_all_found(musicas: list[dict]) -> None:
    app = get_application()
    lista = '\n'.join(f'{i + 1}. {m["nome"]} — {m["hora"]}' for i, m in enumerate(musicas))
    text = (
        f'✅ *TODAS AS {config.TOTAL_SONGS} MÚSICAS ENCONTRADAS*\n\n'
        f'Lista final em ordem de publicação:\n'
        f'{lista}\n\n'
        f'🚨 *ENVIE O FORMULÁRIO AGORA!*'
    )
    await app.bot.send_message(
        chat_id=config.TELEGRAM_CHAT_ID,
        text=text,
        parse_mode='Markdown',
    )


# ── Comandos ──────────────────────────────────────────────────────────────────

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    current = state.load_sync()
    musicas = current['musicas']
    n = len(musicas)

    if not musicas:
        text = f'📊 Progresso: 0/{config.TOTAL_SONGS} músicas encontradas'
    else:
        lista = '\n'.join(f'{i + 1}. {m["nome"]} ({m["hora"]})' for i, m in enumerate(musicas))
        text = f'📊 Progresso: {n}/{config.TOTAL_SONGS} músicas encontradas:\n{lista}'

    await update.message.reply_text(text, parse_mode='Markdown', do_quote=False)


async def cmd_remover(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not context.args:
        await context.bot.send_message(chat_id, 'Uso: /remover N (onde N é o número da música)')
        return
    try:
        n = int(context.args[0])
    except ValueError:
        await context.bot.send_message(chat_id, 'Número inválido.')
        return

    current = state.load_sync()
    musicas = current['musicas']

    if n < 1 or n > len(musicas):
        await context.bot.send_message(chat_id, f'Número fora do intervalo (1-{len(musicas)}).')
        return

    removida = musicas.pop(n - 1)
    current['musicas'] = musicas
    state.save_sync(current)
    await context.bot.send_message(chat_id, f'❌ Removida: *{removida["nome"]}*', parse_mode='Markdown')


async def cmd_adicionar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    text = update.message.text.partition(' ')[2].strip()
    if '|' not in text:
        await context.bot.send_message(chat_id, 'Uso: /adicionar Nome | URL')
        return

    nome, _, url = text.partition('|')
    nome = nome.strip()
    url = url.strip()

    if not nome or not url:
        await context.bot.send_message(chat_id, 'Nome e URL são obrigatórios.')
        return

    nova = {
        'hashtag': 'manual',
        'nome': nome,
        'url': url,
        'titulo': 'Adicionado manualmente',
        'hora': datetime.now().strftime('%H:%M'),
    }
    current = state.load_sync()
    current['musicas'].append(nova)
    state.save_sync(current)

    n = len(current['musicas'])
    await context.bot.send_message(
        chat_id,
        f'✅ Adicionada: *{nome}* ({n}/{config.TOTAL_SONGS})',
        parse_mode='Markdown',
    )

    if n >= config.TOTAL_SONGS:
        await notify_all_found(current['musicas'])


async def cmd_limpar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    now = datetime.now().timestamp()

    if chat_id in _pending_limpar and now - _pending_limpar[chat_id] < 30:
        del _pending_limpar[chat_id]
        current = state.load_sync()
        current.update({'musicas': [], 'urls_vistas': []})
        state.save_sync(current)
        await context.bot.send_message(chat_id, '🗑️ Progresso zerado.')
    else:
        _pending_limpar[chat_id] = now
        await context.bot.send_message(chat_id, '⚠️ Confirme: envie /limpar novamente nos próximos 30 segundos.')


async def cmd_exportar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    current = state.load_sync()
    musicas = current['musicas']

    if not musicas:
        await context.bot.send_message(chat_id, 'Nenhuma música encontrada ainda.')
        return

    text = '\n'.join(m['nome'] for m in musicas)
    await context.bot.send_message(chat_id, f'```\n{text}\n```', parse_mode='Markdown')


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        '*Comandos disponíveis:*\n\n'
        '/status — Progresso atual\n'
        '/remover N — Remove a N-ésima música\n'
        '/adicionar Nome | URL — Adiciona música manualmente\n'
        '/limpar — Zera o progresso (requer confirmação)\n'
        '/exportar — Lista músicas em texto puro\n'
        '/help — Esta mensagem'
    )
    await context.bot.send_message(update.effective_chat.id, text, parse_mode='Markdown')
