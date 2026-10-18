# Étape 1 — Cadrage et fondations

## Objectif et résultat vérifiable

Définir le périmètre du MVP, ses contraintes, ses principes produit et ses fondations visuelles. Le résultat vérifiable est un ensemble cohérent de cinq documents relus : AGENTS.md, PRODUCT.md, DESIGN.md, docs/ETAT.md et docs/etapes/etape-01.md.

Aucun code applicatif n’est produit pendant cette étape. L’étape 2 n’est pas commencée. L’autorisation de poursuivre reste conditionnée au « OK » explicite de l’étudiante après la revue.

## Décisions de cadrage recueillies

| Sujet | Décision | Effet sur le projet |
|---|---|---|
| Catégorie MVP | Petit mobilier simple : tabouret, chaise, table d’appoint | Concentre les essais sur des objets utiles au futur aménagement |
| Suivi Scrum | GitHub Projects | Centralise les tâches dans l’écosystème du dépôt |
| Soutenance | Dans environ deux semaines à partir du 18 octobre 2026, vers le 1er novembre 2026 | La date exacte reste à confirmer ; le calendrier est serré |
| Niveau Python | Avancé | Les explications restent nécessaires pour justifier les choix en soutenance |
| Niveau React | Avancé | Le frontend peut suivre la stack prévue sans parcours d’apprentissage débutant |

## Revue des 11 étapes

| Étape | Objectif et résultat vérifiable | Estimation indicative | Risque principal |
|---|---|---:|---|
| 1. Cadrage et fondations | Définir le produit et le design ; documents de fondation complets | 45–90 min | Périmètre ou décisions qui changent |
| 2. Dépôt et structure | Dépôt GitHub, organisation du code et CI fonctionnelle | 1–2 h | Accès au dépôt et configuration CI |
| 3. Faisabilité 3D gratuite | Trois photos testées, sorties GLB et fournisseur choisi | 2–4 h | Indisponibilité, attente, quotas ou qualité |
| 4. Backend socle | API FastAPI, SQLite/SQLAlchemy, configuration et tests | 3–5 h | Schéma et configuration |
| 5. Prétraitement | Contrôle photo et suppression du fond vérifiés sur des exemples | 2–4 h | Variabilité des images et ressources nécessaires |
| 6. Fournisseur et maillage | Fournisseur implémenté derrière Image3DProvider, GLB nettoyé | 3–6 h | API du Space et qualité des maillages |
| 7. Jobs et stockage | Génération en arrière-plan, stockage et état consultables | 2–4 h | Reprise et gestion d’erreurs |
| 8. Base frontend | Application Next.js lancée et conforme à DESIGN.md | 3–5 h | Intégration visuelle |
| 9. Viewer 3D | GLB chargé avec rotation, déplacement de caméra et zoom | 3–6 h | Qualité des modèles et performances |
| 10. Canevas | Objets transformables, inspecteur et export démontrés | 4–8 h | Complexité des interactions 3D |
| 11. Finalisation | Tests E2E, documentation de soutenance et déploiement tenté | 4–8 h | Limites des offres gratuites |

Les durées sont des estimations de travail, pas des garanties. Les étapes 1 à 9 composent le MVP ; les étapes 10 et 11 sont respectivement une extension et la finalisation.

## Options étudiées et recommandation

1. **Cibler dès le MVP plusieurs catégories d’objets :** couverture plus large, mais davantage de cas visuels difficiles à tester.
2. **Cibler le petit mobilier simple :** cohérent avec le futur canevas et assez ciblé pour comparer les générations.
3. **Cibler la décoration opaque :** objets souvent isolés et faciles à photographier, mais lien moins direct avec l’aménagement prévu.

**Recommandation retenue :** petit mobilier simple, avec des essais sur tabouret, chaise et table d’appoint. Le rendu d’une photo unique reste expérimental ; la qualité doit être jugée à l’étape 3 avant de s’engager sur un fournisseur.

## Fichiers de l’étape

### AGENTS.md

Rassemble les contraintes permanentes, la méthode en onze étapes, le cycle de travail, l’architecture prévue et les commandes de référence. Il sert de règle de collaboration pour les prochaines sessions.

**Pourquoi ce choix :** garder les contraintes gratuites, sans entraînement et le passage d’étape avec accord explicite dans un seul fichier de référence.

### PRODUCT.md

Décrit l’utilisateur visé, le parcours photo-vers-viewer, le périmètre du MVP, ses exclusions, ses critères d’acceptation et ses limites.

**Pourquoi ce choix :** éviter que l’implémentation du viewer ou le canevas élargisse le MVP sans décision consciente.

### DESIGN.md

Fixe la direction visuelle, la palette, la typographie, les composants, le mouvement et les règles d’accessibilité.

**Pourquoi ce choix :** donner une référence unique avant de commencer l’interface, sans imposer de service payant ou de police distante.

### docs/ETAT.md

Indique les livrables produits, les décisions, le travail restant et le fait que la poursuite attend le « OK ».

**Pourquoi ce choix :** transmettre l’état concret du projet aux sessions suivantes sans confondre documents écrits et étape validée.

### docs/etapes/etape-01.md

Conserve les décisions de cadrage, la revue du plan, les estimations, les risques et la procédure de vérification des documents.

**Pourquoi ce choix :** fournir un support de révision et de soutenance qui explique aussi pourquoi les décisions ont été prises.

## Lancement et vérification

Cette étape ne contient ni application ni fonction logicielle à lancer. Elle n’ajoute donc pas de tests automatisés.

Depuis le dossier du projet, vérifier la présence des documents avec PowerShell :

- Test-Path -LiteralPath 'AGENTS.md'
- Test-Path -LiteralPath 'PRODUCT.md'
- Test-Path -LiteralPath 'DESIGN.md'
- Test-Path -LiteralPath 'docs/ETAT.md'
- Test-Path -LiteralPath 'docs/etapes/etape-01.md'

Lire chaque document avec Get-Content -LiteralPath 'chemin' -Raw. Les vérifications de code et les commandes de lancement seront ajoutées aux étapes qui introduiront effectivement du code.

## Risques et limites confirmés

- La soutenance est estimée dans deux semaines ; cela rend l’étendue complète ambitieuse, même avec un niveau avancé en Python et React.
- Les services gratuits peuvent dormir, imposer une file ou un quota, changer d’API ou devenir indisponibles.
- Une image unique ne permet pas de promettre des dimensions exactes ni une reconstruction fidèle des côtés invisibles.
- Vérifier les licences des modèles et ne transmettre aucune photo personnelle à un Space public.
- Un modèle pré-généré peut stabiliser une démonstration, mais doit être explicitement étiqueté comme pré-généré.
- Le catalogue de skills visible dans cette session ne contenait pas taste-skill, impeccable, playwright-cli ni img2threejs ; ils n’ont donc pas été utilisés.

## Revue de l’étape

Relecture effectuée après rédaction : les documents s’alignent sur le périmètre petit mobilier, le suivi GitHub Projects, les contraintes de gratuité et d’absence d’entraînement, et la règle d’accord explicite entre les étapes.

**Statut :** revue documentaire terminée ; attente du « OK » de l’étudiante. Ne pas commencer l’étape 2 avant cet accord.
