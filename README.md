# Discount Service

## Local launch

### Setting up environment

Current version of Python: **3.14**

```bash
    sudo add-apt-repository ppa:deadsnakes/ppa
    sudo apt update
    sudo apt install python3.14 python3.14-dev python3.14-venv python3-pip
```

```bash
    python3.14 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
```

```bash
    pre-commit install
```

* Select interpreter from .venv