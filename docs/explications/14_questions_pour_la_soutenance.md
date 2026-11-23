# 14. Questions possibles pendant la soutenance (avec réponses courtes)

## Architecture

**Comment le backend est-il organisé ?**
En trois couches : les **routeurs** reçoivent les requêtes HTTP, les **services** appliquent les règles,
et les **dépôts / fournisseurs / stockage** parlent à PostgreSQL, à l'IA et au disque. C'est
l'organisation `@RestController` → `@Service` → `@Repository` de Spring Boot.

**Pourquoi des interfaces (`Protocol`) partout ?**
Pour changer un outil sans toucher aux règles : TRELLIS et TripoSR tiennent le même contrat
`generate(image) -> bytes`. Et pour tester sans réseau avec de faux fournisseurs.

**Où sont créés les objets ?**
Une seule fois dans `main.py`, puis rangés dans `app.state`. Les routes les obtiennent par `Depends`.
C'est de l'injection de dépendances.

**Pourquoi `models.py` et `schemas.py` séparés ?**
`models.py` décrit ce que le serveur sait (avec les chemins de fichiers) ; `schemas.py` décrit ce qu'il montre.
Ainsi, aucun chemin du disque ne sort jamais dans une réponse.

## Génération

**Pourquoi répondre 202 au lieu d'attendre le modèle ?**
La génération prend 1 à 3 minutes. On enregistre une fiche PENDING, on répond tout de suite avec une
adresse de suivi, et le travail continue en tâche de fond. Le navigateur consulte l'état toutes les 1,5 s.

**Que se passe-t-il si le serveur redémarre pendant une génération ?**
Au démarrage, `initialize()` passe les fiches PENDING ou RUNNING en FAILED avec le message
« Génération interrompue au redémarrage du serveur ». Rien ne reste bloqué « en cours ».

**Pourquoi appeler `view_api()` avant chaque génération ?**
Pour utiliser le contrat **réel** du Space. Si une fonction a disparu, on s'arrête avec un message clair au lieu
d'envoyer des paramètres inventés.

**Pourquoi un délai global de 300 secondes ?**
Les services gratuits peuvent rester bloqués en file d'attente. Le délai garantit qu'une génération finit toujours
(DONE ou FAILED) ; le travail est annulé côté Space s'il dépasse.

**Pourquoi « finir » le GLB ?**
Les GLB de TripoSR n'ont ni matériau ni normales : ils paraissent noirs et facettés. On ajoute un matériau mat
et des normales sans toucher à la géométrie, et on garde l'original si le résultat n'est pas un GLB valide.

**Pourquoi préparer la photo en carré ?**
Les modèles d'IA attendent une image carrée, l'objet centré avec une marge. On travaille sur une copie ;
l'original est conservé. Une photo floue ou petite donne un avertissement, pas un refus.

## Sécurité

**Comment vérifiez-vous qu'une photo est vraiment une image ?**
Extension, type MIME et surtout les **premiers octets** (signature). Un `.exe` renommé en `.jpg` est refusé (415).

**Comment fonctionne la connexion ?**
Mot de passe unique dans `backend/.env`, comparé en temps constant. En cas de succès, le serveur pose un cookie
`HttpOnly`, `SameSite=Lax`, qui contient une date d'expiration signée par HMAC-SHA256. Modifier la date casse la signature.

**Pourquoi limiter à 5 essais par minute ?**
Pour empêcher d'essayer des milliers de mots de passe. Au-delà : 429 avec `Retry-After`.

**Pourquoi ne garder que l'empreinte de la clé API ?**
Si la base fuit, les empreintes SHA-256 ne permettent pas de retrouver les clés. Le secret n'est montré qu'une fois,
avec `Cache-Control: no-store`.

**Le garde du routeur JavaScript suffit-il ?**
Non, c'est seulement un confort d'affichage. La vraie protection est `require_owner` côté serveur : sans cookie valide,
toute donnée renvoie 401.

**Comment évitez-vous l'injection SQL ?**
Requêtes paramétrées (`%s` + tuple) : les valeurs voyagent à part du texte SQL.

**Pourquoi un `public_id` différent de l'`id` ?**
L'`id` reste interne au Studio. Le `public_id` est donné aux sites partenaires, et même connu, il ne donne accès
à rien tant que l'intégration n'est pas activée.

**Pourquoi toujours la même 404 pour un modèle public refusé ?**
Pour ne pas révéler si un modèle existe mais est privé.

## Intégration

**Quelle différence entre iframe et widget ?**
L'iframe est une simple balise HTML. Le widget `<forma3d-viewer>` est un composant web qui crée l'iframe pour toi,
vérifie l'identifiant, borne la hauteur et isole son style (Shadow DOM).

**Comment empêcher n'importe quel site d'afficher nos modèles ?**
L'en-tête CSP `frame-ancestors` liste les sites autorisés à afficher `/embed` dans une iframe ; par défaut, aucun
site externe. Pour l'API lue depuis un navigateur, CORS est fermé de la même façon.

**Comment éviter qu'une clé API épuise le quota GPU gratuit ?**
Deux limites par clé : 10 requêtes par minute et 20 créations par jour (réglables). Elles sont comptées en base avec
`SELECT ... FOR UPDATE` : même 20 requêtes simultanées ne peuvent pas dépasser la limite.

**Pourquoi `/api/v1` ?**
Pour pouvoir changer le contrat plus tard (`/api/v2`) sans casser les sites partenaires.

## Données et tests

**Pourquoi PostgreSQL et plus SQLite ?**
Décision du projet DevOps : une vraie base serveur, partagée par les conteneurs, avec verrous de ligne et contraintes.
`DATABASE_URL` est obligatoire ; la même image Docker fonctionne partout.

**Comment testez-vous sans appeler l'IA ?**
Les fournisseurs reçoivent un faux client par leur constructeur. Les tests tournent sans réseau, sur une base
`forma3d_test` remise à zéro avant chaque test.

**Le modèle 3D est-il parfait ?**
Non. Le résultat dépend de la photo (objet opaque, fond simple, bonne lumière) et du modèle pré-entraîné.
Les offres gratuites peuvent aussi être en veille ou à court de quota : c'est affiché honnêtement dans le badge
« Serveur 3D », et les exemples pré-générés sont signalés comme tels.

**Qu'améliorer ensuite ?**
1) Une file de travaux persistante pour reprendre une génération après redémarrage. 2) Un stockage objet (cloud)
derrière l'interface `Storage`. 3) Des comptes multiples si le Studio devenait public (aujourd'hui volontairement mono-propriétaire).
