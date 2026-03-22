# Metax

## Local launch

### Setting up environment

Current Python version: **3.14**

```commandline
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.14 python3.14-dev python3.14-venv
```

Install the package manager
```commandline
curl -LsSf https://astral.sh/uv/install.sh | UV_VERSION=0.10.0 sh
```

Create a `.venv` (it is recommended to use an IDE with uv support, if available)
    
Activate .venv
```commandline
source .venv/bin/activate
```

Install dependencies
```commandline
uv sync
```

```commandline
pre-commit install
```

Create .env using env_tmpl

## Tests run
**unit**
```commandline
pytest tests/unit
```
**integration**

Run opensearch Docker container
```
docker compose -f metax.docker-compose.yml up discount-service-opensearch-node
```
```commandline
pytest tests/integration
```

## Django project location
```commandline
cd metax/frameworks_and_drivers/django_framework
```
Then use manage.py commands

Mark `discounted_service/frameworks_and_drivers/django_framework` path as Sources root

### Opensearch configuration

Maximize ram size for opensearch, if it's not done, container will not run
```commandline
sudo sysctl -w vm.max_map_count=262144
```

Check
```commandline
cat /proc/sys/vm/max_map_count
```

If output is something like this `262144` all ok

Save this config in '/etc/sysctl.conf' for not doing all config after restarting host

```commandline
sudo nano /etc/sysctl.conf
```
add this `vm.max_map_count=262144` in conf file


### Migrations
```commandline
cd metax/frameworks_and_drivers/django_framework
```
#### SqlLite
```commandline
python manage.py makemigrations metax
```
```commandline
python manage.py migrate
```
