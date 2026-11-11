# Alternatives au fournisseur 3D actuel (TripoSR)

Rôle : comparer les fournisseurs image-vers-3D gratuits pouvant remplacer TripoSR, et proposer un plan de migration.
Utilisation : document de décision pour le Sprint 6 (non démarré). **Aucun fournisseur n'a été changé** : le contrat du projet interdit tout changement de fournisseur sans OK explicite.

Recherche effectuée le 11 novembre 2026. Les offres gratuites changent souvent ; les chiffres ci-dessous viennent en partie de sites tiers qui se contredisent. **Revérifier chaque ligne sur le site officiel avant toute décision.**

## Problème constaté

- TripoSR (Colab + Gradio) produit des formes grossières, des textures floues et des proportions parfois déformées.
- Le serveur Colab gratuit tombe ou expire souvent ; la FAQ Colab ne garantit ni le GPU ni la durée.
- Contraintes à respecter : 100 % gratuit sans carte bancaire, modèle pré-entraîné, sortie GLB, licence compatible avec une soutenance, disponibilité raisonnable.

## Tableau comparatif

| Service | Qualité estimée (exemples publics) | API gratuite ? | Sortie | Temps | Disponibilité | Licence | Intégration |
|---|---|---|---|---|---|---|---|
| **TripoSR** (actuel) | Faible à moyenne ; formes simplifiées | Oui (auto-hébergé sur Colab) | GLB/OBJ | 83 à 215 s mesurés (étape 6) | Instable (Colab gratuit) | MIT | Gradio, déjà intégré |
| **Tripo3D API** (tripo3d.ai) | Nettement meilleure que TripoSR | **Non vérifiée.** Crédits gratuits sur le site web (100/jour ou 300/mois selon les sources) ; l'API semble réservée aux offres payantes (~20 $/mois) | GLB, FBX, OBJ, USDZ | Dizaines de secondes à quelques minutes | Serveur commercial stable | Free : usage commercial non autorisé selon un guide tiers | API REST + SDK |
| **Meshy.ai** | Bonne, textures PBR | **Non.** Free = 100 crédits/mois sur l'application web ; l'API demande l'offre Pro | GLB, FBX, OBJ, USDZ | ~1 à 3 min | Stable | Free : CC BY 4.0 (attribution) | API REST |
| **Hyper3D Rodin** | Très bonne (Gen-2.5) | **Non.** Free = génération/aperçu, téléchargement payé en crédits ; l'API est indiquée dans l'offre Business (~120 $/mois) | GLB, FBX, OBJ, USDZ, STL | ~1 à 2 min | Stable | Droits commerciaux avec crédits payés | API REST |
| **TRELLIS / TRELLIS.2** (Microsoft) | Bonne à très bonne, l'une des meilleures en open source | Oui via le Space HF public (ZeroGPU, quota par compte) ou auto-hébergé | GLB | ~30 s à quelques minutes, plus la file | Space public : file d'attente et quota ZeroGPU ; Colab : GPU lourd (modèle 4B pour TRELLIS.2) | Modèle et code : MIT ; usage commercial des sorties à vérifier (dépendances) | Gradio (`gradio_client`) |
| **InstantMesh / OpenLRM** | Moyenne à bonne (multi-vues) | Oui via Space HF ou Colab | GLB/OBJ | ~30 s à 1 min plus la file | Spaces souvent en veille ou en erreur | Apache 2.0 | Gradio |
| **Stable Fast 3D** (Stability AI) | Moyenne, rapide | Oui via Space HF | GLB | Quelques secondes | Space instable | Stability AI Community License (gratuite sous seuil de chiffre d'affaires) | Gradio — **déjà testé : 5 échecs** sur l'exception interne Gradio générique, aucun GLB reçu (`docs/etapes/etape-06.md`) |

## Lecture du tableau

- **Les trois services commerciaux (Tripo3D, Meshy, Rodin) ont la meilleure qualité, mais aucun ne propose d'API gratuite vérifiée.** Leur offre gratuite passe par l'application web, ce qui ne permet pas une intégration automatique sans carte bancaire. Ils sont donc **incompatibles avec la contrainte « 100 % gratuit »** pour l'API.
- **TRELLIS est le meilleur compromis gratuit** : qualité nettement supérieure à TripoSR, licence MIT, sortie GLB, et une interface Gradio identique à celle que le projet sait déjà inspecter avec `view_api()`.
- Sa limite est la même famille de risque qu'aujourd'hui : file d'attente et quota ZeroGPU sur le Space public, ou besoin d'un GPU puissant en auto-hébergement. Ce risque doit être annoncé honnêtement pendant la démonstration.

## Recommandation

**TRELLIS (Space Hugging Face public de Microsoft), derrière l'interface `Image3DProvider` existante**, en gardant TripoSR comme fournisseur de repli et les exemples pré-générés pour une démonstration sans réseau.

Ne pas envoyer de photo contenant des données personnelles à un Space public ; vérifier la licence du Space et des dépendances avant tout usage non scolaire.

## Plan de migration en 3 étapes (à valider avant le Sprint 6)

1. **Tester l'API réelle.** Avec un script local : `Client("<space-trellis>").view_api()`, noter le nom de la fonction, les paramètres et les sorties exactes (aucun nom inventé). Générer 3 à 5 objets du jeu de l'étape 6 et comparer visuellement aux GLB TripoSR. Noter les temps, la file et les messages de quota.
2. **Créer un adaptateur Python.** Nouveau fichier `backend/app/providers/trellis_provider.py` implémentant `Image3DProvider` : lecture du contrat au moment de la génération, délai maximal, relance limitée, erreurs explicites, validation GLB 2.0 identique à l'actuelle. Ajouter les tests pytest avec un client Gradio simulé.
3. **Basculer par configuration.** Ajouter `IMAGE3D_PROVIDER=triposr|trellis` dans `.env.example` (valeur par défaut `triposr`), sélectionner l'adaptateur au démarrage, puis changer la valeur uniquement dans le `.env` local. Retour arrière immédiat en remettant `triposr`.

## Sources consultées

- [Tripo3D — guide crédits et tarifs](https://www.tripo3d.ai/getting-started/zero-to-3d-getting-started-credits-pricing-guide), [tracker yangmao.ai Tripo](https://yangmao.ai/en/providers/tripo/free-tier/)
- [Meshy — Pricing & Credits (docs officielles)](https://docs.meshy.ai/pricing), [Meshy API pricing](https://docs.meshy.ai/en/api/pricing)
- [Hyper3D — page tarifs](https://hyper3d.ai/pricing), [CostBench — offre gratuite Rodin](https://www.costbench.com/software/ai-3d-generation/rodin-hyper3d/free-plan/)
- [microsoft/TRELLIS (GitHub)](https://github.com/microsoft/TRELLIS), [TRELLIS.2-4B (Hugging Face)](https://huggingface.co/microsoft/trellis.2-4b), [question sur l'usage commercial des sorties](https://github.com/microsoft/TRELLIS/issues/305)
- Historique interne : `docs/etapes/etape-03.md` (Stable Fast 3D) et `docs/etapes/etape-06.md` (mesures TripoSR).
