#!/bin/bash
set -e

# Optional: collect static files
python manage.py collectstatic --noinput || echo "Static files collection failed"

# Run migrations, but do not stop Gunicorn if migration fails
python manage.py migrate --noinput || echo "Migrations failed or already applied, continuing..."

# Start Gunicorn
exec gunicorn knowledge_map.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 3 \
    --timeout 120