# Agent Specifications & Workflows

Marcus uses role-driven autonomous agents to automate development tasks. Each agent is a self-contained workflow that produces a clear report and optional code changes.

---

## Agent Contract (All Agents Follow This)

Every agent must produce:

1. **Intent** - What it's trying to accomplish (1-2 sentences)
2. **Plan** - Steps it will take (bulleted list)
3. **Edits** - Files that were changed or created
4. **How to Verify** - Exact commands to validate output
5. **Risks & Rollback** - Potential issues and how to undo

Output format: Markdown report in `docs/REPORTS/<timestamp>-<agent>.md`

---

## Agent 1: BuildDoctor

**Intent**: Make the build/run pipeline reliable, fix broken scripts, validate environments.

### Responsibilities
- ✓ Check Python, pip, venv setup
- ✓ Validate requirements.txt can install
- ✓ Compile-check Python backend
- ✓ Ensure PyInstaller is ready
- ✓ Verify build scripts syntax
- ✓ Run smoke test to catch regressions
- ✓ Suggest fixes for common issues (port conflicts, missing deps)

### Input
- (Optional) Specific issue to diagnose (e.g., "EXE won't start")

### Output
1. Environment validation report (Python version, venv status, deps)
2. Build readiness status (green/yellow/red)
3. Suggested fixes for any issues found
4. Step-by-step verification commands

### Plan
```
1. Check Python 3.12 installed & in PATH
2. Check pip installed & functional
3. Check .venv exists, is activated
4. Try: pip install -r requirements.txt (dry-run)
5. Python compile-check on backend/api.py
6. Check PyInstaller installed
7. Validate Marcus_v052.spec exists & is readable
8. Run smoke_test.ps1
9. Report results + recommendations
```

### How to Invoke
```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 builddoctor
```

### Risks & Rollback
- **Risk**: May reinstall packages (safe, non-destructive)
- **Rollback**: None needed; all changes are verification-only

---

## Agent 2: BugHunter

**Intent**: Reproduce bugs, create minimal test cases, suggest targeted fixes.

### Responsibilities
- ✓ Gather reproduction steps from user
- ✓ Set up minimal failing scenario
- ✓ Identify root cause (backend / frontend / build)
- ✓ Create small test case
- ✓ Suggest fix + provide code patch (optional)
- ✓ Create regression test

### Input
- Bug description or issue number
- Steps to reproduce
- Expected vs actual behavior

### Output
1. Minimal reproduction script (.ps1 or .py)
2. Root cause analysis (line numbers, logic error)
3. Suggested fix (code diff)
4. Regression test to prevent re-occurrence

### Plan
```
1. Ask user for repro steps (if not provided)
2. Create isolated test scenario
3. Run scenario, capture error
4. Trace error to source (backend API / frontend JS / build)
5. Identify root cause code
6. Suggest minimal fix
7. Create regression test
8. Output: repro script, analysis, patch, test
```

### How to Invoke
```powershell
# Interactive mode
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 bughunter

# With issue context
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 bughunter -Issue 185
```

### Risks & Rollback
- **Risk**: May modify test files (safe, in-memory only by default)
- **Rollback**: `git checkout` any test files

---

## Agent 3: Refactorer

**Intent**: Refactor code safely with type checks, tests, and before/after comparison.

### Responsibilities
- ✓ Identify refactoring target (function, class, module)
- ✓ Run existing tests (baseline)
- ✓ Perform refactoring
- ✓ Ensure no behavior change (tests still pass)
- ✓ Verify performance (optional: profiling)
- ✓ Check type/lint compliance
- ✓ Generate before/after comparison

### Input
- File or function to refactor
- Refactoring goal (simplify, performance, readability, type safety)

### Output
1. Before/after code comparison
2. Test results (all tests still pass)
3. Type checker report (mypy, pyright)
4. Optional: Performance impact analysis

### Plan
```
1. Identify target code
2. Baseline: Run all tests
3. Analyze code for refactoring opportunities
4. Apply refactoring
5. Rerun all tests (must pass)
6. Run type checker
7. Run linter (if applicable)
8. Generate before/after diff
9. Output report
```

### How to Invoke
```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 refactorer -File backend/api.py
```

### Risks & Rollback
- **Risk**: May change code (on branch, always reversible)
- **Rollback**: `git reset --hard`, `git checkout <branch>`
- **Mitigation**: Always creates branch, requires review before merge

---

## Agent 4: TestWriter

**Intent**: Increase code coverage, write regression tests for fixed bugs.

### Responsibilities
- ✓ Identify low-coverage areas
- ✓ Write unit tests (backend API, models)
- ✓ Write integration tests (multi-endpoint workflows)
- ✓ Write regression tests (prevent bug re-occurrence)
- ✓ Verify tests pass
- ✓ Report coverage delta

### Input
- Coverage report (optional)
- Specific bug to write regression test for
- Feature to write unit tests for

### Output
1. New test files (e.g., `test_api.py`, `test_models.py`)
2. Coverage report (before/after)
3. All tests passing
4. Optional: Coverage threshold check

### Plan
```
1. Analyze code coverage (if pytest available)
2. Identify low-coverage hot spots
3. Write unit tests for uncovered functions
4. Write integration tests for workflows
5. If bug ID provided: write regression test
6. Run all tests (must pass)
7. Generate coverage report
8. Output: new tests, coverage delta
```

### How to Invoke
```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 testwriter
```

### Risks & Rollback
- **Risk**: New test files (safe, can be deleted)
- **Rollback**: `git checkout test_*.py` or `rm test_*.py`

