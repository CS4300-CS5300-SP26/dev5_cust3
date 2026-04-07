#!/bin/bash
set -e

echo "Running collectstatic..."
python ./knowledge_map/manage.py collectstatic --noinput

echo "Starting server..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --chdir /app/knowledge_map knowledge_map.wsgi:application