# Database Migrations

## Create a Migration Script

```shell
alembic revision --autogenerate -m "migration_name_here"
```

## Running Migration

```shell
alembic upgrade head
```

## Downgrading

```shell
alembic downgrade -1
```
