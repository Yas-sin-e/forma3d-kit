# 13. Lancer le projet sur ton PC

Ouvre un terminal **PowerShell** à la racine du dépôt (`forma3d-kit`).

## Avant la première fois

| Outil | Pourquoi |
|---|---|
| Python 3.11 ou plus récent | Exécuter le backend |
| Docker Desktop (démarré) | Faire tourner PostgreSQL |
| `backend/.env` | Tes réglages et secrets (copie de `.env.example`, jamais commis) |

Dans `backend/.env`, renseigne au minimum :
- `FORMA3D_OWNER_PASSWORD` : le mot de passe du Studio ;
- `IMAGE3D_PROVIDER` : `trellis` ou `triposr` ;
- pour TripoSR : `HF_SPACE_ID` (identifiant du Space ou lien Gradio de la session Colab).

## Lancer l'application : une seule commande

```powershell
.\scripts\dev.ps1
```

Ce script :
1. crée l'environnement Python `backend/.venv` s'il manque, puis installe les dépendances ;
2. crée `.env.compose` à partir du modèle s'il manque ;
3. démarre **PostgreSQL** avec Docker Compose (accessible sur `127.0.0.1:5433`) et crée la base de test ;
4. lance **pytest** ;
5. démarre **Uvicorn** et ouvre le Studio dans le navigateur.

Puis ouvre :
- le Studio : http://127.0.0.1:8001/
- la documentation interactive de l'API : http://127.0.0.1:8001/docs
- l'état du serveur 3D : http://127.0.0.1:8001/health/provider

## Lancer seulement les tests

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest -q
```

PostgreSQL doit être démarré (le plus simple : lancer `.\scripts\dev.ps1` une fois avant).

## Le badge « Serveur 3D » de l'en-tête

| Badge | Sens | Que faire |
|---|---|---|
| En ligne | Le fournisseur répond | Tu peux créer un modèle |
| Hors ligne (TRELLIS) | Le Space dort, est en panne ou le quota GPU du jour est atteint | Réessayer plus tard |
| Hors ligne (TripoSR) | Le notebook Colab est arrêté ou son lien a expiré (72 h) | Relancer le notebook, mettre le nouveau lien dans `backend/.env`, redémarrer |
| Non configuré | `HF_SPACE_ID` est vide | Le renseigner dans `backend/.env` |

⚠️ Les offres gratuites (Spaces, Colab) ont des **quotas**, des **files d'attente** et des **mises en veille** :
une démonstration en direct peut échouer pour une raison extérieure au code. Les 5 exemples
pré-générés restent consultables dans **Exemples** (ils sont signalés comme pré-générés).

## Si ça ne marche pas

| Message | Cause | Solution |
|---|---|---|
| `Docker ne répond pas` | Docker Desktop est fermé | Démarrer Docker Desktop, relancer le script |
| `DATABASE_URL est vide` | Le backend est lancé sans le script | Utiliser `.\scripts\dev.ps1` |
| Connexion refusée au Studio (503) | `FORMA3D_OWNER_PASSWORD` est vide | Le renseigner dans `backend/.env`, redémarrer |
| « Trop de tentatives » (429) | 5 mots de passe faux en une minute | Attendre une minute |
| Erreur 401 sur toutes les pages | Session expirée (8 h) ou serveur redémarré | Se reconnecter |
| Création refusée « catégorie inconnue » (422) | Catégorie désactivée | La réactiver dans **Catégories** |
| `address already in use` | Un autre serveur utilise le port | `.\scripts\dev.ps1 -Port 8002` |
| Le modèle reste « en cours » puis échoue | Délai de 300 s dépassé ou Space saturé | Réessayer plus tard ; vérifier `/health/provider` |
