#!/bin/sh

echo "Waiting for PostgreSQL to start..."
while ! python -c "import psycopg2; psycopg2.connect(dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}', host='db')" 2>/dev/null; do
  sleep 1
done
echo "PostgreSQL started"

python manage.py makemigrations
python manage.py migrate --noinput
python manage.py load_data
python manage.py collectstatic --noinput

gunicorn --bind 0.0.0.0:8000 foodgram.wsgi