#!/bin/bash
set -e

echo "💾 Migrating..."
python manage.py migrate --noinput

echo "🚀 Starting gunicorn..."
exec gunicorn go_guide.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${WORKERS:-3} \
  --threads ${THREADS:-4} \
  --timeout ${TIMEOUT:-30}
