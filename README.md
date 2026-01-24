# Discount Service

## Local launch

### Setting up environment

Current version of Python: **3.14**

```commandline
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.14 python3.14-dev python3.14-venv python3-pip
```

```commandline
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

```commandline
pre-commit install
```
Select interpreter from .venv


Create .env using env_tmpl

## Tests run
**unit**
```commandline
pytest tests/unit
```
**integration**

Run opensearch Docker container
```
cd discount_service
docker compose -f discount_service.docker-compose.yml up discount-service-opensearch-node
```
```commandline
pytest tests/integration
```

## Django project location
```commandline
cd discount_service/frameworks_and_drivers/django_framework
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
cd discount_service/frameworks_and_drivers/django_framework
```
#### SqlLite
```commandline
python manage.py makemigrations discount_service
```
```commandline
python manage.py migrate
```
