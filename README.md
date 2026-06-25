# Metax

Telegram-bot–driven service that crawls Armenian retailers for discounted products and lets
users search them. Search is **semantic**: product names are embedded and matched with
pgvector, all inside a single PostgreSQL database.

## Architecture

| Component | Role |
|-----------|------|
| **PostgreSQL + pgvector** | The single data store for every environment. Holds entities (categories, retailers, discounted products) **and** the search index — a `vector(1024)` embedding column on `discounted_products` with an HNSW (cosine) index, plus a `pg_trgm` GIN index for the exact-match boost. |
| **metax-embeddings** | sentence-transformers (PyTorch, CPU) service serving `Metric-AI/armenian-text-embeddings-2-large` (a multilingual E5 model fine-tuned for Armenian). Runs as a container; the model is downloaded on first boot. The same service also powers embedding-based category classification. |
| **Redis** | Message broker / result backend for the Taskiq worker (not a data store). |
| **metax (HTTP)** | Gunicorn/uvicorn Django ASGI app (JSON:API). Runs DB migrations on startup. |
| **metax-taskiq** | Background worker: nightly crawl of retailers, optional embedding-based category classification, then embeds the newly collected products. |
| **metax-telegram-bot** | Long-polling Telegram bot for end users (search + retailer/category filters). |
| **fluent-bit** | Log shipping (prod only). |

Search ranking: order by vector cosine distance, with a literal `ILIKE` boost so exact
brand/SKU queries surface their exact matches first.

## Environments

Selected by the `ENV` variable:

| `ENV` | Application | Infra (Postgres / Embeddings / Redis) | Compose file |
|-------|-------------|-----------------------------------|--------------|
| `dev` | Python on the host | Docker (ports on `127.0.0.1`) | `docker-compose.dev.yml` |
| `prod` | Docker | Docker | `docker-compose.prod.yml` |
| `test` | Docker | Docker | `docker-compose.test.yml` |

Configuration classes live in `metax_configs.py`:

* `DevConfigs` ignores `.env` — all dev values are class-level defaults that must stay in
  sync with `docker-compose.dev.yml`.
* `TestConfigs` ignores `.env` — CI values come from `docker-compose.test.yml`.
* `ProdConfigs` reads `.env` (created at deploy time, never committed).

## Local setup (dev on the host)

Python: **3.14.2**

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.14 python3.14-dev python3.14-venv

curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.10.0 sh

uv sync
source .venv/bin/activate
pre-commit install
```

## Run dev

Create `.env` from `env_template` and set `ENV=dev` (only `TELEGRAM_BOT_TOKEN` is needed for
the bot; the rest of dev uses `DevConfigs` defaults).

**One command** — starts the infra containers (Postgres + Embeddings + Redis), waits for them to
become healthy, then runs the HTTP server, Taskiq worker, and Telegram bot together:

```bash
python run_dev.py
```

Or run pieces individually (with the containers up via `docker compose -f docker-compose.dev.yml up -d`):

```bash
python run_metax_http_server.py     # HTTP API (runs migrations on startup)
python run_metax_taskiq_app.py      # background worker
python run_metax_telegram_bot.py    # Telegram bot (needs TELEGRAM_BOT_TOKEN)
```

> First boot downloads `armenian-text-embeddings-2-large` into the embeddings container
> (~2.2 GB from HuggingFace); give it a couple of minutes before search/embedding works.

## Run prod

Create `.env` from `env_template`, fill in real values (including `TELEGRAM_BOT_TOKEN` and the
`EMBEDDING_*` values pointing at the in-stack `metax-embeddings` service), then:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

This brings up: Postgres + Embeddings + Redis + fluent-bit + **metax (HTTP)** + **metax-taskiq** +
**metax-telegram-bot**. Migrations run automatically when the `metax` service starts.

## Tests

```bash
pytest tests/unit          # no containers needed
```

Integration / e2e tests need Postgres **and** the embeddings service. Locally, with the dev stack up:

```bash
docker compose -f docker-compose.dev.yml up -d
pytest tests/integration tests/e2e
```

Full CI-style run (everything in Docker):

```bash
docker compose -f docker-compose.test.yml up -d --build --wait
docker compose -f docker-compose.test.yml exec -T metax pytest tests/unit tests/integration
```

## Migrations

Migrations run automatically on `metax` HTTP startup. There is a single consolidated
`0001_initial` migration that creates the whole schema plus the `vector` and `pg_trgm`
extensions and the search indexes. To create a new migration after a model change:

```bash
python metax_cli_app.py migrations migrate-postgres
```

> Switching an existing dev/test database to the consolidated migration requires a clean
> volume: `docker compose -f docker-compose.dev.yml down -v` then bring it back up.

## Django project

```bash
cd metax/frameworks_and_drivers/django_framework
```

Use `manage.py` from there. Mark this directory as Sources Root in your IDE.

## Production machine requirements

The footprint is dominated by the **embeddings service** running the Armenian E5 model
(CPU inference). Embedding the nightly crawl — and the optional embedding-based category
classification that runs alongside it — is the peak load; interactive search embeds one short
string per query.

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| **RAM** | 6 GB (tune Gunicorn workers down) | **8–16 GB** |
| **vCPU** | 2 | **4** |
| **Disk** | 20 GB SSD | 40 GB SSD |
| **Swap** | 2 GB | 2–4 GB |
| **GPU** | none | optional (only speeds up nightly embedding) |

Rough RAM breakdown at peak: embeddings/E5 ~2–3 GB · Postgres ~0.5–1 GB · Gunicorn workers
~1 GB · Taskiq ~0.4 GB · Telegram bot ~0.25 GB · Redis + fluent-bit ~0.2 GB · OS ~0.5 GB.

Notes:
* **4 GB is not enough** — the embeddings service alone needs ~2–3 GB while embedding, risking OOM during a crawl.
* Gunicorn workers default to `(2 × CPU) + 1`; on small machines keep CPU low (or tune) so the
  worker count doesn't inflate RAM.
* Disk: container images + the embedding model ~2.2 GB + Postgres data (embeddings are
  ~4 KB/row plus HNSW index) + logs. 20 GB is a safe floor.
* GPU is **not required**; the model runs fine on CPU at this scale. A GPU mainly shortens the
  nightly bulk-embedding window.
