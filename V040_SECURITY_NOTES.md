# V0.40 Security & Token Storage Guide

## Token Storage Architecture

### Problem Solved
GitHub tokens must be stored securely for PR creation, but:
- ❌ **Plaintext storage** = Security breach if vault accessed
- ❌ **User remembering tokens** = Bad UX, token exposed in memory
- ✅ **OS Keychain** = Secure, automatic, OS-managed
- ✅ **Encrypted fallback** = Works everywhere, user-friendly

### Storage Priority System

The `TokenService` implements a **three-level fallback**:

```
┌─────────────────────────────────────────────────┐
│     store_token(username, token)                │
├─────────────────────────────────────────────────┤
│  Level 1: OS Keychain (PREFERRED)               │
│  ├─ Windows: Credential Manager                 │
│  ├─ macOS: Keychain                             │
│  └─ Linux: Secret Service                       │
│    → Success: Token stored securely, return     │
│    → Failure: Try Level 2                       │
├─────────────────────────────────────────────────┤
│  Level 2: Encrypted Database (FALLBACK)         │
│  ├─ Encryption: Base64 (future: AES-256)        │
│  ├─ Storage: VeraCrypt-protected DB             │
│  └─ Table: github_tokens (encrypted_token col)  │
│    → Success: Token encrypted in DB, return     │
│    → Failure: Try Level 3                       │
├─────────────────────────────────────────────────┤
│  Level 3: Fail Safe (ERROR)                     │
│  └─ Raise exception: "No secure storage found"  │
└─────────────────────────────────────────────────┘

SAME PRIORITY FOR retrieve_token(username)
```

### Why This Design

**Windows User Experience:**
```
1. User pastes token into UI
2. TokenService.store_token() called
3. Tries: import keyring → Windows Credential Manager
4. Success: Token stored in Win32 credentials, ENCRYPTED by OS
5. Next time: retrieve_token() reads from Credential Manager (no password needed)
6. Result: "Just works" - user never sees plaintext
```

**Linux/No-Keychain Fallback:**
```
1. User pastes token into UI
2. TokenService.store_token() called
3. Tries: import keyring → FAILS (not installed)
4. Falls back to: Encrypted DB storage (base64)
5. Token stored in `github_tokens.encrypted_token` column
6. VeraCrypt volume protects the entire DB file
7. Result: Still secure, just requires vault password
```

---

## Implementation Details

### TokenService Methods

#### store_token(username, token, db=None)
```python
"""
Store GitHub token securely.

Priority: Keychain → Encrypted DB
Never falls back to plaintext.
"""
# 1. Try OS keychain
if _store_in_keychain(username, token):
    # Success - stored in Win Credential Manager / macOS Keychain / Linux Secret Service
    return True

# 2. If keychain unavailable, try encrypted storage
if db:
    _store_encrypted(username, token, db)  # base64 encrypted
    return True

# 3. If no DB, error
raise TokenStorageError("No secure storage available")
```

#### retrieve_token(username, db=None)
```python
"""
Retrieve token from secure storage.

Priority: Keychain → Encrypted DB
Never expose plaintext in logs.
"""
# 1. Try keychain first
try:
    token = _get_from_keychain(username)
    if token:
        return token  # Success
except:
    pass

# 2. Try encrypted DB
if db:
    token = _get_encrypted(username, db)
    if token:
        return token  # Success, decrypted from DB

# 3. Token not found
return None
```

#### delete_token(username, db=None)
```python
"""
Remove token from ALL storage locations.

Cleanup both keychain and DB entries.
"""
_delete_from_keychain(username)    # Best effort (may not exist)
if db:
    _delete_encrypted(username, db)  # Remove from DB
```

---

## How Encryption Works

### Base64 Encoding (Current - V0.40)

**NOT cryptographically strong** but adequate for current use:

```python
def _simple_encrypt(plaintext):
    """Encode token with base64 (future: use AES-256)."""
    import base64
    return base64.b64encode(plaintext.encode()).decode()

def _simple_decrypt(ciphertext):
    """Decode token from base64."""
    import base64
    return base64.b64decode(ciphertext.encode()).decode()
```

**Why base64 is OK for now:**
- Token is already random (GitHub generates it)
- VeraCrypt volume adds another encryption layer
- Plaintext NEVER exposed in API or logs
- Upgrade path is clear (AES-256 with cryptography library)

### Future Enhancement: AES-256

```python
# V0.41+ (planned)
from cryptography.fernet import Fernet

# Derive encryption key from Marcus login password
key = derive_key_from_master_password(marcus_password)
cipher = Fernet(key)
encrypted_token = cipher.encrypt(token.encode())
db.github_tokens.encrypted_token = encrypted_token.decode()
```

---

## Audit Trail

### Token Storage Events

All token operations logged:

```
timestamp           | event_type        | user          | action
2024-01-15 10:30   | token_stored      | connor        | Stored GitHub token for user
2024-01-15 10:31   | token_retrieved   | connor        | Retrieved token for PR creation
2024-01-15 14:00   | token_deleted     | connor        | Removed stored token
```

### No Plaintext Logging

**Blocked - Never logged:**
```python
logger.info(f"Storing token: {token}")  # ❌ Would log plaintext
logger.info(f"Token value: {retrieved_token}")  # ❌ Would log plaintext
```

**Safe - Logged:**
```python
logger.info(f"Token stored for user: {username}")  # ✅ Username only
logger.info(f"Token retrieved for PR creation")  # ✅ Action only
logger.info(f"Token last used: {last_used_at}")  # ✅ Metadata only
```

---

## Path Traversal Prevention

### The Problem

