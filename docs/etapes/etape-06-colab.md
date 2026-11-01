# Guide — TripoSR, Colab et limites du serveur public

Dernière mise à jour : 1 novembre 2026.

## Historique vérifié

Le 21 octobre 2026, le notebook a vérifié un runtime Tesla T4 sous Python 3.12.12, installé TripoSR dans le runtime distant et démarré son interface Gradio. Cinq demandes réelles de l'application ont fourni cinq GLB 2.0 valides ; les mesures figurent dans [etape-06.md](etape-06.md). Ce résultat est historique et ne garantit pas qu'une nouvelle session ou un nouveau GPU soit disponible.

Le 1 novembre 2026, la tentative de reconnexion dans Colab a affiché exactement « Échec : backend non attribué ». L'interaction a été arrêtée sans autre tentative, demande payante, validation ou contournement. Aucun nouveau lien n'a été reçu, `backend/.env` n'a pas été modifié, aucune photo n'a été envoyée et aucune nouvelle génération n'a été lancée.

## Pourquoi le serveur public est suspendu

La FAQ officielle de Google Colab indique que les runtimes gérés interdisent l'hébergement de fichiers, le service de médias et les autres services web sans lien avec le calcul interactif. Elle précise que, dans l'offre gratuite, une interface web sur un runtime Colab pour générer du contenu est couramment interrompue et hors des priorités de cette offre. Le serveur public TripoSR/Gradio prévu ici correspond à ce cas d'usage ; le notebook arrête donc explicitement cette cellule. Ce garde-fou ne doit pas être retiré pour relancer le service dans un runtime Colab géré gratuit.

La FAQ ne garantit ni l'accès à un GPU, ni une disponibilité, ni une durée constante. Elle indique aussi qu'une VM gratuite peut être supprimée après inactivité et que la durée de vie est limitée par le service. Source consultée le 1 novembre 2026 : [FAQ officielle Google Colab](https://research.google.com/colaboratory/faq.html).

## À propos du lien Gradio

Un lien `gradio.live` est public à toute personne qui le connaît, sauf authentification explicitement configurée. La documentation Gradio 4.44.1 décrit une expiration après 72 heures ; la documentation Gradio actuelle parle désormais d'une semaine. Le dépôt TripoSR utilisé lors de l'essai précédent dépendait de Gradio 4.8.0, donc la limite de 72 heures reste une borne conservatrice retenue dans le projet. Ni cette durée ni la continuité du runtime ne constituent une garantie de service ; Colab peut arrêter le runtime avant.

Si un environnement distinct et explicitement autorisé fournit un lien, sa valeur doit rester uniquement dans `backend/.env`, sous la clé `HF_SPACE_ID`. Ne jamais l'enregistrer dans Git, un document, un journal ou une capture partagée. Le fichier versionné `.env.example` garde cette valeur vide.

Références consultées le 1 novembre 2026 : [Guide officiel Gradio 4.44.1 sur le partage](https://www.gradio.app/4.44.1/guides/sharing-your-app), [guide Gradio actuel sur le partage](https://www.gradio.app/guides/sharing-your-app).

## Notebook et usage local

`tools/colab/triposr_server.ipynb` conserve les cellules pédagogiques de contrôle GPU et d'installation distante. La première cellule s'arrête avec un message clair si aucun GPU CUDA/T4 n'est attribué. La dernière cellule refuse de lancer le serveur public depuis un runtime Colab géré gratuit et n'essaie ni tunnel alternatif, ni maintien en vie, ni nouveau compte. La compatibilité de ces modifications n'a pas été vérifiée sur un runtime Colab actif ; statut : **non testé sur Colab le 1 novembre 2026**.

Après démarrage local autorisé, `scripts/dev.ps1` lance les tests, démarre Uvicorn et ouvre Edge. Le badge `Serveur 3D` interroge `/health/provider` au chargement et toutes les 30 secondes. Si la cible n'est pas configurée ou ne répond pas en 5 secondes, l'interface désactive la génération et garde l'accès aux modèles locaux déjà présents.

Envoyer uniquement des photos libres de droits, sans personne et sans donnée personnelle. Un GLB de démonstration est une sortie pré-générée et ne prouve pas qu'un nouveau serveur a généré un modèle pendant la démo.
