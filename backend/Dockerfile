FROM python:3.12-slim

WORKDIR /app
RUN chmod -R 755 /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x deploy.sh

ENTRYPOINT ["./deploy.sh"]