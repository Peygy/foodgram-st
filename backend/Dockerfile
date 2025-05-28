FROM python:3.12-slim

WORKDIR /app
RUN chmod -R 755 /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["sh", "-c", "python manage.py makemigrations && \
python manage.py migrate && \
python manage.py collectstatic --noinput && \
python manage.py load_db_food --path data/ && \
gunicorn --bind 0.0.0.0:8000 foodgram.wsgi"]