FROM python:3.11.5

# Installation des dépendances système
RUN apt-get update && apt-get install -y \
    pkg-config \
    default-libmysqlclient-dev \
    python3-dev \
    build-essential \
    libpcsclite-dev \
    swig \
    redis-server \
    python3-mysqldb \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Mise à jour de pip et installation de dj-database-url
RUN pip install --upgrade pip
RUN pip install dj-database-url mysqlclient gunicorn

# Installation des dépendances
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copie du projet
COPY . .

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=config.settings
ENV PORT=8000

# Commande de démarrage
CMD gunicorn config.wsgi:application --bind 0.0.0.0:$PORT