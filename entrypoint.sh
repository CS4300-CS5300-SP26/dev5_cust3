#!/bin/bash
set -e

# Collect static files
python manage.py collectstatic --noinput || echo "Static files already collected"

# Run migrations safely
python manage.py migrate --noinput || echo "Migrations failed or already applied"

# Start Gunicorn
exec gunicorn knowledge_map.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120