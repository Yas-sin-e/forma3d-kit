# Guide d’intégration Forma3D

Ce guide s’adresse à la personne qui connecte une boutique au service Forma3D. Une version lisible est aussi affichée dans le Studio, page **Guide d’intégration** (`#/guide`), avec l’adresse réelle du service dans les exemples. Il décrit les routes et les limites présentes dans le code du dépôt. Il ne contient ni clé API réelle, ni identifiant de modèle réel.

## Avant de commencer

- Forma3D Studio et son backend doivent tourner sur une adresse joignable depuis l'intégrateur ; en local, le script de développement utilise `http://127.0.0.1:8001`.
- Créez une clé dans la page locale **Clés API** (`#/cles-api`). La clé complète n'apparaît qu'une fois. Copiez-la immédiatement dans le coffre ou la configuration du serveur intégrateur.
- Envoyez les requêtes API depuis un backend marchand protégé. Ne placez jamais `X-API-Key` dans JavaScript, HTML public, application mobile distribuée, capture ou dépôt Git.
- Une génération doit être terminée dans le Studio puis activée sur la fiche du modèle avant que les clients puissent voir son viewer public.
- Le Studio est protégé par le mot de passe de la propriétaire (`FORMA3D_OWNER_PASSWORD`, session par cookie HttpOnly). Les routes `/api/v1` n'utilisent pas cette session : elles exigent `X-API-Key`. Gardez néanmoins le Studio en local tant qu'il n'est pas déployé en HTTPS.

## 1. Envoyer une photo

La clé a le droit d'envoyer des photos JPG, PNG ou WebP jusqu'à 10 Mo. Le champ catégorie reçoit un slug actif, par exemple `chair`.

```bash
BASE_URL="http://127.0.0.1:8001"
API_KEY="REMPLACER_PAR_VOTRE_CLE"
curl --fail-with-body -X POST "$BASE_URL/api/v1/models" \
  -H "X-API-Key: $API_KEY" \
  -F "category=chair" \
  -F "file=@chaise.jpg;type=image/jpeg"
```

La réponse est `202 Accepted`, car la création continue en tâche de fond. Elle contient `id`, `status`, `status_url`, `public_id` et `model_url`. Au départ, l'état peut être `PENDING` ou `RUNNING` ; le lien GLB est absent tant que le modèle n'est pas terminé.

## 2. Consulter le résultat

Reprenez l'identifiant `id` reçu à l'envoi. Chaque route `/api/v1` exige la même clé.

```bash
GENERATION_ID="ID_RECU_DANS_LA_REPONSE"
curl --fail-with-body "$BASE_URL/api/v1/models/$GENERATION_ID" \
  -H "X-API-Key: $API_KEY"
```

L'état réel est `PENDING`, `RUNNING`, `DONE` ou `FAILED`. Pour limiter les appels, consultez la route toutes les 6 à 10 secondes pendant l'attente : le quota de débit inclut les vérifications d'état. Lorsque `DONE` et `model_url` sont présents, téléchargez le fichier :

```bash
curl --fail-with-body "$BASE_URL/api/v1/models/$GENERATION_ID/glb" \
  -H "X-API-Key: $API_KEY" \
  -o chaise.glb
```

Le code HTTP de succès du téléchargement sert des octets GLB ; il ne promet pas une qualité visuelle donnée. Le viewer sert à examiner le résultat, qui reste approximatif car il est créé depuis une seule photo.

## 3. Autoriser puis intégrer un modèle

1. Ouvrez **Mes modèles**, puis la fiche portant l'identifiant reçu.
2. Activez explicitement **Intégration sur un site**. L'activation est désactivée par défaut et ne réussit qu'après `DONE`.
3. Dans le backend de la boutique, demandez `GET /api/v1/models/{id}/integration-code` avec `X-API-Key`. La réponse JSON contient `iframe_html`, `widget_html` et `public_id`.

```bash
curl --fail-with-body "$BASE_URL/api/v1/models/$GENERATION_ID/integration-code" \
  -H "X-API-Key: $API_KEY"
```

L'extrait iframe charge `/embed/{public_id}`. L'extrait widget charge `/static/widget.js` et crée `<forma3d-viewer model="…" height="480"></forma3d-viewer>`. Le script ne reçoit pas la clé API : il ne fait qu'ajouter une iframe au viewer public.

Une version minimale de la balise est :

```html
<script src="https://VOTRE-SERVICE/static/widget.js" defer></script>
<forma3d-viewer model="UUID_PUBLIC_REÇU" height="480" auto-rotate></forma3d-viewer>
```

