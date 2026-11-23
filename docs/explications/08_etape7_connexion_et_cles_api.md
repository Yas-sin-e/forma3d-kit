# 8. Étape 7 — Qui a le droit d'entrer : connexion et clés API

Fichiers : `backend/app/routers/auth.py`, `backend/app/services/owner_auth.py`,
`backend/app/routers/api_keys.py`, `backend/app/services/api_key_service.py`.

Deux mécanismes, pour deux publics :

| | Connexion du Studio | Clé API |
|---|---|---|
| Pour qui | La propriétaire dans son navigateur | Le serveur d'un site partenaire |
| Preuve | Mot de passe → **cookie de session** | En-tête `X-API-Key: f3d_live_...` |
| Durée | 8 heures | Jusqu'à révocation |
| Gardé côté serveur | Rien (le cookie est **signé**) | Seulement l'**empreinte** SHA-256 |

## Étape 7.1 — Le mot de passe et la session (`owner_auth.py`)

### Vérifier le mot de passe

```python
def verify_password(self, candidate: str) -> bool:
    expected = (self._password_reader() or "").strip()          # FORMA3D_OWNER_PASSWORD
    if not expected:
        raise OwnerPasswordNotConfiguredError("Connexion impossible : ...")
    return hmac.compare_digest(candidate.encode("utf-8"), expected.encode("utf-8"))
```

- Le mot de passe est dans `backend/.env`, **jamais** dans le navigateur ni dans Git.
- `hmac.compare_digest` compare **en temps constant** : la comparaison prend le même temps que le
  mot de passe soit faux dès la 1re lettre ou à la 10e. Un attaquant ne peut pas deviner lettre
  par lettre en mesurant le temps de réponse.
- Sans mot de passe configuré, toute connexion est **refusée** (503).

### Fabriquer le jeton de session

```python
def issue_token(self) -> str:
    expires_at = int(self._clock()) + self.ttl_seconds        # maintenant + 8 h
    payload = f"owner.{expires_at}"
    return f"{payload}.{self._sign(payload)}"                 # « owner.1763400000.Xy3k... »

def _sign(self, payload: str) -> str:
    digest = hmac.new(self._signing_key, payload.encode("ascii"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
```

Le jeton contient **la date d'expiration** et une **signature HMAC-SHA256** calculée avec une clé
secrète que seul le serveur connaît. C'est comme un ticket avec un tampon officiel.

### Vérifier le jeton

```python
def validate_token(self, token: str | None) -> bool:
    if not token or token.count(".") != 2:
        return False
    subject, expires_text, signature = token.split(".")
    if subject != "owner" or not expires_text.isdigit():
        return False
    if not hmac.compare_digest(signature, self._sign(f"{subject}.{expires_text}")):
        return False                                          # signature fausse
    return int(expires_text) > int(self._clock())             # expiré ?
```

Si quelqu'un change la date dans son cookie pour rester connecté plus longtemps, la signature ne
correspond plus : **refusé**. Aucune session n'est stockée en base.

### La clé de signature

`session_key_from_environment()` lit `FORMA3D_SESSION_SECRET` (au moins 32 caractères).
- Vide : clé aléatoire à chaque démarrage → les sessions se ferment au redémarrage.
- Remplie : la session survit à un redémarrage (toujours 8 h au plus).

### Limiter les tentatives

```python
LOGIN_ATTEMPTS_PER_MINUTE = 5

def register(self, client_ip: str) -> None:
    now = self._clock()
    with self._lock:
        attempts = self._attempts[client_ip]
        while attempts and now - attempts[0] >= self._window_seconds:
            attempts.popleft()                                 # oublie les tentatives de plus de 60 s
        if len(attempts) >= self._max_attempts:
            raise LoginRateLimitedError(retry_after)
        attempts.append(now)
```

**Fenêtre glissante** : au plus 5 essais par minute et par adresse IP. Au-delà : **429** et
l'en-tête `Retry-After` (secondes à attendre). Cela empêche d'essayer des milliers de mots de passe.

## Étape 7.2 — Les routes de connexion (`routers/auth.py`)

| Route | Rôle |
|---|---|
| `POST /auth/login` | Vérifie le mot de passe, pose le cookie |
| `POST /auth/logout` | Supprime le cookie |
| `GET /auth/me` | `{"authenticated": true/false, "configured": true/false}` |

