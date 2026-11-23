# 1. L'idée générale

## Le problème

Une boutique en ligne montre ses meubles avec des **photos plates**. Un modèle 3D, que l'acheteur
fait tourner à la souris, aide beaucoup à décider. Mais le fabriquer coûte cher : il faut un logiciel
3D et une personne formée.

## La solution

| Étape | Qui | Ce qui se passe |
|---|---|---|
| 1 | La propriétaire | Envoie **une photo** d'une chaise, d'un tabouret ou d'une table d'appoint |
| 2 | Le serveur | Vérifie la photo, la prépare, l'envoie à un **modèle d'IA pré-entraîné** (TRELLIS ou TripoSR) |
| 3 | L'IA | Renvoie un fichier **`.glb`** |
| 4 | La propriétaire | Examine le modèle dans le Studio, le compare à la photo, le télécharge |
| 5 | La propriétaire | **Active l'intégration** du modèle (il est privé par défaut) |
| 6 | Un site partenaire | Affiche le modèle avec `<forma3d-viewer>` ou l'appelle par l'**API `/api/v1`** avec une **clé API** |

## Les contraintes qui expliquent les choix

| Contrainte | Conséquence dans le code |
|---|---|
| 100 % gratuit | Aucune API payante : on utilise des **Spaces publics Hugging Face** ou un serveur Colab |
| Aucun entraînement | On appelle un modèle **déjà entraîné** ; le projet ne contient aucun code d'apprentissage |
| Les services gratuits sont instables | Délai maximal, une relance au plus, messages d'erreur clairs, badge « Serveur 3D » dans l'en-tête |
| Studio mono-propriétaire | Une seule personne se connecte, avec **un mot de passe** ; pas de comptes publics |
| Sécurité de l'intégration | Tout est **fermé par défaut** : modèle désactivé, aucun site autorisé (CORS et iframe) |

## La mauvaise idée et la bonne idée

**Mauvaise idée :** écrire l'appel à l'IA directement dans la route HTTP. Le jour où le Space change
ou où l'on passe de TripoSR à TRELLIS, il faut tout réécrire, et on ne peut rien tester sans réseau.

**Bonne idée : des contrats (interfaces).** Le service de génération ne connaît qu'une promesse :

```python
class Image3DProvider(Protocol):
    def generate(self, image_path: Path) -> bytes:
        """Renvoie un modèle GLB réellement produit pour cette image."""
```

TRELLIS et TripoSR tiennent tous les deux cette promesse. Dans les tests, un **faux fournisseur**
la tient aussi, sans réseau. C'est comme une prise électrique : l'appareil (le service) se fiche de
savoir quelle centrale produit le courant.

Même principe pour la base de données (`GenerationRepository`) et pour les fichiers (`Storage`).

## Les états d'une génération

Une génération prend 1 à 3 minutes. On ne peut pas faire attendre le navigateur aussi longtemps,
donc chaque génération a un **état** enregistré en base :

```
PENDING  ──►  RUNNING  ──►  DONE
 (reçue)      (en cours)     (GLB prêt)
                  │
                  └──────►  FAILED  (message d'erreur clair, sans secret)
```

Le navigateur reçoit tout de suite une réponse **202 Accepted** avec une adresse de suivi
(`status_url`), puis la consulte toutes les 1,5 seconde jusqu'à DONE ou FAILED.

## Les deux portes d'entrée du serveur

| Porte | Pour qui | Protection |
|---|---|---|
| Studio : `/models`, `/categories`, `/api-keys` | La propriétaire, dans son navigateur | **Cookie de session** signé (après mot de passe) |
| API externe : `/api/v1/...` | Le serveur d'un site partenaire | **Clé API** dans l'en-tête `X-API-Key` |
| Public : `/public/models/...`, `/embed/...` | N'importe quel visiteur d'une boutique | Seulement les modèles **activés** par la propriétaire |

## Correspondance avec les sprints

| Sprint | Ce qui a été construit | Où dans le code |
|---|---|---|
| 1 — De la photo au 3D | Upload, fournisseur, états, viewer | `upload_validator.py`, `providers/`, `generation_service.py`, `frontend/` |
| 2 — Qualité et fiabilité | Historique en base, catégories, préparation de la photo | `repositories/`, `category_service.py`, `image_preparer.py` |
| 5 — Module intégrable | UUID public, clés API, `/api/v1`, `/embed`, widget, connexion | `routers/api_v1.py`, `routers/embed.py`, `widget.js`, `owner_auth.py` |
| DevOps | PostgreSQL, Docker, CI | `postgres_repository.py`, `factory.py`, `Dockerfile`, `compose.yaml` |
