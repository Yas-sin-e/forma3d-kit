# 5. Étape 4 — Le cœur : de la photo au modèle 3D

Fichiers : `backend/app/services/generation_service.py`, `backend/app/providers/base.py`,
`backend/app/providers/trellis.py`, `backend/app/services/glb_finisher.py`.
(`backend/app/providers/huggingface.py`, le fournisseur TripoSR, n'est pas détaillé ici.)

## Étape 4.1 — Le contrat du fournisseur (`providers/base.py`)

```python
class ProviderError(RuntimeError):
    """Erreur compréhensible émise par un fournisseur image-vers-3D."""

class Image3DProvider(Protocol):
    def generate(self, image_path: Path) -> bytes:
        """Renvoie un modèle GLB réellement produit pour cette image."""
```

Tout le projet tient dans cette promesse : **une image entre, des octets GLB sortent**.
Si quelque chose se passe mal, le fournisseur lève une `ProviderError` avec un message lisible.

| Fournisseur | Fichier | Choisi quand |
|---|---|---|
| TripoSR (Colab ou Space) | `huggingface.py` | `IMAGE3D_PROVIDER=triposr` (défaut) |
| TRELLIS (Space public) | `trellis.py` | `IMAGE3D_PROVIDER=trellis` |

## Étape 4.2 — Le chef d'orchestre (`generation_service.py`)

### Il reçoit ses outils, il ne les fabrique pas

```python
class GenerationService:
    def __init__(self, provider: Image3DProvider, storage: Storage,
                 repository: GenerationRepository, image_preparer: ImagePreparer | None = None):
        self._provider = provider
        self._storage = storage
        self._repository = repository
        self._image_preparer = image_preparer or ImagePreparer()
        self._lock = RLock()
```

Les trois premiers paramètres sont des **interfaces**. Le service ne sait pas si le fournisseur est
TRELLIS, TripoSR ou un faux fournisseur de test. Le **verrou** (`RLock`) empêche deux morceaux de code
de modifier la même fiche au même moment.

### Phase 1 — `create_generation()` : la demande est reçue (rapide)

```python
if self._repository.get_category(category_slug) is None:
    raise ValueError("Cette catégorie est inconnue ou désactivée.")
generation_id = str(uuid4())
image_path = self._storage.save_image(generation_id, extension, content)
record = GenerationRecord(id=generation_id, status=GenerationStatus.PENDING, ...)
self._repository.save_generation(record)
return record
```

1. La catégorie existe et est active ? 2. Un UUID est créé. 3. La photo est enregistrée.
4. Une fiche **PENDING** est écrite en base. La route répond alors **202** au navigateur.

### Phase 2 — `run()` : la génération (lente, en tâche de fond)

```python
def run(self, generation_id: str) -> None:
    record = self._repository.get_generation(generation_id)
    if record is None or record.status is not GenerationStatus.PENDING:
        return                                                       # déjà traitée : on ne recommence pas
    running_record = replace(record, status=GenerationStatus.RUNNING, ...)
    self._repository.save_generation(running_record)                 # ① RUNNING

    try:
        with tempfile.TemporaryDirectory(prefix="forma3d-photo-") as temporary_directory:
            preparation = self._image_preparer.prepare(...)          # ② copie carrée
            model_bytes = self._finish_generated_model(
                self._provider.generate(provider_image_path))        # ③ IA + ④ finition
            model_path = self._storage.save_model(generation_id, model_bytes)   # ⑤ fichier GLB
    except ProviderError as error:
        failed_record = replace(..., status=GenerationStatus.FAILED,
                                error_message=redact(str(error)))     # message de l'IA, nettoyé
    except Exception:
        failed_record = replace(..., status=GenerationStatus.FAILED,
                                error_message="La génération a échoué à cause d'une erreur interne.")
    else:
        completed_record = replace(..., status=GenerationStatus.DONE, model_path=model_path, ...)
        self._repository.save_generation(completed_record)           # ⑥ DONE
        return
    self._repository.save_generation(failed_record)                  # ⑥ FAILED
```

Points à savoir expliquer :

- **`try / except / else`** : le bloc `else` ne s'exécute que si **aucune** erreur n'a eu lieu.
- **Deux sortes d'erreurs** :
  - `ProviderError` (le Space dort, quota atteint…) → le message est montré, après `redact()` ;
  - toute autre erreur (bug) → message générique, le détail technique reste dans le journal.
- **`redact()`** remplace le jeton `HF_TOKEN` et l'adresse du serveur 3D par `[valeur masquée]` :
  aucun secret n'arrive jamais à l'écran.
- **Si la préparation échoue**, on envoie la photo originale avec un avertissement : ce n'est pas bloquant.
- **`duration_seconds`** est mesurée avec `monotonic()`, une horloge qui ne recule jamais (même si l'heure du PC change).
- **Dossier temporaire** : la copie préparée disparaît automatiquement à la fin du `with`.

### Les autres méthodes du service

| Méthode | Ce qu'elle fait | Règle importante |
|---|---|---|
| `get_generation(id)` | Lit une fiche | — |
| `get_model_path(id)` | Donne le chemin du GLB | Seulement si DONE **et** fichier présent |
| `list_completed_generations()` | Liste les modèles terminés | Ignore une fiche dont le fichier a disparu |
| `set_integration_enabled(id, True/False)` | Active l'intégration publique | Refusé si le modèle n'est pas DONE |
| `rename_generation(id, nom)` | Renomme | 1 à 80 caractères, sans `/` ni `\`, extension conservée |
| `change_category(id, slug)` | Change la catégorie | Catégorie active uniquement |
| `delete_generation(id)` | Supprime fiche + GLB + photo | **Refusé** si PENDING ou RUNNING (la tâche de fond écrirait un GLB orphelin) |
| `create_library_model(...)` | Enregistre un GLB importé ou un exemple copié | Fichier non vide, taille max, **GLB 2.0 valide** |

## Étape 4.3 — Le fournisseur TRELLIS (`providers/trellis.py`)

TRELLIS est un Space Hugging Face public. On l'appelle comme le ferait sa page web, en 4 temps :

```python
REQUIRED_FUNCTIONS = ("/start_session", "/preprocess_image", "/generate_and_extract_glb")

self._check_contract(client)                                       # 1. les fonctions existent encore ?
self._call(client, deadline, api_name="/start_session")            # 2. ouvre une session côté Space
prepared = output_file_path(self._call(client, deadline,
            image=handle_file(str(source)), api_name="/preprocess_image"))     # 3. détoure le fond
result = self._call(client, deadline, image=handle_file(str(prepared)),
            api_name="/generate_and_extract_glb", **GENERATION_SETTINGS)       # 4. génère le GLB
return HuggingFaceSpaceProvider._read_glb(glb_path)                # vérifie que c'est un vrai GLB 2.0
```

### Vérifier le contrat avant d'envoyer la photo

```python
description = client.view_api(print_info=False, return_format="dict")
missing = [name for name in REQUIRED_FUNCTIONS if name not in endpoints]
if missing:
    raise ProviderError(f"Le contrat du Space TRELLIS a changé : fonctions absentes {missing}.")
```

`view_api()` demande au Space **la liste réelle** de ses fonctions. Règle du projet :
**on n'invente jamais un nom de fonction ou de paramètre**. Si le Space a changé, on s'arrête proprement.

### Un délai global, pas un délai par étape

```python
deadline = self._clock() + self.settings.hf_timeout_seconds        # par défaut 300 s au total

def _call(self, client, deadline, **kwargs):
    remaining = deadline - self._clock()
    if remaining <= 0:
        raise JobTimeoutError("Délai global atteint.")
    job = client.submit(**kwargs)
    try:
        return job.result(timeout=remaining)
    except JobTimeoutError:
        job.cancel()                                               # on libère le Space
        raise
```

Les 4 appels **partagent** les 300 secondes. Si le temps est écoulé, le travail est annulé côté Space.

### Des messages compréhensibles

```python
if "quota" in message.casefold():
    return ("Quota GPU gratuit du Space TRELLIS atteint pour aujourd'hui. Réessayez plus tard ; ...")
```

Le quota GPU gratuit est **limité par jour** : c'est dit clairement, sans aucun contournement.
Le jeton est masqué (`[jeton masqué]`) avant d'écrire le message.

### Le contrôle de santé

```python
url = f"https://huggingface.co/api/spaces/{...}/runtime"
return "ONLINE" if response.json().get("stage") == "RUNNING" else "OFFLINE"
```

C'est ce qu'affiche le badge « Serveur 3D » dans l'en-tête du Studio.

### Pour les tests

```python
def __init__(self, settings=None, client_factory=Client, clock=time.monotonic): ...
```

`client_factory` et `clock` sont des paramètres : les tests donnent un **faux client** et une
**fausse horloge**, donc ils tournent sans réseau et sans attendre.

## Étape 4.4 — La finition du GLB (`glb_finisher.py`)

### Le problème

Les GLB de TripoSR contiennent des positions et une couleur par point, mais **ni matériau ni normales**.

- Sans matériau, la norme glTF impose un matériau **100 % métallique** → le modèle paraît presque noir.
- Sans **normales** (la direction vers laquelle « regarde » chaque point), le modèle paraît **facetté**.

### La solution

```python
PRODUCT_MATERIAL = {
    "name": "forma3d-product",
    "pbrMetallicRoughness": {"baseColorFactor": [1.0, 1.0, 1.0, 1.0],
                             "metallicFactor": 0.0, "roughnessFactor": 0.8},
}
```

`finish_glb(content)` :
1. découpe le GLB en deux blocs : le **JSON** (description) et le **BIN** (nombres) ;
2. ajoute ce matériau **mat** aux pièces qui n'en ont pas ;
3. calcule les normales : pour chaque triangle, on fait la moyenne pondérée par l'aire (`compute_vertex_normals`) ;
4. met `metallicFactor = 0` quand un matériau texturé (cas TRELLIS) l'a oublié ;
5. reconstruit le fichier (chaque bloc complété à un multiple de 4 octets, règle du format).

### La règle de sécurité

```python
finished, report = finish_glb(model_bytes)
if report.changed and DemoGallery.is_valid_glb_2(finished):
    return finished
return model_bytes                 # en cas de doute, on garde l'original
```

Les positions, triangles et couleurs **ne sont jamais modifiés**. Si la structure est inattendue,
on rend le fichier d'origine : **la finition ne fait jamais échouer une génération**.

## À retenir

> `create_generation` répond vite (PENDING) ; `run` travaille ensuite (RUNNING → DONE/FAILED).
> Le fournisseur est interchangeable, appelé selon son **contrat réel** (`view_api`), sous un **délai global**,
> et aucun secret n'apparaît dans les messages.
