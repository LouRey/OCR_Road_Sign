# syntax=docker/dockerfile:1.4

########################################
# Stage 1: Builder
########################################
FROM python:3.10-slim AS builder

LABEL org.opencontainers.image.authors="Votre Nom <vous@example.com>"
LABEL org.opencontainers.image.version="1.0.0"

WORKDIR /app

# Installer dépendances de compilation
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      build-essential \
      git \
      libgl1-mesa-glx \
      libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# Copier dépendances Python
COPY requirements.txt pyproject.toml ./

# Installer pip et dépendances
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir streamlit kedro-datasets

########################################
# Stage 2: Runtime
########################################
FROM python:3.10-slim AS runtime

# Installer dépendances système (OpenCV, Tesseract, curl)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libgl1-mesa-glx \
      libglib2.0-0 \
      tesseract-ocr \
      libleptonica-dev \
      libtesseract-dev \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Télécharger modèle de langue français pour Tesseract
RUN mkdir -p /usr/share/tessdata \
 && curl -sSL \
    https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata \
    -o /usr/share/tessdata/fra.traineddata

# Créer utilisateur non-root
RUN groupadd --system app \
 && useradd --system --create-home --gid app app

WORKDIR /app

# Copier bibliothèques Python du builder
COPY --from=builder /usr/local /usr/local

# Copier le code source
COPY . .

# Donner à l'utilisateur app la main sur le dossier de configuration
RUN chown -R app:app /app/conf
# Donner à l'utilisateur non-root "app" la propriété de tout /app
RUN chown -R app:app /app/data

# Préparer tmp et modèles
RUN mkdir -p /app/tmp /app/models \
 && chown -R app:app /app/tmp /app/models

# Installer le projet en mode editable
RUN pip install --no-cache-dir -e .

# Passer à l'utilisateur non-root
USER app

# Exposer le port default Streamlit (8501)
EXPOSE 8501

# Healthcheck optionnel pour la UI (ici on check /)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -f http://127.0.0.1:8501/ || exit 1

# Lancer Streamlit
CMD ["streamlit", "run", "app.py", "--server.fileWatcherType", "none", "--server.port=8501", "--server.address=0.0.0.0"]