---

## Agent 5: DocIndexer

**Intent**: Keep repo documentation and index up-to-date with code.

### Responsibilities
- ✓ Scan repo for changes (new files, deleted files, modified structure)
- ✓ Update REPO_MAP.md with any structural changes
- ✓ Update DEPENDENCIES.md if requirements.txt changed
- ✓ Rebuild file index (file_index.json)
- ✓ Rebuild symbol index (symbol_index.json) - Python exports, classes, functions
- ✓ Check for orphaned docs (docs that reference deleted code)
- ✓ Ensure AGENTS.md is up-to-date

### Input
- (Optional) Specific files to index
- (Optional) Focus area (backend / frontend / scripts)

### Output
1. Updated docs/REPO_MAP.md (if needed)
2. Updated docs/DEPENDENCIES.md (if needed)
3. Fresh `.agent/index/file_index.json`
4. Fresh `.agent/index/symbol_index.json`
5. Warnings for orphaned references
6. Summary: "Docs are in sync" or "N changes needed"

### Plan
```
1. Scan marcus_v052/ for file changes
2. Check git status (new, deleted, modified files)
3. Update docs/REPO_MAP.md if structure changed
4. Check requirements.txt, update docs/DEPENDENCIES.md if changed
5. Regenerate file_index.json (file list, sizes, timestamps)
6. Regenerate symbol_index.json (Python exports, classes, functions)
7. Scan docs/ for dead links or references to deleted code
8. Report findings
```

### How to Invoke
```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 docindexer
```

### Risks & Rollback
- **Risk**: May modify docs (always safe, human-readable)
- **Rollback**: `git checkout docs/`

---

## Agent 6: ReleaseSheriff

**Intent**: Manage versioning, changelog, CI sanity, release preparation.

### Responsibilities
- ✓ Check version number consistency (README, spec file, code)
- ✓ Verify changelog is up-to-date
- ✓ Ensure all commits since last release are logged
- ✓ Run full test suite
- ✓ Verify EXE can build cleanly
- ✓ Generate release notes
- ✓ Suggest version bump (major/minor/patch)

### Input
- Release type (alpha, beta, RC, stable)
- Previous version (for diff)

### Output
1. Version consistency report
2. Generated CHANGELOG entry (git commits since last tag)
3. Full test suite results
4. Build verification (EXE compiles)
5. Release notes (auto-generated or manual)
6. Suggested version number

### Plan
```
1. Check current version (from spec file, README)
2. Check if versions consistent across codebase
3. Parse git log since last tag
4. Generate CHANGELOG entry
5. Run full test suite (quality.ps1)
6. Verify EXE builds (build_windows_exe.ps1)
7. Suggest version bump based on commits
8. Output release checklist
```

### How to Invoke
```powershell
powershell -ExecutionPolicy Bypass -File scripts\agent.ps1 releasesheriff
```

### Risks & Rollback
- **Risk**: May update version strings (on branch, review before merge)
- **Rollback**: `git reset --hard`

---

## Agent Priority & Interdependencies

```
BuildDoctor (lowest risk, run first)
    ↓
BugHunter, TestWriter (parallel)
    ↓
Refactorer (requires passing tests from TestWriter)
    ↓
DocIndexer (documents what others do)
    ↓
ReleaseSheriff (final validation before release)
```

---

## Configuration

Agent behavior can be customized via `.agent/config.toml`:

```toml
[buildDoctor]
python_version = "3.12"
check_venv = true
run_smoke_test = true

[testWriter]
coverage_threshold = 60  # warn if below
coverage_target = 80     # goal

[docIndexer]
auto_commit_docs = false  # manual review first
generate_symbol_index = true

[releaseSheriff]
version_file = "marcus_v052/Marcus_v052.spec"
auto_changelog = true
```

---

## How Agents Interact with User

### Workflow
```
1. User runs: powershell agent.ps1 <agent-name>
2. Agent validates inputs (asks for missing info)
3. Agent executes plan (may take 1-10 minutes)
4. Agent generates report in docs/REPORTS/<timestamp>-<agent>.md
5. Agent outputs summary to console
6. User reviews report
7. User approves/modifies/rejects agent output
8. If approved: agent commits on new branch or outputs diff for manual merge
```

### Example Session
```powershell
$ .\scripts\agent.ps1 builddoctor

[BuildDoctor] Validating environment...
[BuildDoctor] ✓ Python 3.12.2 found
[BuildDoctor] ✓ pip functional
[BuildDoctor] ✓ venv activated
[BuildDoctor] ✓ requirements.txt valid
[BuildDoctor] ✓ Backend syntax OK
[BuildDoctor] ✓ PyInstaller ready
[BuildDoctor] Running smoke test...
[BuildDoctor] ✓ All tests passed

[BuildDoctor] Report: docs/REPORTS/2025-01-12-builddoctor.md
[BuildDoctor] Status: GREEN (all systems go)
```

---

## Future Enhancements

- [ ] Add `CodeSearcher` agent (find usages, refactoring impact)
- [ ] Add `SecurityAuditor` agent (dependency vulnerabilities, code audit)
- [ ] Add `PerformanceProfiler` agent (identify bottlenecks)
- [ ] Add `MigrationAssistant` agent (major version upgrades)
- [ ] Add `ArchitectureValidator` agent (ensure patterns are followed)

---

## See Also

- [Agent Runner](../scripts/agent.ps1) - Main entrypoint
- [Quality Gate](../scripts/quality.ps1) - Quick sanity checks
- [Indexer](../.agent/scripts/indexer.py) - Repo analysis tool
