# ============================================================
# ATC PLANNER — Image Docker de production
# ============================================================

FROM python:3.11-slim

# Dépendances système nécessaires à psycopg2 (client PostgreSQL)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Streamlit écoute sur ce port par défaut ; certaines plateformes (Railway,
# Render...) imposent leur propre port via la variable d'environnement PORT.
EXPOSE 8501

# Vérifie que l'app répond (utilisé par ECS/App Runner/docker-compose/Railway)
HEALTHCHECK CMD curl --fail http://localhost:${PORT:-8501}/_stcore/health || exit 1

# --server.address=0.0.0.0 est indispensable pour être joignable depuis
# l'extérieur du conteneur (sinon Streamlit n'écoute que sur localhost).
# Forme shell (pas de crochets JSON) : nécessaire pour que ${PORT:-8501}
# soit bien substitué au démarrage. Sur Railway/Render, PORT est injecté
# automatiquement ; en local ou sur AWS, on retombe sur 8501 par défaut.
ENTRYPOINT streamlit run app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --browser.gatherUsageStats=false
