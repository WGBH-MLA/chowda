![deploy](https://github.com/WGBH-MLA/chowda/actions/workflows/CI.yml/badge.svg)
![deploy](https://github.com/WGBH-MLA/chowda/actions/workflows/CD.yml/badge.svg)

# Chowda

CLAMS processing app

## Install

1. Clone the repository::

```shell
git clone https://github.com/WGBH-MLA/chowda.git
cd chowda
```

2. Create and activate a virtual environment::

### With Poetry

```shell
poetry install
poetry shell
```

### With venv

```shell
python3 -m venv env
source env/bin/activate
```

Install the package

```shell
pip install .'
```

## Run the application

```shell
uvicorn chowda:app
```
