# Install

### Clone the repository

```shell
git clone https://github.com/WGBH-MLA/chowda.git
cd chowda
```

### Install Chowda

#### Option 1: Install with PDM (Recommended)

[PDM](https://pdm.fming.dev/) is used as the packaging manager. It can be installed with `pip install pdm`.

Install the project with development dependencies:

```shell
pdm install
```

Activate your virtual environment

```shell
$(pdm venv activate)
```

???+ info "$() wrapper"

    **Note**: `pdm venv activate` outputs the command needed to activate your virtual environment. The `$()` wrapper evaluates it in your current shell context.

???+ info "Deactivate the virtual environment"

    To return to your normal shell environment, run:

    ```shell
    deactivate
    ```

#### Option 2: Install with pip

If PDM is not available, it can also be installed with pip. It is recommeneded to install to a virtual environment using `venv`:

```shell
python3 -m venv .venv
source .venv/bin/activate
```

Install the package

```shell
pip install .
```

### Create database

Chowda needs to have a PostgreSQL server running and database named `chowda-development` (tests use a database `chowda-test`).

There are many ways to do this, but an easy way is to use docker. After starting Docker on your local machine, the following command will start a container using the `postgres` image in Dockerhub.

```shell
docker run --rm --name pg -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=chowda-development postgres
```

#### Command explained

- `docker run` runs a docker container
- `--rm` option will remove the docker container once it exits.
- `--name pg` will name the running container `pg` so it can be identified when listing running containers.
- `-p 5432:5432` forwards port 5432 on your local machine to port 5432 (default postgres port) on the running container.
- `-e POSTGRES_USER=postgres` sets ENV var on container for the postgres username

!!! note inline end "Security"

    Not a secure password, but that's ok for test and development environments.

- `-e POSTGRES_PASSWORD=postgres` sets ENV var on container for postgres password

!!! note inline end "`DB_URL` environment variable"

    the environment variables values in the command must match the values that are part of the `DB_URL` environment variable specified in `.env.development`.

- `-e POSTGRES_DB=chowda-development` sets ENV var on container for the name of postgres database to use

!!! note inline end "Database creation in docker"

    The `postgres` image will create the database when starting the container.

- `postgres` is the name of the Docker image to use when starting the container.

## Apply database migrations

```shell
alembic upgrade head
```

## Run the application

The development server can be run with

```shell
pdm dev
```

Which is a shortcut for:

```shell
uvicorn chowda.app:app --reload
```

Visit: [localhost:8000](http://localhost:8000/)

## Seed the database

To seed the database with fake data, run the `seeds.py` script:

```shell
python tests/seeds.py
```

**Optional:** Customize the number of records created by changing the `num_*` variables in the `seed` function.

## Running tests

Chowda uses `pytest` for testing. Simply run:

```shell
pdm test
```

Which is the same as running:

```shell
pytest
```

### Creating the test database and running a postgres server

For the tests to run successfully, it needs a dedicated test database. This can be done with docker, with the following command:

```shell
docker run --rm --name pg -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=chowda-test postgres
```
