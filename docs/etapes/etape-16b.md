# Étape 16b — Refonte visuelle du Studio (frontend uniquement)

Date : 11 novembre 2026. Demandée explicitement par l'étudiante, entre l'étape 16 (5d) et l'étape 17 (5e).

## Objectif et livrable vérifiable

- Objectif : faire passer le Studio d'un prototype à une interface de produit fini, inspirée de Hyper3D/Rodin et Tripo3D, sans framework et sans changer le backend.
- Livrable vérifiable : à l'ouverture, un écran de connexion ; après connexion, un accueil avec chiffres réels, exemples et raccourcis ; des guides intégrés sur les pages Clés API et Fiche modèle ; aucune fonction existante perdue.

## Ce qui a changé

| Fichier | Rôle | Changement |
|---|---|---|
| `frontend/js/auth.js` (nouveau) | Session et verrou d'accès | Mot de passe vérifié dans le navigateur, session en `sessionStorage`, page demandée mémorisée |
| `frontend/js/pages/login.js` (nouveau) | Écran de connexion | Logo, champ mot de passe, bouton « Accéder au Studio », erreur lisible |
| `frontend/js/pages/dashboard.js` (nouveau) | Accueil | Héros avec un vrai modèle du catalogue, 3 chiffres clés, modèles récents, exemples, raccourcis |
| `frontend/js/format.js` (nouveau) | Mises en forme | Dates relatives, tailles, durées, durées mesurées des exemples |
| `frontend/js/views/confirm-dialog.js` (nouveau) | Modale | Remplace `window.confirm()` |
| `frontend/js/views/illustrations.js` (nouveau) | SVG | Cube des états vides |
| `frontend/favicon.svg` (nouveau) | Favicon | Cube Forma3D |
| `frontend/css/theme.css`, `components.css` | Design system | Échelle d'espacement, animations, fichier réécrit en 14 sections |
| `frontend/index.html`, `router.js`, `main.js` | Coque et routes | Icônes, menu Administration, déconnexion, routes protégées, `?query` et `#ancre` |
| Pages `create`, `models`, `examples`, `api-keys`, `categories`, `model-detail` | Pages | Layout 40/60, état vide, compteurs, guide API + curl, intégration guidée, bascule photo/3D |
| `frontend/js/views/gallery.js`, `viewer.js`, `uploader.js`, `categories.js` | Vues | Cartes animées, squelette, vignette photo, modales |

Les routes API, les noms des endpoints et le code Python de l'application sont inchangés.

## Choix justifiés pour la soutenance

- **Connexion temporaire** : la demande précise que le backend `POST /auth/login` viendra après. Le mot de passe par défaut est `forma3d-demo` (constante `TEMPORARY_STUDIO_PASSWORD` dans `auth.js`). Il est lisible dans le code source : c'est un **verrou de démonstration, pas une sécurité**. Le Studio reste réservé à un usage local, comme avant.
- **Aucun chiffre inventé** : la demande proposait « généré en ~2 min » sous chaque exemple. Cette durée n'est pas prouvée pour chaque objet ; les cartes affichent donc les durées **mesurées** à l'étape 6 (de 1 min 23 s à 3 min 35 s).
- **Aperçu d'intégration réel** : l'étape 4 de la fiche affiche la vraie page `/embed/{id}` dans une iframe ; c'est possible car la CSP du viewer autorise `frame-ancestors 'self'`.
- **Message honnête** : la note « Modèle approximatif… » devient « Aperçu 3D généré automatiquement — idéal pour la visualisation produit. La géométrie est une estimation. », placée sous la scène.
- **Pas de Google Fonts** : la pile système (Inter si installée) évite une requête externe et reste conforme à la contrainte « aucune dépendance externe ».

## Tests modifiés

`backend/tests/test_frontend.py` vérifiait d'anciens éléments que la demande supprime explicitement. Seules ces assertions ont été adaptées (aucun code d'application Python modifié) :
- le stepper « Parcours de création » doit maintenant être absent ;
- la nouvelle note « La géométrie est une estimation » remplace l'ancienne phrase ;
- `confirmDialog` remplace `window.confirm` ;
- clé de cache `20261111-ui` au lieu de `20261111-5d`.

Deux tests ont été ajoutés : protection des routes par la connexion, et guides/compteurs/durées honnêtes. Les nouveaux modules sont ajoutés à la liste qui interdit `fetch(` hors de `api.js`.

## Lancement et vérification

```bash
cd backend
.venv\Scripts\python.exe -m pytest -q
```

Résultat obtenu : 101 tests réussis.

Lancement manuel : `uvicorn app.main:app --app-dir backend --port 8000`, puis ouvrir `http://127.0.0.1:8000`.

Vérifié dans le navigateur intégré (serveur local sans `.env`, fournisseur non configuré) : connexion avec mauvais puis bon mot de passe, redirection vers `#/login` après déconnexion, accueil, Créer, Exemples (compteurs), copie d'un exemple, fiche avec activation de l'intégration et aperçu `/embed`, Clés API (création, modale de révocation annulée), Catégories (compteurs, suppression désactivée si utilisée), Mes modèles ; absence de débordement horizontal à 375 px sur les six pages ; aucune erreur console.

## Limites et points non vérifiés

- Aucune génération réelle : le serveur 3D était hors ligne pendant les essais.
- Bascule Vue 3D / Photo / Comparer non testée avec une vraie photo source (les copies d'exemples n'en ont pas).
- Pas de test au lecteur d'écran ni sur un vrai téléphone.
- Les liens « Documentation » et « GitHub » du pied de page pointent vers le dépôt GitHub, privé : ils ne fonctionnent que pour un compte autorisé.
