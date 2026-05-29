# Bot do Concurso Jonas Brothers — Hugo Gloss

Bot Python que monitora o site [Hugo Gloss](https://hugogloss.uol.com.br) em tempo real
e detecta hashtags de músicas dos Jonas Brothers escondidas em notícias.

---

## Sumário

1. [Como funciona](#como-funciona)
2. [Instalação](#instalação)
3. [Configuração](#configuração)
4. [Criando o bot no Telegram](#criando-o-bot-no-telegram)
5. [Como rodar](#como-rodar)
6. [Comandos do Telegram](#comandos-do-telegram)
7. [Testando antes do dia oficial](#testando-antes-do-dia-oficial)
8. [Aviso de uso responsável](#aviso-de-uso-responsável)
9. [Estrutura do projeto](#estrutura-do-projeto)

---

## Como funciona

1. A cada 60 segundos o bot checa duas fontes:
   - Feed RSS: `https://hugogloss.uol.com.br/feed/`
   - Página inicial: `https://hugogloss.uol.com.br/`
2. Para cada matéria nova publicada na data alvo, o bot baixa o HTML e extrai hashtags.
3. As hashtags são comparadas com a lista em `config/musicas.json`.
4. A cada música encontrada, o grupo do Telegram recebe uma notificação.
5. Ao encontrar a 6ª música, o bot envia a lista final com todas as músicas em ordem.

---

## Instalação

```bash
# Clone o repositório
git clone <url-do-repo>
cd concurso-jb-br

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate        # macOS/Linux
.venv\Scripts\activate           # Windows

# Instale as dependências
pip install -r requirements.txt
```

Requer **Python 3.10+**.

---

## Configuração

### 1. Arquivo `.env`

```bash
cp .env.example .env
```

Edite `.env` com os valores reais:

| Variável | Descrição |
|---|---|
| `TELEGRAM_BOT_TOKEN` | Token do bot gerado pelo @BotFather |
| `TELEGRAM_CHAT_ID` | ID do grupo (número negativo, ex: `-1001234567890`) |
| `TARGET_DATE` | Data do concurso no formato `YYYY-MM-DD` |
| `TOTAL_SONGS` | Número de músicas esperadas (padrão: `6`) |
| `CHECK_INTERVAL_SECONDS` | Intervalo entre checagens em segundos (mínimo recomendado: `60`) |
### 2. `config/musicas.json`

Liste todas as músicas possíveis do concurso. Cada entrada tem:

- `hashtag`: a hashtag **normalizada** (lowercase, sem espaços, sem caracteres especiais)
- `nome`: o nome formatado para exibição e submissão no formulário

```json
[
  {"hashtag": "burninup", "nome": "Burnin' Up"},
  {"hashtag": "sucker",   "nome": "Sucker"}
]
```

> O arquivo já vem pré-preenchido com músicas conhecidas dos Jonas Brothers.
> Substitua ou ajuste conforme o regulamento oficial do concurso.

---

## Criando o bot no Telegram

### Passo 1 — Criar o bot

1. No Telegram, abra uma conversa com [@BotFather](https://t.me/BotFather).
2. Envie `/newbot`.
3. Escolha um nome e um username (deve terminar em `bot`).
4. O BotFather vai responder com o **token** — copie para o `.env`.

### Passo 2 — Adicionar o bot ao grupo

1. Crie (ou abra) o grupo no Telegram.
2. Adicione o bot como membro do grupo.
3. Dê permissão para o bot enviar mensagens (nas configurações do grupo).

### Passo 3 — Descobrir o Chat ID do grupo

Opção A — usando a API do Telegram:
```bash
curl "https://api.telegram.org/bot<SEU_TOKEN>/getUpdates"
```
Depois de alguém enviar uma mensagem no grupo, o campo `chat.id` aparecerá na resposta.

Opção B — adicione [@userinfobot](https://t.me/userinfobot) ao grupo e envie `/start`.

Cole o ID (número negativo) em `TELEGRAM_CHAT_ID` no `.env`.

---

## Como rodar

```bash
# Ative o ambiente virtual primeiro
source .venv/bin/activate

# Execute como módulo Python
python -m src.main
```

Para manter rodando em background (opcional):

```bash
nohup python -m src.main > /dev/null 2>&1 &
```

Para parar: `Ctrl+C` (o bot salva o estado antes de sair).

---

## Comandos do Telegram

Todos os membros do grupo podem usar:

| Comando | Descrição |
|---|---|
| `/status` | Mostra o progresso atual (N/6 músicas encontradas) |
| `/remover N` | Remove a N-ésima música da lista (1-indexed) |
| `/adicionar Nome \| URL` | Adiciona uma música manualmente |
| `/limpar` | Zera todo o progresso (requer confirmação em 30s) |
| `/exportar` | Exibe a lista em texto puro para copiar |
| `/help` | Lista todos os comandos |

---

## Testando antes do dia oficial

Para validar que o bot está funcionando **antes do concurso**:

1. **Teste de unidade** (sem precisar do Telegram):
   ```bash
   python -m pytest tests/ -v
   ```

2. **Teste de integração** — sete `TARGET_DATE` para hoje no `.env` e rode o bot.
   O bot vai monitorar o Hugo Gloss e logar tudo. Se houver qualquer matéria publicada
   hoje, ele tentará extrair hashtags e comparar com `musicas.json`.

3. **Teste do Telegram** — com o bot rodando, envie `/status` no grupo.
   Se o bot responder, a conexão está OK.

Logs detalhados ficam em `data/bot.log`.

---

## Aviso de uso responsável

- **Não diminua o intervalo de checagem abaixo de 60 segundos.** Requisições muito
  frequentes podem sobrecarregar o servidor do Hugo Gloss e resultar em bloqueio de IP.
- O bot usa User-Agent de browser real para evitar erros 403, mas não tente contornar
  proteções mais robustas (CAPTCHAs, rate limits explícitos).
- Use este bot apenas para participar legitimamente do concurso.

---

## Estrutura do projeto

```
concurso-jb-br/
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
├── config/
│   └── musicas.json          # hashtag -> nome formatado
├── src/
│   ├── __init__.py
│   ├── main.py               # entry point
│   ├── config.py             # carrega .env e JSONs
│   ├── monitor.py            # loop de monitoramento
│   ├── rss_source.py         # parser do feed RSS
│   ├── homepage_source.py    # scraper da home
│   ├── article_parser.py     # extrai hashtags do HTML
│   ├── song_matcher.py       # identifica música pela hashtag
│   ├── state.py              # gerencia state.json
│   ├── telegram_bot.py       # bot, comandos, notificações
│   └── logger_setup.py       # configuração de logging
├── data/
│   ├── state.json            # criado em runtime (gitignored)
│   └── bot.log               # log gerado em runtime (gitignored)
└── tests/
    └── test_song_matcher.py
```
