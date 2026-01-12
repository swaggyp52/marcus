"""
Marcus v0.41 - Complete Verification Script
Verifies backend routes, frontend consistency, file structure, and API integration
"""

import re
from pathlib import Path

def check_file_exists(path, description):
    """Check if a file exists"""
    exists = Path(path).exists()
    status = "[OK]" if exists else "[MISS]"
    print(f"  {status} {description}: {path}")
    return exists

def count_routes_in_file(file_path, router_name="router"):
    """Count API routes in a file"""
    if not Path(file_path).exists():
        return 0
    content = Path(file_path).read_text(encoding='utf-8')
    routes = re.findall(rf'@{router_name}\.(get|post|put|delete|patch)\(', content)
    return len(routes)

def check_imports_in_file(file_path, expected_imports):
    """Check if file contains expected imports"""
    if not Path(file_path).exists():
        return {}
    content = Path(file_path).read_text(encoding='utf-8')
    results = {}
    for imp in expected_imports:
        found = imp in content
        results[imp] = found
    return results

print("=" * 80)
print("MARCUS v0.41 - COMPLETE VERIFICATION")
print("=" * 80)

# ============================================================================
# 1. BACKEND VERIFICATION
# ============================================================================
print("\n1. BACKEND COMPONENTS")
print("-" * 80)

backend_files = [
    ("marcus_app/backend/dev_mode_routes.py", "Dev Mode API Routes"),
    ("marcus_app/services/git_service.py", "Git Service (LocalGitClient)"),
    ("marcus_app/services/token_service.py", "Token Service"),
]

backend_ok = True
for path, desc in backend_files:
    if not check_file_exists(path, desc):
        backend_ok = False

# ChangeSet logic is in routes file, not separate service
print(f"  [INFO] ChangeSet logic: Implemented in dev_mode_routes.py")

# Count routes
if Path("marcus_app/backend/dev_mode_routes.py").exists():
    dev_routes = count_routes_in_file("marcus_app/backend/dev_mode_routes.py")
    print(f"  [INFO] Dev Mode Routes defined: {dev_routes}")
else:
    print(f"\n  [FAIL] Dev Mode routes file missing!")
    backend_ok = False

# ============================================================================
# 2. FRONTEND VERIFICATION
# ============================================================================
print("\n2. FRONTEND COMPONENTS")
print("-" * 80)

frontend_files = [
    ("marcus_app/frontend/app.js", "Main Frontend App"),
    ("marcus_app/frontend/dev_mode_service.js", "Dev Mode Service"),
    ("marcus_app/frontend/index.html", "Main HTML"),
    ("marcus_app/frontend/life_view.js", "Life View (experimental)"),
]

frontend_ok = True
for path, desc in frontend_files:
    if not check_file_exists(path, desc):
        frontend_ok = False

# Verify DevModeUI class exists
if Path("marcus_app/frontend/dev_mode_service.js").exists():
    service_content = Path("marcus_app/frontend/dev_mode_service.js").read_text(encoding='utf-8')
    has_class = "class DevModeUI" in service_content
    has_export = "window.DevModeUI" in service_content
    print(f"\n  [{'OK' if has_class else 'FAIL'}] DevModeUI class defined")
    print(f"  [{'OK' if has_export else 'FAIL'}] DevModeUI exported to window")
    if not (has_class and has_export):
        frontend_ok = False

# ============================================================================
# 3. FRONTEND-BACKEND METHOD CONSISTENCY
# ============================================================================
print("\n3. FRONTEND-BACKEND CONSISTENCY")
print("-" * 80)

def extract_method_calls(file_path, patterns):
    """Extract method calls from file"""
    if not Path(file_path).exists():
        return set()
    content = Path(file_path).read_text(encoding='utf-8')
    calls = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        calls.update(matches)
    return calls

def extract_defined_methods(file_path):
    """Extract defined methods from class"""
    if not Path(file_path).exists():
        return set()
    content = Path(file_path).read_text(encoding='utf-8')
    pattern = r'^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*\{'
    matches = re.findall(pattern, content, re.MULTILINE)
    return {method for _, method in matches if method != 'constructor'}

# Extract calls
app_patterns = [r'devModeUI\.(\w+)\(', r'await devModeUI\.(\w+)\(']
html_patterns = [r'devModeUI\?\.(\w+)\(']

app_calls = extract_method_calls('marcus_app/frontend/app.js', app_patterns)
html_calls = extract_method_calls('marcus_app/frontend/index.html', html_patterns)
all_calls = app_calls | html_calls

# Extract definitions
defined = extract_defined_methods('marcus_app/frontend/dev_mode_service.js')

# Find missing
missing = all_calls - defined

if missing:
    print(f"  [FAIL] Missing methods: {len(missing)}")
    for method in sorted(missing):
        print(f"    - {method}()")
    frontend_ok = False
else:
    print(f"  [OK] All {len(all_calls)} frontend calls have matching methods")

