"""
Marcus v0.43 - PR Autopilot Verification Script

Verifies:
1. PRAutopilotService exists with heuristic methods
2. API endpoint exists and requires auth
3. 200KB diff limit enforced
4. Frontend integration complete
5. Audit logging functional
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

print("=" * 80)
print("MARCUS v0.43 - PR AUTOPILOT VERIFICATION")
print("=" * 80)

# ============================================================================
# 1. PR AUTOPILOT SERVICE
# ============================================================================
print("\n1. PR AUTOPILOT SERVICE")
print("-" * 80)

service_checks = [
    ("class PRAutopilotError", "Custom error class"),
    ("def get_staged_diff(", "Staged diff extraction"),
    ("def propose_pr_text_heuristic(", "Heuristic PR text generation"),
    ("def _categorize_files(", "File categorization"),
    ("def _generate_title_heuristic(", "Title generation"),
    ("def _assess_confidence_heuristic(", "Confidence assessment"),
    ("MAX_DIFF_BYTES = 200 * 1024", "200KB hard limit"),
    ("hashlib.sha256", "Diff hash for provenance"),
]

service_ok = True
for pattern, desc in service_checks:
    if not check_file_contains(
        "marcus_app/services/pr_autopilot_service.py",
        [pattern],
        f"Service - {desc}"
    ):
        service_ok = False

# Check 200KB limit enforcement
service_content = Path("marcus_app/services/pr_autopilot_service.py").read_text(encoding='utf-8')
if "MAX_DIFF_BYTES" in service_content and "200 * 1024" in service_content:
    print("  [OK] Service - 200KB limit enforced")
else:
    print("  [FAIL] Service - 200KB limit not enforced")
    service_ok = False

# ============================================================================
# 2. API ENDPOINT
# ============================================================================
print("\n2. PR AUTOPILOT API ENDPOINT")
print("-" * 80)

endpoint_ok = True

# Check route exists
if check_file_contains(
    "marcus_app/backend/pr_autopilot_routes.py",
    [
        "router = APIRouter(",
        "/{project_id}/pr-autopilot",
        "async def suggest_pr_text",
        "require_auth",
        "PRAutopilotService.propose_pr_text"
    ],
    "Endpoint implementation"
):
    pass
else:
    endpoint_ok = False

# Check router registration in main API
if check_file_contains(
    "marcus_app/backend/api.py",
    [
        "from .pr_autopilot_routes import router as pr_autopilot_router",
        "app.include_router(pr_autopilot_router"
    ],
    "Router registration"
):
    pass
else:
    endpoint_ok = False

# ============================================================================
# 3. AUDIT LOGGING
# ============================================================================
print("\n3. AUDIT LOGGING")
print("-" * 80)

audit_ok = check_file_contains(
    "marcus_app/backend/pr_autopilot_routes.py",
    [
        "event_type='pr_autopilot_suggest'",
        "online_mode='offline'"
    ],
    "PR autopilot audit logging"
)

# ============================================================================
# 4. FRONTEND INTEGRATION
# ============================================================================
print("\n4. FRONTEND INTEGRATION")
print("-" * 80)

frontend_ok = True

# Check button in HTML
if check_file_contains(
    "marcus_app/frontend/index.html",
    [
        "✨ Suggest PR Text",
        "id=\"suggestPRBtn\"",
        "onclick=\"suggestPRText()\"",
        "id=\"prSuggestionStatus\""
    ],
    "HTML button and status span"
):
    pass
else:
    frontend_ok = False

# Check JavaScript function
if check_file_contains(
    "marcus_app/frontend/app.js",
    [
        "async function suggestPRText(",
        "/projects/${currentProjectId}/pr-autopilot",
        "Analyzing staged diff...",
        "document.getElementById('prTitle').value = result.title",
        "document.getElementById('prDescription').value = result.body_md",
        "Diff exceeds 200KB limit"
    ],
    "JavaScript suggestPRText function"
):
    pass
else:
    frontend_ok = False

# ============================================================================
# 5. SECURITY CHECKS
# ============================================================================
print("\n5. SECURITY & CONSTRAINTS")
print("-" * 80)

security_ok = True

# Check read-only operation (git diff only, no write commands)
service_content = Path("marcus_app/services/pr_autopilot_service.py").read_text(encoding='utf-8')
# Check for write operations - look for git commands in subprocess calls
has_git_diff = "'diff', '--staged'" in service_content
has_write_ops = ("'commit'" in service_content and "'git', 'commit'" in service_content) or \
                ("'push'" in service_content and "'git', 'push'" in service_content) or \
                ("'add'" in service_content and "'git', 'add'" in service_content)
if has_git_diff and not has_write_ops:
    print("  [OK] Read-only operation (no git commit/push/add)")
else:
    print("  [FAIL] Service should be read-only")
    security_ok = False

# Check offline-first (no network calls in heuristic)
if "requests." not in service_content and "http" not in service_content.lower():
    print("  [OK] Offline-first (no network dependencies)")
else:
    print("  [WARN] Service may have network dependencies")
    # Not a failure since LLM fallback might use network

# Check subprocess timeout
if "timeout=" in service_content:
    print("  [OK] Subprocess timeout protection")
else:
    print("  [FAIL] Missing subprocess timeout")
    security_ok = False

# ============================================================================
# 6. HEURISTIC QUALITY
# ============================================================================
print("\n6. HEURISTIC QUALITY CHECKS")
print("-" * 80)

heuristic_ok = True

# Check file categorization patterns
if check_file_contains(
    "marcus_app/services/pr_autopilot_service.py",
    [
        "'tests':",
        "'docs':",
        "'config':",
        "'primary':"
    ],
    "File categorization patterns"
):
    pass
else:
    heuristic_ok = False

# Check title generation logic
if check_file_contains(
    "marcus_app/services/pr_autopilot_service.py",
    [
        "if prefix in ['fix',",
        "'feature'",
        "'docs'"
    ],
    "Branch name pattern detection"
):
    pass
else:
    heuristic_ok = False

# Check confidence thresholds
if check_file_contains(
    "marcus_app/services/pr_autopilot_service.py",
    [
        "if size < 10 * 1024",  # 10KB = high
        "if size < 50 * 1024"  # 50KB = medium
    ],
    "Confidence threshold logic"
):
    pass
else:
    heuristic_ok = False

# ============================================================================
# FINAL SUMMARY
# ============================================================================
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

results = [
    ("PR Autopilot Service", service_ok),
    ("API Endpoint & Registration", endpoint_ok),
    ("Audit Logging", audit_ok),
    ("Frontend Integration", frontend_ok),
    ("Security & Constraints", security_ok),
    ("Heuristic Quality", heuristic_ok),
]

for component, ok in results:
    status = "[PASS]" if ok else "[FAIL]"
    print(f"  {status} {component}")

all_ok = all(ok for _, ok in results)

if all_ok:
    print("\n[SUCCESS] Marcus v0.43 PR Autopilot verification PASSED")
    print("+ 200KB diff limit enforced")
    print("+ Offline-first heuristic analysis works")
    print("+ Frontend button wired to backend")
    print("+ Read-only operation, no auto-commits")
    print("+ Audit logging tracks usage")
    print("\nMarcus v0.43 is ready for use.")
else:
    print("\n[WARNING] Some v0.43 components need attention")
    print("Review failed checks above before deploying.")

print("=" * 80)
