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

COPY requirements.txt pyproject.toml ./

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir gunicorn kedro-datasets

########################################
# Stage 2: Runtime
########################################
FROM python:3.10-slim AS runtime

# Installer dépendances système (OpenCV, Tesseract natif et curl pour récupérer les données)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libgl1-mesa-glx \
      libglib2.0-0 \
      tesseract-ocr \
      libleptonica-dev \
      libtesseract-dev \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Télécharger manuellement le modèle français dans le bon dossier
RUN mkdir -p /usr/share/tessdata \
 && curl -sSL \
    https://github.com/tesseract-ocr/tessdata/raw/main/fra.traineddata \
    -o /usr/share/tessdata/fra.traineddata

# Créer un utilisateur non-root
RUN groupadd --system app \
 && useradd --system --create-home --gid app app

WORKDIR /app

# Copier libs Python depuis le builder
COPY --from=builder /usr/local /usr/local

# Variables d'environnement
ENV PATH=/usr/local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    KEDRO_ENV=local \
    TESSDATA_PREFIX=/usr/share/tessdata

COPY . .

# Installer le projet en mode editable via pyproject.toml
RUN pip install --no-cache-dir -e .

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -f http://127.0.0.1:${PORT}/health || exit 1

CMD ["gunicorn",  \
     "--bind", "0.0.0.0:8080",  \
     "--workers", "2",  \
     "--timeout", "0",  \
     "app:app"  \
    ]
