# Install

### Clone the repository::

```shell
git clone https://github.com/WGBH-MLA/chowda.git
cd chowda
```

### Install with PDM (Recommended)

[PDM](https://pdm.fming.dev/) is used as the packaging manager. It can be installed with `pip install pdm`.

Install the project with development dependencies:

```shell
pdm install
```

Activate your virtual environment

```shell
$(pdm venv activate)
```

**Note**: `pdm venv activate` outputs the command needed to activate your virtual environment. The `$()` wrapper evaluates it in your current shell context.

### Install with venv

If PDM is not available, it can also be installed with pip. It is recommeneded to install to a virtual environment using `venv`:

```shell
python3 -m venv .venv
source .venv/bin/activate
```

Install the package

```shell
pip install .
```

## Run the application

```shell
uvicorn chowda:app --reload
```

Visit: [localhost:8000](http://localhost:8000/)

## Seed the database

To seed the database with fake data, run the `seeds.py` script:

```shell
python tests/seeds.py
```

**Optional:** Customize the number of records created by changing the `num_*` variables in the `seed` function.

## Deactivate the virtual environment

Run the `deactivate` command to return to your normal shell environment.

```shell
deactivate
```
