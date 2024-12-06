FROM python:3.11.5

RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    python3-dev \
    build-essential \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PORT=8000

CMD gunicorn config.wsgi:application --bind 0.0.0.0:$PORT