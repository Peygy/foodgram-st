FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --no-cache-dir
COPY . .

COPY ./deploy.sh /deploy.sh
RUN chmod +x /deploy.sh
ENTRYPOINT ["/deploy.sh"]

CMD ["gunicorn", "--bind", "0.0.0.0:8083", "internal.wsgi"]