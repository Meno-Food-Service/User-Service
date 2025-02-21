FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*


WORKDIR /app


COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


ENV PYTHONUNBUFFERED=1 \
    DATABASE_URL="postgresql+asyncpg://username:password@pg:5432/UserYDB" \
    RMQ_URL="amqp://username:password@rabbitmq:5672/" \
    REDIS_HOST="redis" \
    REDIS_PORT="6379" \
