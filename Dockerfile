# Rôle : construit l'image Docker de l'API Forma3D (FastAPI + Studio HTML + widget).
# Exécution : docker build -t forma3d:1.0 .   puis   docker run -d -p 8080:8080 forma3d:1.0
# L'image ne contient aucun secret ni donnée locale (voir .dockerignore) ; la configuration
# passe uniquement par les variables d'environnement (Compose, CI, staging).

# Image de base à version FIXÉE (jamais « latest ») : la même construction donne le même résultat.
# « slim » = Debian minimale : moins de paquets, image plus petite, moins de failles potentielles.
FROM python:3.12-slim

# PYTHONDONTWRITEBYTECODE : pas de fichiers .pyc inutiles dans l'image.
# PYTHONUNBUFFERED : les journaux sortent immédiatement (visibles par « docker logs »).
# PIP_DISABLE_PIP_VERSION_CHECK : pas d'appel réseau de vérification de pip pendant la construction.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Arborescence /app/backend + /app/frontend : main.py calcule la racine du projet depuis son propre
# emplacement et sert /app/frontend sous /static. Il faut donc reproduire ces deux dossiers côte à côte.
WORKDIR /app/backend

# Couche 1 : les dépendances SEULES. Docker met en cache chaque couche ; tant que requirements.txt
# ne change pas, cette étape (la plus longue) est réutilisée même si le code change.
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Couche 2 : le code, qui change souvent, APRÈS les dépendances.
COPY backend/app ./app
COPY frontend /app/frontend

# Utilisateur non root : si l'application est compromise, l'attaquant n'est pas root dans le conteneur.
# Les dossiers de données lui appartiennent pour qu'il puisse y écrire (SQLite, GLB, photos).
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/backend/data /app/backend/storage \
    && chown -R appuser:appuser /app/backend/data /app/backend/storage
USER appuser

# Documentation du port d'écoute (le publier reste le rôle de « docker run -p » ou de Compose).
EXPOSE 8000

# Contrôle de santé interne : Docker marque le conteneur « healthy » ou « unhealthy ».
# Écrit en Python car curl n'est pas présent dans l'image slim (l'installer alourdirait l'image).
HEALTHCHECK --interval=10s --timeout=3s --start-period=15s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"]

# 0.0.0.0 = écouter sur toutes les interfaces du conteneur. Avec 127.0.0.1, l'API ne serait joignable
# que depuis l'intérieur du conteneur : le port publié sur l'hôte ne recevrait aucune réponse.
# Forme JSON (exec) : uvicorn est le processus 1 et reçoit directement le signal d'arrêt de Docker.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
