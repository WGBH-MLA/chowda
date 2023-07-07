# Database Management

## Migrations with Alembic
Chowda uses [Alembic](https://alembic.sqlalchemy.org/en/latest/), a migration tool for the [SQLAlchemy](https://www.sqlalchemy.org/), which is the database ORM used by [SQLModel](https://sqlmodel.tiangolo.com/).

### Creating migrations
Chowda's models inherit from `SQLModel` and if the `table=True` parameter is passed, then the model is for representing data stored in a database table. For these models to work correctly, the underlying table needs to match the `SQLModel` definition in python code, and this is where migrations come in.

Alembic can detect the differences between Chowda's models and the underlying databse schema and then generate a migration script to change the database to match the model.

After you have made the changes to your model classes, run the following command from the command line:
```shell
alembic revision --autogenerate -m "short_desc_of_model_changes"
```
This will generate a migration script under `migrations/revision`. The script name will be an random ID for the revision followed by the value of the `-m` flag, e.g.  `480b8fe17026_short_desc_of_db_change.py`.

NOTE: After a migration is run, the revision ID in the file name is stored in the `alembic_version` table that is added to the database when Alembic is first installed. This table is what tells Alembic whether there are migrations to run or not.

### Checking to see if there are any migrations to run
From the command line run:
```shell
alembic check
```
If there are no migrations to run, you should see:
```shell
No new upgrade operations detected.
```
If there are migrations to run, you should see:
```shell
ERROR [alembic.util.messaging] Target database is not up to date.
  FAILED: Target database is not up to date.
```

### Run migrations
From the command line run:
```shell
alembic upgrade head
```
This will run all migrations that haven't yet been run. If there were no migrations that needed to run, nothing will happen.