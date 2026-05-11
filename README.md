# Metax

## Environments

The project supports three environments selected by the `ENV` variable:

| `ENV` | Application | Databases | Compose file |
|-------|-------------|-----------|--------------|
| `dev` | Python on the host | Docker (ports on `127.0.0.1`) | `docker-compose.dev.yml` |
| `prod` | Docker | Docker | `docker-compose.prod.yml` |
| `test` | Docker | Docker | `docker-compose.test.yml` |

Configuration classes live in `metax_configs.py`:

* `DevConfigs` ignores `.env` - all dev values are class-level defaults that
  must stay in sync with `docker-compose.dev.yml`.
* `TestConfigs` ignores `.env` - CI values come from `docker-compose.test.yml`.
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

OpenSearch needs `vm.max_map_count` raised:

```bash
sudo sysctl -w vm.max_map_count=262144
```

To make it persistent, add `vm.max_map_count=262144` to `/etc/sysctl.conf`.

## Run dev
Create .env from env_template, set ENV=dev in .env

Start the database containers:
```bash
docker compose -f docker-compose.dev.yml up -d 
```

Run the application on the host with `ENV=dev`:

```bash
python run_metax_http_server.py
```

Run taskiq app
```bash
python run_metax_taskiq_app.py
```

## Tests

**Unit:**

```bash
pytest tests/unit
```

**Integration** (against the dev DB containers running locally):

```bash
docker compose -f docker-compose.dev.yml up -d 
```

```bash
pytest tests/integration
```

## Run prod

Create `.env` from `env_template` and fill in real values, then:

```bash
docker compose -f docker-compose.prod.yml up -d 
```

## Django project

```bash
cd metax/frameworks_and_drivers/django_framework
```

Use `manage.py` from there. Mark this directory as Sources Root in your IDE.

## Migrations

```bash
python metax_cli_app.py migrations migrate-postgres
```
