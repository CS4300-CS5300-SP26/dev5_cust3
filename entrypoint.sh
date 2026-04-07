#!/bin/bash
set -e

echo "Running migrations..."
python ./knowledge_map/manage.py migrate --noinput

echo "Collecting static files..."
python ./knowledge_map/manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 --workers 3 --chdir /app/knowledge_map knowledge_map.wsgi:application