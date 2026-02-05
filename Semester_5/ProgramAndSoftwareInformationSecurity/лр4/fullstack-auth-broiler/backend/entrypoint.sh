#!/bin/sh

echo "Applying database migrations..."
alembic upgrade head

echo "Starting application..."
# `exec "$@"` заменяет текущий процесс shell процессом, переданным в CMD.
exec "$@"