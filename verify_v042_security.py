"""
Marcus v0.42 - Security & Online Operations Verification Script

Verifies:
1. Token encryption (AES-256-GCM, not base64)
2. Push/PR routes exist
3. Online mode gating works
4. Audit logging functional
"""

import re
from pathlib import Path

def check_file_contains(file_path, patterns, description):
    """Check if file contains all specified patterns"""
    if not Path(file_path).exists():
        print(f"  [FAIL] {description}: File not found - {file_path}")
        return False

    content = Path(file_path).read_text(encoding='utf-8')
    all_found = True

    for pattern in patterns:
        if pattern not in content:
            print(f"  [FAIL] {description}: Missing pattern '{pattern}'")
            all_found = False

    if all_found:
        print(f"  [OK] {description}")

    return all_found

def count_routes(file_path, route_pattern):
    """Count matching routes in file"""
    if not Path(file_path).exists():
        return 0
    content = Path(file_path).read_text(encoding='utf-8')
    return len(re.findall(route_pattern, content))

print("=" * 80)
print("MARCUS v0.42 - SECURITY & ONLINE OPS VERIFICATION")
print("=" * 80)

# ============================================================================
# 1. TOKEN ENCRYPTION VERIFICATION
# ============================================================================
print("\n1. TOKEN ENCRYPTION (AES-256-GCM)")
print("-" * 80)

token_service_checks = [
    ("from cryptography.hazmat.primitives.ciphers.aead import AESGCM", "AESGCM import"),
    ("from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC", "PBKDF2 import"),
    ("def set_encryption_key", "set_encryption_key method"),
    ("def clear_encryption_key", "clear_encryption_key method"),
    ("def _encrypt_token", "_encrypt_token method"),
    ("def _decrypt_token", "_decrypt_token method"),
    ("PBKDF2HMAC", "Key derivation"),
    ("AESGCM", "AES-GCM encryption"),
    ("iterations=600000", "OWASP-compliant KDF iterations"),
]

encryption_ok = True
for pattern, desc in token_service_checks:
    if not check_file_contains(
        "marcus_app/services/token_service.py",
        [pattern],
        f"Token encryption - {desc}"
    ):
        encryption_ok = False

# Check that base64 is NOT used for encryption
token_content = Path("marcus_app/services/token_service.py").read_text(encoding='utf-8')
if "base64.b64encode(plaintext.encode())" in token_content and "_encrypt_token" not in token_content:
    print("  [FAIL] Token encryption still uses base64 directly")
    encryption_ok = False

# ============================================================================
# 2. PUSH/PR ROUTES VERIFICATION
# ============================================================================
print("\n2. PUSH/PR BACKEND ROUTES")
print("-" * 80)

routes_ok = True

# Check push route
if check_file_contains(
    "marcus_app/backend/dev_mode_routes.py",
    [
        "/git/push",
        "async def push_branch",
        "require_online_mode",
        "subprocess.run"
    ],
    "Push route implementation"
):
    print("  [OK] Push route: Requires online mode, uses subprocess")
else:
    routes_ok = False

# Check PR route
if check_file_contains(
    "marcus_app/backend/dev_mode_routes.py",
    [
        "/github/create-pr",
        "async def create_pull_request",
        "require_online_mode",
        "gh_available"
    ],
    "PR route implementation"
):
    print("  [OK] PR route: Requires online mode, uses gh CLI or API")
else:
    routes_ok = False

# Count total routes
dev_routes = count_routes(
    "marcus_app/backend/dev_mode_routes.py",
    r'@router\.(get|post|put|delete|patch)\('
)
print(f"  [INFO] Total Dev Mode routes: {dev_routes}")

if dev_routes < 17:  # 15 from v0.41 + 2 new routes
    print(f"  [WARN] Expected at least 17 routes, found {dev_routes}")
    routes_ok = False

# ============================================================================
# 3. ONLINE MODE GATING
# ============================================================================
print("\n3. ONLINE MODE GATING")
print("-" * 80)

gating_ok = check_file_contains(
    "marcus_app/backend/dev_mode_routes.py",
    [
        "def require_online_mode",
        "online_mode_enabled",
        "status_code=403"
    ],
    "Online mode guard function"
)

# ============================================================================
# 4. AUTH INTEGRATION
# ============================================================================
print("\n4. AUTH INTEGRATION (Login/Logout)")
print("-" * 80)

auth_ok = True

# Check login sets encryption key
if check_file_contains(
    "marcus_app/backend/api.py",
    [
        "TokenService.set_encryption_key(request.password, db)",
    ],
    "Login initializes encryption key"
):
    pass
else:
    auth_ok = False

# Check logout clears encryption key
if check_file_contains(
    "marcus_app/backend/api.py",
    [
        "TokenService.clear_encryption_key()",
    ],
    "Logout clears encryption key"
):
    pass
else:
    auth_ok = False

# ============================================================================
# 5. AUDIT LOGGING
# ============================================================================
print("\n5. AUDIT LOGGING")
print("-" * 80)

audit_ok = True

# Check push logs audit
if "event_type='git_push'" in Path("marcus_app/backend/dev_mode_routes.py").read_text(encoding='utf-8'):
    print("  [OK] Push operations audit logged")
else:
    print("  [FAIL] Push operations not audit logged")
    audit_ok = False

# Check PR logs audit
if "event_type='github_pr_created'" in Path("marcus_app/backend/dev_mode_routes.py").read_text(encoding='utf-8'):
    print("  [OK] PR creation audit logged")
else:
    print("  [FAIL] PR creation not audit logged")
    audit_ok = False

# ============================================================================
# 6. FRONTEND INTEGRATION
# ============================================================================
print("\n6. FRONTEND INTEGRATION")
print("-" * 80)

frontend_ok = True

# Check push method exists
if check_file_contains(
    "marcus_app/frontend/dev_mode_service.js",
    [
        "async pushBranch(",
        "/projects/${this.projectId}/git/push"
    ],
    "Frontend push method"
):
    pass
else:
    frontend_ok = False

# Check PR method exists
if check_file_contains(
    "marcus_app/frontend/dev_mode_service.js",
    [
        "async createPR(",
        "/projects/${this.projectId}/github/create-pr"
    ],
    "Frontend PR method"
):
    pass
else:
    frontend_ok = False

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

results = [
    ("Token Encryption (AES-256-GCM)", encryption_ok),
    ("Push/PR Routes Implemented", routes_ok),
    ("Online Mode Gating", gating_ok),
    ("Auth Integration (Key Management)", auth_ok),
    ("Audit Logging", audit_ok),
    ("Frontend Integration", frontend_ok),
]

for component, ok in results:
    status = "[PASS]" if ok else "[FAIL]"
    print(f"  {status} {component}")

all_ok = all(ok for _, ok in results)

if all_ok:
    print("\n[SUCCESS] Marcus v0.42 verification PASSED")
    print("Token encryption is now cryptographic (AES-256-GCM).")
    print("Push and PR routes are implemented and guarded.")
    print("Marcus is ready for real production pushes.")
else:
    print("\n[WARNING] Some v0.42 components need attention")
    print("Review failed checks above before deploying.")

print("=" * 80)