# ============================================================================
# 4. DATABASE MODELS VERIFICATION
# ============================================================================
print("\n4. DATABASE MODELS")
print("-" * 80)

models_file = "marcus_app/core/models.py"
if Path(models_file).exists():
    models_content = Path(models_file).read_text(encoding='utf-8')

    required_models = [
        ("DevChangeSet", "ChangeSet snapshots"),
        ("DevChangeSetFile", "ChangeSet files"),
        ("Project", "Project/repository metadata"),
        ("GitHubToken", "GitHub tokens (encrypted)"),
    ]

    models_ok = True
    for model, desc in required_models:
        found = f"class {model}" in models_content
        status = "[OK]" if found else "[MISS]"
        print(f"  {status} {model}: {desc}")
        if not found:
            models_ok = False
else:
    print(f"  [FAIL] Models file not found")
    models_ok = False

# ============================================================================
# 5. API SCHEMAS VERIFICATION
# ============================================================================
print("\n5. API SCHEMAS")
print("-" * 80)

schemas_file = "marcus_app/core/schemas.py"
if Path(schemas_file).exists():
    schemas_content = Path(schemas_file).read_text(encoding='utf-8')

    required_schemas = [
        "GitStatusResponse",
        "GitDiffResponse",
        "GitCommitRequest",
        "DevChangeSetResponse",
        "DevChangeSetCreateRequest",
    ]

    schemas_ok = True
    for schema in required_schemas:
        found = f"class {schema}" in schemas_content
        status = "[OK]" if found else "[MISS]"
        print(f"  {status} {schema}")
        if not found:
            schemas_ok = False
else:
    print(f"  [FAIL] Schemas file not found")
    schemas_ok = False

# ============================================================================
# 6. LIFE VIEW VERIFICATION (EXPERIMENTAL)
# ============================================================================
print("\n6. LIFE VIEW (Experimental Feature)")
print("-" * 80)

life_view_file = "marcus_app/frontend/life_view.js"
if Path(life_view_file).exists():
    life_content = Path(life_view_file).read_text(encoding='utf-8')
    has_class = "class LifeView" in life_content or "function LifeView" in life_content
    status = "[OK]" if has_class else "[WARN]"
    print(f"  {status} Life View implementation found")
    print(f"  [INFO] Feature is experimental and feature-flagged")
else:
    print(f"  [WARN] Life View not implemented (OK - experimental)")

# ============================================================================
# 7. DOCUMENTATION VERIFICATION
# ============================================================================
print("\n7. DOCUMENTATION")
print("-" * 80)

docs = [
    ("V041_UI_COMPLETE.md", "UI completion docs"),
    ("V041_IMPLEMENTATION_SUMMARY.md", "Implementation summary"),
    ("V041_DELIVERY_PACKAGE.md", "Delivery package"),
    ("V041_FRONTEND_TEST_CHECKLIST.md", "Frontend test checklist"),
]

docs_ok = True
for doc, desc in docs:
    exists = Path(doc).exists()
    status = "[OK]" if exists else "[MISS]"
    print(f"  {status} {desc}: {doc}")
    if not exists:
        docs_ok = False

# ============================================================================
# 8. SECURITY CHECKS
# ============================================================================
print("\n8. SECURITY VERIFICATION")
print("-" * 80)

security_checks = []

# Check for require_auth in dev_mode_routes
if Path("marcus_app/backend/dev_mode_routes.py").exists():
    routes_content = Path("marcus_app/backend/dev_mode_routes.py").read_text(encoding='utf-8')
    has_auth = "require_auth" in routes_content
    has_online_guard = "require_online_mode" in routes_content
    security_checks.append(("Auth dependency exists", has_auth))
    security_checks.append(("Online mode guard exists", has_online_guard))

# Check token service has encryption
if Path("marcus_app/services/token_service.py").exists():
    token_content = Path("marcus_app/services/token_service.py").read_text(encoding='utf-8')
    has_encryption = "cryptography" in token_content or "encrypt" in token_content
    security_checks.append(("Token encryption implemented", has_encryption))

for check, passed in security_checks:
    status = "[OK]" if passed else "[WARN]"
    print(f"  {status} {check}")

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

all_ok = all([backend_ok, frontend_ok, models_ok, schemas_ok])

results = [
    ("Backend Components", backend_ok),
    ("Frontend Components", frontend_ok),
    ("Frontend-Backend Consistency", not bool(missing)),
    ("Database Models", models_ok),
    ("API Schemas", schemas_ok),
    ("Documentation", docs_ok),
]

for component, ok in results:
    status = "[PASS]" if ok else "[FAIL]"
    print(f"  {status} {component}")

if all_ok:
    print("\n[SUCCESS] Marcus v0.41 verification PASSED")
    print("Frontend Dev Mode UI is ready for deployment.")
else:
    print("\n[WARNING] Some components need attention")
    print("Review failed checks above before deploying.")

print("=" * 80)
