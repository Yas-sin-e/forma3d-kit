# 4. Étape 3 — Contrôler la photo, la préparer et enregistrer les fichiers

Fichiers : `backend/app/services/upload_validator.py`, `backend/app/services/image_preparer.py`,
`backend/app/storage/base.py`, `backend/app/storage/local_storage.py`.

## Étape 3.1 — Le videur à l'entrée (`upload_validator.py`)

On ne fait **jamais confiance** à ce qu'envoie le navigateur. Quatre contrôles, dans cet ordre :

```python
MAX_UPLOAD_BYTES = 10 * 1024 * 1024                 # 10 Mo

if not content:                                     # 1. fichier vide         → 400
    raise UploadValidationError("Le fichier est vide.", status_code=400)
if len(content) > MAX_UPLOAD_BYTES:                 # 2. trop gros            → 413
    raise UploadValidationError("La taille maximale autorisée est de 10 Mo.", status_code=413)
expected_type = _FORMATS_BY_EXTENSION.get(extension)
if expected_type is None:                           # 3a. extension refusée   → 415
    raise UploadValidationError("Format refusé. Utilisez un fichier JPG, PNG ou WebP.")
if content_type != expected_type:                   # 3b. type MIME incohérent → 415
    raise UploadValidationError("Le type MIME ne correspond pas à l'extension du fichier.")
if not _SIGNATURES_BY_MEDIA_TYPE[expected_type](content):   # 4. vrais octets ? → 415
    raise UploadValidationError("Le contenu du fichier ne correspond pas à son format déclaré.")
```

### La signature : le contrôle le plus important

```python
_SIGNATURES_BY_MEDIA_TYPE = {
    "image/jpeg": lambda content: content.startswith(b"\xff\xd8\xff"),
    "image/png":  lambda content: content.startswith(b"\x89PNG\r\n\x1a\n"),
    "image/webp": lambda content: content[:4] == b"RIFF" and content[8:12] == b"WEBP",
}
```

Chaque format commence par des **octets magiques**. Un fichier `virus.exe` renommé `photo.jpg`
a la bonne extension et peut-être le bon type MIME, mais **pas** les bons premiers octets : refusé.

### Le nom de fichier nettoyé

```python
safe_filename = (filename or "").replace("\\", "/").rsplit("/", maxsplit=1)[-1]
```

Un nom comme `../../etc/passwd` devient `passwd` : on garde seulement la dernière partie.

### Les codes HTTP

| Code | Sens | Exemple |
|---|---|---|
| 400 | Requête mal formée | fichier vide, nom manquant |
| 413 | Trop gros | photo de 15 Mo |
| 415 | Format non pris en charge | PDF, GIF, faux JPEG |

`ValidatedUpload` (nom propre, type, taille) est le résultat : le reste du code ne reçoit que des données sûres.

## Étape 3.2 — Préparer la photo (`image_preparer.py`)

Les modèles d'IA donnent de meilleurs résultats avec une image **carrée**, l'objet **centré** et
une **marge** autour. On en fait une **copie** ; la photo originale n'est jamais modifiée.

```python
_MINIMUM_SIDE = 512          # côté minimal de l'image préparée
_MARGIN_RATIO = 0.12         # 12 % de marge
_BLUR_VARIANCE_THRESHOLD = 500.0

image = ImageOps.exif_transpose(opened)          # 1. redresse une photo de téléphone tournée
sharpness = self._sharpness_variance(image)      # 2. mesure la netteté
canvas_side = max(_MINIMUM_SIDE, original_width, original_height)
contained = ImageOps.contain(rgb, (content_side, content_side), method=Image.Resampling.LANCZOS)
canvas = Image.new("RGB", (canvas_side, canvas_side), _CANVAS_COLOR)
canvas.paste(contained, offset)                  # 3. centre l'image sur un fond carré gris clair
canvas.save(destination_path, format="PNG")      # 4. enregistre la copie
```

### Mesurer le flou, simplement

```python
grayscale = image.convert("L")                       # noir et blanc
edges = grayscale.filter(ImageFilter.FIND_EDGES)     # garde seulement les contours
return float(ImageStat.Stat(edges).var[0])           # variance des contours
```

Une photo nette a des contours francs, donc une **variance élevée**. Une photo floue a des contours
mous, donc une variance faible (moins de 500 → avertissement).

### Un avertissement, jamais un refus

```python
if min(original_width, original_height) < _MINIMUM_SIDE:
    warnings.append("La photo est petite (un côté fait moins de 512 px) ; ...")
if sharpness < _BLUR_VARIANCE_THRESHOLD:
    warnings.append("La photo semble floue ou manque de détails. ...")
```

L'avertissement est enregistré dans `image_warning` et affiché dans la page Créer, mais la génération
**continue**. C'est la propriétaire qui décide.

## Étape 3.3 — Le contrat de stockage (`storage/base.py`)

```python
class Storage(Protocol):
    def save_image(self, generation_id: str, extension: str, content: bytes) -> Path: ...
    def save_model(self, generation_id: str, content: bytes) -> Path: ...
    def get_model_path(self, generation_id: str) -> Path | None: ...
    def delete_files(self, generation_id: str) -> None: ...
```

`Protocol` = une **interface** Python : la liste des méthodes promises, sans le code.
Aujourd'hui on stocke sur le disque ; demain on pourrait stocker dans un service cloud
en écrivant une autre classe qui tient la même promesse.

## Étape 3.4 — Le stockage sur disque (`local_storage.py`)

```
backend/storage/
    images/  3f9c...e1.jpg     ← photo source
    models/  3f9c...e1.glb     ← modèle 3D
```

### Le nom du fichier est choisi par le serveur

```python
@staticmethod
def _validate_generation_id(generation_id: str) -> None:
    try:
        UUID(generation_id)
    except (ValueError, AttributeError) as error:
        raise ValueError("Identifiant de génération invalide.") from error
```

Le nom vient toujours d'un **UUID** généré par le serveur (`3f9c…e1`), jamais du nom envoyé.
Un UUID ne peut pas contenir `../` : impossible de sortir du dossier de stockage.

### L'écriture atomique

```python
temporary_path = destination.with_name(f".{destination.name}.{uuid4().hex}.tmp")
with temporary_path.open("xb") as temporary_file:
    temporary_file.write(content)
    temporary_file.flush()
    os.fsync(temporary_file.fileno())     # force l'écriture réelle sur le disque
os.link(temporary_path, destination)      # le fichier final apparaît d'un coup
temporary_path.unlink()
```

On écrit d'abord dans un fichier temporaire, puis on le « publie » sous son vrai nom.
Si le serveur s'arrête au milieu, il reste au pire un `.tmp`, **jamais un GLB à moitié écrit**.
`"xb"` = créer un nouveau fichier binaire, en erreur s'il existe déjà.

### La suppression

```python
candidates = [self.models_dir / f"{generation_id}.glb"]
candidates += [self.images_dir / f"{generation_id}{extension}" for extension in sorted(_ALLOWED_IMAGE_EXTENSIONS)]
for path in candidates:
    path.unlink(missing_ok=True)
```

Les noms à effacer sont **reconstruits par le serveur** à partir de l'UUID ; aucun chemin ne vient du client.

## À retenir

> Trois couches de prudence : **valider** (octets magiques), **copier** (l'original n'est jamais touché),
> **écrire atomiquement** (jamais de fichier à moitié écrit).
