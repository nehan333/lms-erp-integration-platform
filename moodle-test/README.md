# Moodle Test Environment

This directory contains the local Moodle environment used by the LMS-ERP Integration Platform.

## Structure

- `moodle/` — Moodle source code. This directory is ignored by Git.
- `moodle-docker/` — Docker configuration for running Moodle locally.

## Requirements

- Docker
- Docker Compose
- Moodle source
- PostgreSQL Docker container

## Environment

The Moodle Docker database uses an external named volume:

`moodle-postgres-data`

The database password is supplied through the environment variable `MOODLE_DOCKER_DB_PASSWORD`.

Do not commit the password to Git.

## Starting Moodle

From the `moodle-docker` directory:

```bash
cd ~/lms-erp-integration-platform/moodle-test/moodle-docker

export MOODLE_DOCKER_WWWROOT=../moodle
export MOODLE_DOCKER_DB=pgsql
export MOODLE_DOCKER_WEB_PORT=8080
export MOODLE_DOCKER_DB_PASSWORD='your-local-password'

bin/moodle-docker-compose up -d
```

Moodle is available at `http://localhost:8080`.

## Stopping Moodle

```bash
bin/moodle-docker-compose down
```

## Important

Do not delete the `moodle-postgres-data` Docker volume.

Do not run `docker volume prune` unless you have verified that the Moodle database volume is not required.

The Moodle source directory and local Moodle data are intentionally excluded from Git.
