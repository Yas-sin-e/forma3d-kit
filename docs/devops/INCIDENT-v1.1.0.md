# Compte rendu d'incident — version v1.1.0 (16 novembre 2026)

1. **Ce qui s'est passé :** la v1.1.0 a fait écouter l'API sur le port 8000 au lieu de 8080 (« alignement avec dev.ps1 ») alors que le staging publie toujours `8080` du conteneur ; l'API tournait, le `HEALTHCHECK` interne la disait `healthy`, mais `/health` était injoignable depuis l'hôte.
2. **Quand on l'a su :** à 17:09:30, quand `wait-healthy.sh` a échoué après 6 tentatives ; première ligne utile des journaux : `Uvicorn running on http://0.0.0.0:8000`, à comparer au port publié `127.0.0.1:8080->8080`.
3. **Ce qui a été fait :** `deploy.sh` est revenu automatiquement à `v1.0.0` (dernier tag sain) à 17:09:31, sans aucune reconstruction ; la correction a ensuite été publiée en `v1.1.1` (on ne réécrit pas `v1.1.0`) et mise en service saine à 17:10:44.
4. **Durée d'indisponibilité mesurée :** 39 s, de 17:09:00 (arrêt de v1.0.0, démarrage de v1.1.0) à 17:09:39 (v1.0.0 de nouveau saine).
5. **Ce qui empêchera la récidive :** `check-project.sh` vérifie désormais le « contrat de port » (EXPOSE, CMD et HEALTHCHECK de l'image = port publié par `compose.yaml` et `compose.staging.yaml`) et fait échouer le job `test` de la CI ; la santé est toujours vérifiée depuis l'extérieur du conteneur.

> **Rejoué avec les images réellement publiées sur GHCR** (16/11/2026, 22:43–22:46) : `v1.1.0` refusée
> après 6 tentatives à 22:44:33, retour automatique à `v1.0.1` sain à 22:44:46, puis `v1.1.1` saine à
> 22:46:27 ; au plus 95 s entre le début du déploiement et le retour sain. Sorties : `phase-07.md` §4b.
>
> Versions publiées sur GHCR : la version saine de référence est `v1.0.1` (le tag `v1.0.0`, posé avant la
> fusion, n'a jamais produit d'image). Lors de la répétition ci-dessus, elle portait localement le nom `v1.0.0`.
>
> Répétition réalisée en local avec des images étiquetées localement (`ghcr.io/yas-sin-e/forma3d:v1.1.0`
> et `v1.1.1` construites par `docker build`, non publiées sur GHCR) et `SKIP_PULL=1`. Détails et
> sorties complètes : [phase-07.md](phase-07.md).