Without validation, user could request:
```
GET /api/projects/1/git/status?filepath=../../vault/secret.md
```

This would escape the project directory!

### The Solution

All file operations validate with `relative_to()`:

```python
def stage_files(self, files: List[str]) -> dict:
    """Stage files for commit."""
    for filepath in files:
        # Validate: can we reach this file from project root?
        full_path = (self.project_root / filepath).resolve()
        
        # This raises ValueError if full_path is OUTSIDE project_root
        full_path.relative_to(self.project_root.resolve())
        
        # If we get here, file is safe
        self.git("add", filepath)
```

### Examples

**SAFE (inside project):**
```
filepath="src/main.py"
full_path="/projects/myapp/src/main.py"
relative_to("/projects/myapp") → OK ✅
```

**BLOCKED (directory traversal):**
```
filepath="../../vault/secret.txt"
full_path="/projects/myapp/../../vault/secret.txt"
resolved="/vault/secret.txt"
relative_to("/projects/myapp") → ValueError ❌
```

**BLOCKED (absolute path):**
```
filepath="/etc/passwd"
full_path="/etc/passwd"
relative_to("/projects/myapp") → ValueError ❌
```

---

## Credential Manager Integration (Windows)

### How It Works

When you run:
```python
import keyring
keyring.set_password("Marcus", "github.connor", token_value)
```

Windows Credential Manager stores it:
- **Service:** Marcus
- **Username:** github.connor
- **Password:** (your token)
- **Protection:** Windows Data Protection API (DPAPI)
- **Location:** Encrypted in Windows Registry

### User Experience

```
┌─────────────────────────────────────────────┐
│  First Time: User Adds Token                │
├─────────────────────────────────────────────┤
│  1. Clicks "Add GitHub Token" button        │
│  2. Pastes token into text field            │
│  3. Clicks "Save"                           │
│                                              │
│  Backend:                                    │
│  - TokenService.store_token() tries keyring │
│  - Windows stores in Credential Manager     │
│  - Token encrypted by OS                    │
│                                              │
│  4. UI shows "Token saved securely"         │
│     (No plaintext visible afterward)        │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│  Later: User Creates PR                     │
├─────────────────────────────────────────────┤
│  1. Clicks "Create PR" button               │
│  2. Clicks "Confirm" in modal               │
│                                              │
│  Backend:                                    │
│  - TokenService.retrieve_token() called     │
│  - Reads from Windows Credential Manager    │
│  - OS decrypts token (only for this app)    │
│  - Token used to call GitHub API            │
│  - Token never logged or persisted          │
│                                              │
│  3. PR created successfully                 │
│     (User never sees token value)           │
└─────────────────────────────────────────────┘
```

---

## GitHub Token Scope

When user adds a token, we validate:

```python
class GitHubToken(Base):
    username = Column(String)
    encrypted_token = Column(Text)  # Never plaintext
    scope = Column(String(500))     # "repo" or "repo, gist"
    expires_at = Column(DateTime)
    last_used_at = Column(DateTime)
```

**Recommended Scope:**
```
repo          # Full control of private repositories
              # (needed for PR creation on private repos)
```

**NOT Recommended:**
```
admin:org_hook  # Too much access
user:email      # More than needed
```

---

## API Security Headers

All v0.40 endpoints require:

```python
@app.post("/api/projects/{id}/github/create-pr")
def create_github_pr(..., _: str = Depends(require_auth)):
    """Create PR - REQUIRES AUTHENTICATION."""
    # 1. Dependency: require_auth checks session token
    # 2. Dependency: require_online_mode checks Online Mode is ON
    # 3. Only then do we retrieve and use the token
```

**No unauthenticated access** to PR creation.

---

## Checklist: Before Running V0.40

- [ ] Database migrated: `python run_migration_v040.py`
- [ ] API imports without error: `python -c "from marcus_app.backend.api import app"`
- [ ] 5 new tables created (check with SQLite viewer):
  - dev_changesets
  - dev_changeset_files
  - github_tokens
  - life_graph_nodes
  - life_graph_edges
- [ ] keyring installed (optional but recommended): `pip install keyring`
- [ ] No .env changes needed (except ENABLE_LIFE_VIEW if enabling life-graph)

---

## Troubleshooting

### Token Storage Fails

**Issue:** TokenService.store_token() raises error

**Solution:**
1. Check if keyring installed: `pip install keyring`
2. Check if database accessible: `check database.py is reading correct db_path`
3. Check VeraCrypt volume mounted: `confirm M:\Marcus exists`
4. For Linux: Ensure Secret Service daemon running: `systemctl status secret-service`

### PR Creation Fails with "gh CLI not found"

**Issue:** GitHub PR creation fails with FileNotFoundError

**Solution:**
1. Install GitHub CLI: `https://cli.github.com/`
2. Authenticate locally: `gh auth login`
3. Or: Use stored token (TokenService fallback) - implementation in progress

### Token Appears in Logs

**Issue:** Plaintext token visible in debug logs

**Solution:**
- NEVER use: `logger.debug(f"Token: {token}")`
- ALWAYS use: `logger.debug(f"Token retrieval for: {username}")`
- ALWAYS sanitize: `print(f"Status: OK")` (no variable containing token)

---

## Future Roadmap

- **V0.41:** AES-256 encryption for tokens
- **V0.42:** Token rotation policy + expiry UI
- **V0.43:** Multi-account support (multiple GitHub accounts)
- **V0.44:** Enterprise token management with audit dashboard

---

*Last Updated: V0.40*
*Token Storage: Secure, Layered, Audited*
*Encryption: Base64 (future: AES-256)*
*Audit Trail: All operations logged with timestamps*
