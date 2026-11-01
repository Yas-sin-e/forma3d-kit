# Sprint 1 — Étape 7 : fiabilité et qualité

Dernière mise à jour : 1 novembre 2026.

## Objectif et état

Rendre l'indisponibilité du fournisseur explicite, protéger le parcours photo-vers-GLB, permettre des réglages TripoSR seulement quand les bornes sont découvertes dans le contrat réel, et comparer chaque modèle à sa photo source.

**Livrable local :** contrôle de santé à délai maximal de 5 secondes, badge en ligne/hors ligne actualisé toutes les 30 secondes, génération bloquée quand le serveur est indisponible, galerie de secours sans modèles fictifs, et conseils de prise de vue.

**Point 0 : en attente.** La reconnexion Colab du 1 novembre 2026 a rendu `Échec : backend non attribué`. Aucun lien n'est disponible ; aucune photo n'a été transmise et aucune génération n'a été effectuée. Le tableau ci-dessous reste vide jusqu'à une session d'inférence dans un environnement autorisé.

## Réglages qualité TripoSR

Le contrat TripoSR réellement enregistré à l'étape 6 a révélé les noms `foreground_ratio` et `mc_resolution`. Les valeurs d'interface observées étaient 0,85 et 256. Le backend peut lire `FOREGROUND_RATIO` et `MC_RESOLUTION` depuis `backend/.env` ou `.env` racine. Il ne fixe aucune plage dans le code : à chaque appel, il redécouvre `view_api()`, lit les bornes numériques publiées dans les paramètres ou `Client.config`, vérifie la valeur, puis refuse un réglage si son nom ou ses bornes ne sont pas disponibles.

L'échantillon `.env.example` laisse ces variables vides : le fournisseur conserve alors les valeurs réelles de l'interface. Les bornes et les trois configurations expérimentales doivent être choisies après lecture d'un `view_api()` réel. Aucun résultat d'étape 7 n'est inventé.

## Tableau d'essais en attente

Après la disponibilité d'un fournisseur autorisé, lire à nouveau son contrat réel et comparer les cinq photos sous trois réglages présents et autorisés par ce contrat. Garder les fichiers d'étape 6, écrire les nouveaux modèles sous un sous-dossier daté distinct et ne rien écraser. Les cases de la dernière colonne sont réservées à l'appréciation visuelle de l'étudiante.

| Photo libre | Configuration observée | Durée mesurée | Taille GLB | GLB 2.0 valide | Note visuelle (étudiante) |
|---|---|---:|---:|---|---|
| stool-met-01.jpg | A — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| stool-met-01.jpg | B — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| stool-met-01.jpg | C — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-bentwood.jpg | A — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-bentwood.jpg | B — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-bentwood.jpg | C — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-met-01.jpg | A — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-met-01.jpg | B — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-met-01.jpg | C — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-met-02.jpg | A — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-met-02.jpg | B — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| chair-met-02.jpg | C — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| side-table-met.jpg | A — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| side-table-met.jpg | B — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |
| side-table-met.jpg | C — en attente du contrat réel | — | — | — | ☐ bon ☐ moyen ☐ mauvais |

## Fichiers et responsabilités