Remplacez l'adresse et l'UUID par les valeurs réelles retournées par votre instance ; les valeurs ci-dessus sont des marqueurs, pas un modèle de démonstration. La hauteur acceptée par le widget est bornée entre 240 et 1200 px.

## 4. Tester l'exemple HTML fourni

`examples/integration.html` est une petite page de démonstration : elle demande une origine de service et un UUID public, puis charge le widget. Elle n'invente pas d'objet et ne crée pas de GLB.

Depuis un terminal à la racine du dépôt, servez-la sur HTTP :

```bash
python -m http.server 8081
```

Dans une configuration locale de démonstration, ajoutez précisément `http://127.0.0.1:8081` à `EMBED_ALLOWED_ORIGINS` dans votre environnement local, redémarrez le backend, puis ouvrez `http://127.0.0.1:8081/examples/integration.html`. Dans la page, gardez l'origine Forma3D `http://127.0.0.1:8001` et saisissez l'UUID public d'un modèle terminé et activé. Si vous hébergez la page ailleurs, autorisez l'origine exacte réellement visible par le navigateur.

`EMBED_ALLOWED_ORIGINS` est distinct de `API_CORS_ORIGINS`. Un site qui n'effectue aucun `fetch` API direct et affiche seulement le viewer n'a besoin que de l'autorisation `frame-ancestors`. Si son JavaScript appelle aussi l'API, son origine doit en plus apparaître dans `API_CORS_ORIGINS`. Ces deux paramètres refusent `*` et restent vides par défaut.

## Réponses d'erreur et limites

Les erreurs API versionnées utilisent la forme `{ "error": { "code": "…", "message": "…" } }`.

| HTTP | Situation habituelle | Action |
|---|---|---|
| `401` | Clé absente, invalide ou révoquée | Créer une autre clé dans le Studio et la mettre à jour côté serveur intégrateur. |
| `403` | Catégorie inactive/inconnue ou intégration pas activée | Vérifier la catégorie puis activer le modèle depuis sa fiche Studio. |
| `404` | Identifiant inconnu ou GLB devenu indisponible | Vérifier l'identifiant ; une iframe désactivée affiche une page indisponible avec 404. |
| `409` | Demande de téléchargement ou code avant `DONE` | Continuer à consulter l'état sans dépasser le débit. |
| `413`, `415`, `422` | Fichier trop grand, type refusé ou photo invalide | Envoyer JPG/PNG/WebP valide de 10 Mo maximum. |
| `429` | Limite par minute ou quota quotidien | Respecter `Retry-After`, réduire le polling ou attendre le renouvellement du quota. |

Par défaut, une clé peut lancer jusqu'à 20 créations par jour UTC et 10 requêtes par minute sur les routes `/api/v1`. Les valeurs se règlent avec `API_DAILY_GENERATION_LIMIT` et `API_RATE_LIMIT_PER_MINUTE` dans l'environnement local. La création peut aussi échouer si le service gratuit de génération n'est pas disponible : Forma3D ne garantit ni un GPU, ni un délai fixe, ni une qualité donnée.

## Sécurité et portée

- La clé API est un secret serveur. Elle est créée et retournée une seule fois ; SQLite garde son empreinte, pas sa valeur.
- Le viewer d'intégration ne requiert pas la clé API. Après activation, quiconque possède son UUID public peut consulter le modèle. Désactivez l'intégration dans le Studio pour couper les routes publiques.
- La CSP `frame-ancestors` limite les sites pouvant encadrer le viewer. CORS seul ne remplace pas cette règle.
- Les exemples locaux utilisent HTTP sans chiffrement. Toute utilisation depuis un réseau partagé ou déploiement public exige un hébergement HTTPS, une protection d'accès appropriée et la configuration du serveur par la propriétaire.
- Le projet ne comporte pas de compte vendeur, de facturation, de promesse de disponibilité ni de comptes multiples : le Studio n'a qu'un mot de passe propriétaire. Cette intégration est un prototype de démonstration/développement personnel, pas un service de production.

## Vérification de la documentation

Les chemins, paramètres et réponses ci-dessus sont repris des routeurs FastAPI et des tests simulés du dépôt. Ils ne prouvent ni une génération réelle avec le service 3D, ni l'intégration depuis un vrai site marchand, ni l'état de la CI GitHub. Voir `docs/etapes/etape-13.md` à `docs/etapes/etape-17.md` pour le suivi par étape, et `docs/STOCKAGE.md` pour SQLite et la provenance des modèles.
