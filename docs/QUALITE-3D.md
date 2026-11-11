# Qualité des modèles 3D — grille et essais de fournisseurs

Rôle : définir comment juger un modèle image-vers-3D et consigner les essais réellement faits.
Utilisation : avant tout changement de fournisseur (Sprint 6, sous-étape C). Grille écrite **avant** les essais du 11 novembre 2026.

## 1. Grille de mesure

Chaque essai utilise les **mêmes photos libres** de `backend/data/feasibility-inputs/` (photos de l'étape 6, sans personne). Les critères automatiques sont mesurés par script ; les critères visuels sont notés par l'étudiante, jamais par le système.

| # | Critère | Comment on le mesure | Type |
|---|---|---|---|
| 1 | Validité GLB | `DemoGallery.is_valid_glb_2()` sur le fichier obtenu | Automatique (oui/non) |
| 2 | Taille du fichier | Octets du GLB | Automatique |
| 3 | Durée | Secondes entre l'appel et la réception du GLB (file d'attente comprise) | Automatique |
| 4 | Contenu du GLB | Sommets, triangles, présence de matériau, de normales et de texture | Automatique |
| 5 | Proportions | Rapport hauteur / largeur / profondeur de la boîte englobante, comparé à l'objet réel | Automatique + jugement |
| 6 | Silhouette | Contour vu de face/trois quarts comparé à la photo | Étudiante (0 à 2) |
| 7 | Structure visible | Pieds distincts, dossier, assise, pas de parties fusionnées ou manquantes | Étudiante (0 à 2) |
| 8 | Faces cachées | Arrière et dessous plausibles (inventés par le modèle) | Étudiante (0 à 2) |
| 9 | Texture / couleur | Ressemblance des couleurs et matériaux avec la photo | Étudiante (0 à 2) |
| 10 | Affichage dans Forma3D | Le GLB s'affiche dans le viewer et se télécharge | Automatique + contrôle |

**Règle de réussite** : un fournisseur ne « réussit » que si Forma3D lui-même obtient le GLB réel, le valide, l'affiche et permet de le télécharger (critères 1 et 10). Un essai par script prouve seulement la faisabilité technique.

**Conditions** : aucun paiement, aucune carte bancaire, aucun contournement de quota ou de file d'attente ; contrat Gradio lu par `view_api()` avant chaque appel ; aucun jeton envoyé à un Space ; échecs consignés tels quels.

## 2. Contrats observés (11 novembre 2026)

| Space | État | Fonction utile | Entrées principales | Sortie |
|---|---|---|---|---|
| `trellis-community/TRELLIS` | En ligne | `/generate_and_extract_glb` | `image`, `multiimages` (plusieurs vues facultatives), `seed`, `ss_guidance_strength`, `ss_sampling_steps`, `slat_guidance_strength`, `slat_sampling_steps`, `multiimage_algo`, `mesh_simplify`, `texture_size` | Vidéo d'aperçu, GLB |
| `microsoft/TRELLIS.2` | En ligne | `/start_session` → `/image_to_3d` → `/extract_glb` | `image`, `seed`, `resolution` (512/1024/1536), réglages d'échantillonnage ; puis `decimation_target`, `texture_size` | GLB |
| `JeffreyXiang/TRELLIS` | `CONFIG_ERROR` | — | — | — |

## 3. Résultats des essais (11 novembre 2026)

| Date | Space | Photo | Résultat observé | GLB obtenu |
|---|---|---|---|---|
| 11/11 | `trellis-community/TRELLIS` | chair-bentwood.jpg | Échec : `AppError: FileNotFoundError` côté Space (appel sans `/start_session`) | Non |
| 11/11 | `trellis-community/TRELLIS` | chair-bentwood.jpg | Arrêt : « You have exceeded your ZeroGPU quota (120s requested vs. 171s left). Try again in 23:58:37 » (quota anonyme) | Non |
| 11/11 | `microsoft/TRELLIS.2` | — | Non essayé : même quota ZeroGPU ; un nouvel appel aurait contourné la limite | — |
| 02/11 (étape 6) | TripoSR (Colab) | 5 photos | Succès, 83 à 215 s ; GLB sans matériau ni normales (voir `docs/etapes/etape-19.md`) | Oui |

**Conclusion honnête : aucun fournisseur alternatif n'a encore été démontré.** Le seul fournisseur prouvé dans Forma3D reste TripoSR. Aucun score visuel n'est inventé : les critères 6 à 9 seront notés par l'étudiante quand un GLB alternatif existera.

## 4. Relancer l'essai sans contournement

L'outil `tools/trials/trial_trellis.py` lit le contrat, ouvre la session, envoie la photo, copie le GLB dans `backend/data/trials/` (ignoré par Git) et imprime les mesures automatiques. Il s'arrête au premier message de quota.

- Attendre le renouvellement du quota (environ 24 h), ou définir un **jeton gratuit** Hugging Face dans la variable `HF_TOKEN` de votre propre terminal : les comptes connectés ont un quota ZeroGPU plus élevé, sans carte bancaire. Le jeton n'est envoyé qu'à huggingface.co.
- Commande (PowerShell, racine du dépôt) :

```text
backend\.venv\Scripts\python.exe tools\trials\trial_trellis.py backend\data\feasibility-inputs\chair-bentwood.jpg backend\data\feasibility-inputs\stool-met-01.jpg backend\data\feasibility-inputs\side-table-met.jpg
```

## 5. Licences et confidentialité à vérifier avant adoption

- TRELLIS (code et poids) est publié sous licence MIT ; l'usage commercial des modèles générés via le Space et de ses dépendances reste une question ouverte sur le dépôt officiel : à confirmer avant tout usage non scolaire.
- Un Space public reçoit les photos envoyées : n'y envoyer que des photos de produits sans personne ni donnée personnelle.
- Plusieurs vues : `trellis-community/TRELLIS` accepte `multiimages` (face, côté, arrière). Cette possibilité n'a pas encore pu être testée ; elle ne sera proposée au vendeur qu'après un essai réussi.

## 6. Étape suivante proposée

1. Relancer l'outil sur 3 photos (chaise, tabouret, table) quand le quota le permet, puis noter les critères 6 à 9.
2. Si TRELLIS fait mieux que TripoSR : écrire un adaptateur `Image3DProvider` choisi par une variable de configuration (TripoSR par défaut), pour qu'une génération passe par Forma3D lui-même, seule preuve de réussite selon la grille.