```python
response.set_cookie(
    SESSION_COOKIE_NAME, service.issue_token(),
    max_age=service.ttl_seconds,
    httponly=True,                              # illisible par JavaScript
    samesite="lax",                             # pas envoyé par les formulaires d'autres sites
    secure=request.url.scheme == "https",       # seulement en HTTPS quand on est en HTTPS
    path="/",
)
```

- **`httponly`** : même si un script malveillant s'exécutait dans la page, il ne pourrait pas voler le cookie.
- **`samesite="lax"`** : protège contre les requêtes forgées depuis un autre site (CSRF).

### Le garde : `require_owner`

```python
def require_owner(request: Request) -> None:
    if not _service(request).validate_token(request.cookies.get(SESSION_COOKIE_NAME)):
        raise HTTPException(status_code=401, detail="Connexion requise.")
```

FastAPI l'exécute **avant** chaque route du Studio (branché dans `main.py`). Si le cookie est absent
ou faux, la route n'est jamais appelée. Équivalent d'un filtre Spring Security ou d'un garde Angular,
mais **côté serveur** (un garde côté navigateur seul se contourne facilement).

## Étape 7.3 — Les clés API (`api_key_service.py`)

### Créer une clé

```python
_KEY_PREFIX = "f3d_live_"

secret = _KEY_PREFIX + secrets.token_urlsafe(32)                  # « f3d_live_AbCd1234... » (aléatoire)
prefix = secret[: len(_KEY_PREFIX) + 8]                           # « f3d_live_AbCd1234 » (lisible)
record = APIKeyRecord(id=str(uuid4()), name=clean_name, prefix=prefix,
                      fingerprint=self._fingerprint(secret), created_at=datetime.now(UTC))
return self._repository.create_api_key(record), secret            # le secret n'est renvoyé QU'ICI

def _fingerprint(secret: str) -> str:
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()
```

- `secrets.token_urlsafe(32)` : 32 octets aléatoires sûrs (module fait pour la cryptographie).
- La base garde le **préfixe** (pour reconnaître la clé à l'écran) et l'**empreinte** SHA-256.
- La clé en clair n'est **jamais** enregistrée, ni journalisée. Si la base fuit, les clés restent inutilisables.
- C'est la même idée qu'un mot de passe haché : on ne peut pas remonter de l'empreinte à la clé.

### Vérifier une clé reçue

```python
def authenticate(self, candidate: str | None) -> APIKeyRecord | None:
    prefix = supplied[:prefix_length] if supplied.startswith(_KEY_PREFIX) else ""
    fingerprint = self._fingerprint(supplied)
    matches = self._repository.find_api_keys_by_prefix(prefix) if prefix else []
    if not matches:
        hmac.compare_digest(fingerprint, _DUMMY_FINGERPRINT)      # même temps de calcul, même si rien trouvé
        return None
    for record in matches:
        if hmac.compare_digest(fingerprint, record.fingerprint):
            accepted = record
    return accepted
```

1. Le **préfixe** permet de retrouver vite les clés candidates (index en base).
2. L'**empreinte complète** décide, comparée en temps constant.
3. Une fausse comparaison est faite même si rien n'est trouvé : la réponse prend le même temps.

## Étape 7.4 — Les routes des clés (`routers/api_keys.py`)

| Méthode | Adresse | Rôle |
|---|---|---|
| GET | `/api-keys` | Liste : nom, préfixe, date, révoquée ou non (jamais le secret) |
| POST | `/api-keys` | Crée → **201** avec le secret, une seule fois |
| DELETE | `/api-keys/{id}` | **Révoque** (la clé reste visible, barrée) |
| DELETE | `/api-keys/{id}/permanent` | Supprime définitivement → 204 ; **409 si pas encore révoquée** |

```python
response.headers["Cache-Control"] = "no-store"
response.headers["Pragma"] = "no-cache"
```

La réponse qui contient le secret interdit au navigateur de la garder en cache.

### Le garde des routes externes : `require_api_key`

```python
def require_api_key(service = Depends(get_api_key_service),
                    x_api_key: str | None = Header(alias="X-API-Key", default=None)):
    record = service.authenticate(x_api_key)
    if record is None:
        raise HTTPException(status_code=401, detail="Clé API absente, invalide ou révoquée.",
                            headers={"WWW-Authenticate": "ApiKey"})
    return record
```

`Header(alias="X-API-Key")` lit l'en-tête HTTP. Les routes `/api/v1` l'utilisent (étape suivante).

## À retenir

> Rien de secret n'est stocké en clair : le mot de passe reste dans `.env`, la session est **signée**,
> la clé API est **hachée**. Toutes les comparaisons sont **en temps constant**, et les essais sont **limités**.
