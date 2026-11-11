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
| 11/11 (soir) | `trellis-community/TRELLIS` | chair-bentwood.jpg | Succès avec le jeton gratuit de l'étudiante (saisie masquée) : 85,6 s | Oui |
| 11/11 (soir) | `trellis-community/TRELLIS` | stool-met-01.jpg | Succès : 38,6 s | Oui |
| 11/11 (soir) | `trellis-community/TRELLIS` | side-table-met.jpg | Succès : 82,7 s | Oui |
| 02/11 (étape 6) | TripoSR (Colab) | 5 photos | Succès, 83 à 215 s ; GLB sans matériau ni normales (voir `docs/etapes/etape-19.md`) | Oui |

### Mesures automatiques (critères 1 à 5)

| Photo | Fournisseur | Durée | Valide | Taille | Sommets | Triangles | Matériau | Texture | Normales | Boîte X × Y × Z |
|---|---|---:|---|---:|---:|---:|---|---|---|---|
| chair-bentwood | TripoSR | 215,0 s | oui | 1 236 604 | 30 925 | 61 732 | aucun | non (couleurs par sommet) | non | 0,635 × 1,082 × 0,742 |
| chair-bentwood | TRELLIS | 85,6 s | oui | 1 840 148 | 18 796 | 26 486 | 1 | PNG 1,1 Mo | non | 0,996 × 0,842 × 0,985 |
| stool-met-01 | TripoSR | 83,1 s | oui | 2 619 760 | 65 520 | 130 868 | aucun | non | non | 0,826 × 1,013 × 0,816 |
| stool-met-01 | TRELLIS | 38,6 s | oui | 1 630 440 | 16 070 | 24 392 | 1 | PNG 1,0 Mo | non | 1,001 × 0,703 × 1,001 |
| side-table-met | TripoSR | 83,8 s | oui | 1 035 632 | 25 879 | 51 712 | aucun | non | non | 1,064 × 0,762 × 0,437 |
| side-table-met | TRELLIS | 82,7 s | oui | 1 583 224 | 14 774 | 19 592 | 1 | PNG 1,1 Mo | non | 0,994 × 0,816 × 0,672 |

Les durées TripoSR viennent de l'étape 6 (GPU Colab T4) ; celles de TRELLIS incluent la file d'attente du Space. Les GLB TRELLIS sont rangés dans `backend/data/trials/` (non versionnés).

### Constats techniques

- TRELLIS fournit une **vraie texture** (image PNG plaquée par coordonnées UV) au lieu de couleurs par sommet : c'est le principal gain attendu sur l'aspect.
- Son matériau **n'indique pas `metallicFactor`** : la norme glTF le considère alors comme 100 % métallique, le même défaut d'assombrissement que TripoSR. La correction A ne s'applique pas (elle ignore les matériaux texturés) et la finition B n'ajoute que les normales. Un adaptateur TRELLIS devra donc fixer `metallicFactor = 0` pour ce cas précis.
- Pas de normales non plus : la finition B les ajoutera.
- Proportions : les boîtes TRELLIS sont normalisées autour de 1. Pour la chaise et le tabouret, la hauteur sur l'axe Y paraît plus petite que la largeur : orientation ou proportions **à vérifier visuellement**, rien n'est conclu automatiquement.

**Conclusion honnête** : TRELLIS est **techniquement faisable** (3 GLB valides sur 3, gratuits, avec texture), mais il n'est **pas encore démontré dans Forma3D** : la règle de réussite exige qu'une génération passe par l'application elle-même. Les critères visuels 6 à 9 restent à noter par l'étudiante ; aucune note n'est inventée.

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