| Fichier | Rôle et raison | Quand il intervient |
|---|---|---|
| `backend/app/config.py` | Lit la cible et les réglages facultatifs sans imposer de bornes imaginées. | Au démarrage et à la création du fournisseur. |
| `backend/app/providers/huggingface.py` | Contrôle le serveur en 5 s, découvre le contrat TripoSR, vérifie les bornes et valide le GLB 2.0. | Au contrôle de santé et à chaque génération. |
| `backend/app/main.py` | Journalise l'absence de `backend/.env` ou `HF_SPACE_ID` sans imprimer l'adresse, et sert `/health/provider`. | Au démarrage d'Uvicorn et lors du contrôle API. |
| `backend/app/services/demo_gallery.py` | Associe uniquement chaque entrée autorisée à sa photo source si le fichier existe. | Lors du chargement de la galerie. |
| `backend/app/routers/models.py` et `backend/app/schemas.py` | Publient une route bornée par identifiant pour la photo source et ajoutent son URL facultative au schéma de galerie. | Quand le navigateur compare un GLB de galerie à sa photo. |
| `frontend/js/api.js` | Centralise le nouvel appel `GET /health/provider`. | À l'ouverture du studio et pendant le rafraîchissement périodique. |
| `frontend/js/main.js` | Affiche l'état serveur, désactive la génération hors ligne et ouvre un GLB de démonstration réel. | Au chargement puis toutes les 30 secondes. |
| `frontend/js/views/uploader.js` | N'autorise l'envoi que si le fournisseur est disponible et qu'une photo est valide. | À la sélection d'une photo et aux mises à jour de disponibilité. |
| `frontend/js/views/viewer.js` | Affiche côte à côte la photo source et le modèle, et libère les URL locales temporaires. | Après une génération ou l'ouverture d'une entrée de galerie avec image source. |
| `frontend/js/views/gallery.js` | Ouvre le premier modèle réellement listé sans créer d'échantillon fictif. | Depuis le bouton de secours hors ligne. |
| `frontend/index.html` et `frontend/css/components.css` | Définissent le badge, les messages hors ligne, les conseils photo et la comparaison visuelle. | Au rendu du studio. |
| `scripts/dev.ps1` | Prépare le venv si besoin, lance pytest, démarre Uvicorn en arrière-plan et ouvre Edge. | Au lancement local de développement. |
| `backend/tests/test_health.py`, `test_huggingface_provider.py`, `test_demo_gallery.py`, `test_frontend.py` | Vérifient la disponibilité, le masquage d'URL, les bornes simulées, les photos source et les états de l'interface sans réseau. | Lors de pytest. |
| `tools/colab/triposr_server.ipynb` | Vérifie l'absence de GPU clairement puis bloque le serveur public sur Colab géré gratuit, conformément à la FAQ. | Pour l'apprentissage et le contrôle du runtime ; le démarrage public est suspendu. |

Les noms actuels `Chaise métal 01` et `02` sont conservés. Ils ne seront renommés qu'après confirmation de ce que montrent les photos.

## Limites

- Colab gratuit ne garantit ni GPU T4, ni attribution de backend, ni durée de session. La FAQ actuelle interdit les services web sans rapport avec le calcul interactif sur les runtimes gérés et indique que l'interface web de génération peut être arrêtée en offre gratuite. Cette intégration ne doit donc pas être présentée comme un service gratuit garanti. [FAQ officielle Colab](https://research.google.com/colaboratory/faq.html), consultée le 1 novembre 2026.
- Un lien Gradio est public et temporaire. La doc Gradio 4.44.1 indique 72 heures ; la documentation actuelle indique une semaine. Le dépôt TripoSR précédemment exécuté installait Gradio 4.8.0. Le projet retient donc 72 heures au plus tard comme limite conservatrice, sans garantie de disponibilité plus tôt. [Guide Gradio 4.44.1](https://www.gradio.app/4.44.1/guides/sharing-your-app) et [guide Gradio actuel](https://www.gradio.app/guides/sharing-your-app), consultés le 1 novembre 2026.
- Stable Fast 3D n'est pas installé. Le dépôt officiel annonce environ 6 Go de mémoire GPU VRAM pour une image. Sa licence est la Stability AI Community License, pas MIT : elle demande un enregistrement pour l'usage commercial et une licence Enterprise au-delà d'un million de dollars de revenus annuels pour l'organisation ou ses affiliés. Vérification au 1 novembre 2026 : [README SF3D](https://github.com/Stability-AI/stable-fast-3d#manual-inference) et [licence SF3D](https://github.com/Stability-AI/stable-fast-3d/blob/main/LICENSE.md).
- L'interface TripoSR publique utilisée à l'étape 6 était sans authentification. Une vraie séance de génération doit employer uniquement des photos libres de droits, sans personne ni donnée personnelle.
- Les modèles de démonstration sont des sorties de l'étape 6 ; leur ouverture hors ligne ne prouve pas une nouvelle génération.
- Le fournisseur ne peut être déclaré en ligne par `/health/provider` que si son contrat répond ; cette sonde ne garantit pas la réussite d'une génération.

## Vérifications à la fin de cette étape

Les tests de cette étape sont simulés et sans réseau. La vérification de la session Colab, d'une vraie génération, de l'affichage Edge et du téléchargement reste en attente de la disponibilité d'un environnement autorisé. La comparaison visuelle et la notation bon/moyen/mauvais restent réservées à l'étudiante.
