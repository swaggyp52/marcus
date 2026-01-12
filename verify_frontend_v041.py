"""
V0.41 Frontend Consistency Verification Script
Checks that all app.js and index.html calls map to dev_mode_service.js methods
"""

import re
from pathlib import Path

def extract_method_calls(file_path, patterns):
    """Extract method calls from file using patterns"""
    content = Path(file_path).read_text(encoding='utf-8')
    calls = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        calls.update(matches)
    return calls

def extract_defined_methods(file_path):
    """Extract defined methods from DevModeUI class"""
    content = Path(file_path).read_text(encoding='utf-8')
    pattern = r'^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*\{'
    matches = re.findall(pattern, content, re.MULTILINE)
    return {method for _, method in matches if method != 'constructor'}

# Paths
app_js = Path('marcus_app/frontend/app.js')
index_html = Path('marcus_app/frontend/index.html')
service_js = Path('marcus_app/frontend/dev_mode_service.js')

# Extract calls from app.js
app_patterns = [
    r'devModeUI\.(\w+)\(',
    r'await devModeUI\.(\w+)\(',
]
app_calls = extract_method_calls(app_js, app_patterns)

# Extract calls from index.html
html_patterns = [
    r'devModeUI\?\.(\w+)\(',
    r'onclick="devModeUI\?\.(\w+)\(',
]
html_calls = extract_method_calls(index_html, html_patterns)

# Combine all calls
all_calls = app_calls | html_calls

# Extract defined methods
defined_methods = extract_defined_methods(service_js)

# Find missing methods
missing = all_calls - defined_methods

# Results
print("=" * 80)
print("V0.41 FRONTEND CONSISTENCY CHECK")
print("=" * 80)
print(f"\nTotal method calls found: {len(all_calls)}")
print(f"Total methods defined: {len(defined_methods)}")
print(f"Missing methods: {len(missing)}")

if missing:
    print("\n[FAIL] MISSING METHODS IN dev_mode_service.js:")
    for method in sorted(missing):
        print(f"   - {method}()")
    print("\nThese methods are called but not defined in DevModeUI!")
else:
    print("\n[PASS] All called methods are defined in DevModeUI")

# Show all calls for reference
print(f"\nAll DevModeUI method calls from frontend:")
for call in sorted(all_calls):
    status = "[OK]" if call in defined_methods else "[MISS]"
    print(f"   {status} {call}()")

print("\n" + "=" * 80)
