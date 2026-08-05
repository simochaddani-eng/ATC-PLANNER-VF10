# ============================================
# DOCKERFILE POUR RENDER
# ============================================

FROM python:3.11-slim

# Créer un utilisateur non-root (bonne pratique)
RUN useradd -m -u 1000 render
USER render
ENV PATH="/home/render/.local/bin:$PATH"

# Dossier de travail
WORKDIR /app

# Copier et installer les dépendances
COPY --chown=render requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code
COPY --chown=render . .

# Port par défaut de Render
EXPOSE 10000

# Variables d'environnement pour Streamlit
ENV STREAMLIT_SERVER_PORT=10000
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Lancer l'application
CMD ["streamlit", "run", "app.py", "--server.port=10000", "--server.address=0.0.0.0", "--server.headless=true"]
