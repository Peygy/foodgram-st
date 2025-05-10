#!/bin/bash

python /app/manage.py migrate
python /app/manage.py load_db
python /app/manage.py createsuperuser 
python /app/manage.py collectstatic --noinput

cp -r /app/collected_static/. /backend_static/static/