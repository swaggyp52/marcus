"""
PR Autopilot Service (v0.43)

Analyzes staged git diffs and proposes PR title/body text.

Safety guarantees:
- Read-only (never modifies files, never stages/commits/pushes)
- Offline-first (works without internet or LLM)
- Size-limited (max 200KB diff to enforce PR hygiene)
- Deterministic heuristics with optional LLM enhancement

Invariant: Marcus proposes, human decides.
"""

import subprocess
import re
from typing import Dict, List, Optional
from pathlib import Path
from datetime import datetime
import hashlib


class PRAutopilotError(Exception):
    """PR Autopilot operation failed."""
    pass


class PRAutopilotService:
    """
    Analyzes staged diffs and generates PR text suggestions.

    Uses:
    1. Heuristic analysis (always available, offline)
    2. Optional LLM (Ollama if available, graceful fallback)
    """

    MAX_DIFF_BYTES = 200 * 1024  # 200KB hard limit
    LARGE_DIFF_THRESHOLD = 50 * 1024  # 50KB = "large" warning

    @staticmethod
    def get_staged_diff(project_path: str) -> Dict:
        """
        Get staged diff and metadata.

        Args:
            project_path: Path to git repository

        Returns:
            {
                'diff': str,  # Full diff text
                'files': List[str],  # Changed file paths
                'stats': {
                    'files_changed': int,
                    'insertions': int,
                    'deletions': int,
                    'diff_size_bytes': int
                },
                'diff_hash': str  # SHA256 hash for provenance
            }

        Raises:
            PRAutopilotError: If git operations fail or diff too large
        """
        try:
            # Get staged diff
            diff_result = subprocess.run(
                ['git', 'diff', '--staged'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=30
            )

            if diff_result.returncode != 0:
                raise PRAutopilotError(f"Git diff failed: {diff_result.stderr}")

            diff_text = diff_result.stdout
            diff_size = len(diff_text.encode('utf-8'))

            # Enforce hard limit
            if diff_size > PRAutopilotService.MAX_DIFF_BYTES:
                raise PRAutopilotError(
                    f"Diff too large ({diff_size} bytes). "
                    f"Max allowed: {PRAutopilotService.MAX_DIFF_BYTES} bytes. "
                    f"Split this into smaller PRs."
                )

            # Get file list
            files_result = subprocess.run(
                ['git', 'diff', '--staged', '--name-only'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            files = [f.strip() for f in files_result.stdout.split('\n') if f.strip()]

            # Get stats
            stats_result = subprocess.run(
                ['git', 'diff', '--staged', '--numstat'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=10
            )

            insertions = 0
            deletions = 0
            for line in stats_result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        try:
                            insertions += int(parts[0]) if parts[0] != '-' else 0
                            deletions += int(parts[1]) if parts[1] != '-' else 0
                        except ValueError:
                            pass

            # Generate diff hash for provenance
            diff_hash = hashlib.sha256(diff_text.encode('utf-8')).hexdigest()[:16]

            return {
                'diff': diff_text,
                'files': files,
                'stats': {
                    'files_changed': len(files),
                    'insertions': insertions,
                    'deletions': deletions,
                    'diff_size_bytes': diff_size
                },
                'diff_hash': diff_hash
            }

        except subprocess.TimeoutExpired:
            raise PRAutopilotError("Git operation timed out")
        except Exception as e:
            raise PRAutopilotError(f"Failed to get staged diff: {str(e)}")

    @staticmethod
    def propose_pr_text_heuristic(diff_data: Dict, base_branch: str, current_branch: str) -> Dict:
        """
        Generate PR title/body using deterministic heuristics.

        Args:
            diff_data: Output from get_staged_diff()
            base_branch: Target branch (e.g., 'main')
            current_branch: Source branch

        Returns:
            {
                'title': str,
                'body_md': str,
                'summary': str,
                'confidence': str,  # 'low' | 'medium' | 'high'
                'method': 'heuristic'
            }
        """
        files = diff_data['files']
        stats = diff_data['stats']
        diff_text = diff_data['diff']

        # Analyze file patterns
        file_categories = PRAutopilotService._categorize_files(files)

        # Generate title
        title = PRAutopilotService._generate_title_heuristic(
            files, file_categories, current_branch
        )

        # Determine confidence
        confidence = PRAutopilotService._assess_confidence_heuristic(stats, files)

        # Generate body
        body_sections = []

        # What changed
        body_sections.append("## What Changed\n")
        if file_categories['primary']:
            body_sections.append(f"- Modified {len(file_categories['primary'])} core files")
        if file_categories['tests']:
            body_sections.append(f"- Updated {len(file_categories['tests'])} test files")
        if file_categories['docs']:
            body_sections.append(f"- Updated {len(file_categories['docs'])} documentation files")
        if file_categories['config']:
            body_sections.append(f"- Modified {len(file_categories['config'])} config files")

        # Stats
        body_sections.append(f"\n**Stats:** +{stats['insertions']} -{stats['deletions']} lines across {stats['files_changed']} files\n")

        # Files
        body_sections.append("## Files Modified\n")
        for file in files[:10]:  # Limit to first 10
            body_sections.append(f"- `{file}`")
        if len(files) > 10:
            body_sections.append(f"- ... and {len(files) - 10} more files")

        # Testing note
        body_sections.append("\n## Testing\n")
        if file_categories['tests']:
            body_sections.append("- Tests updated alongside changes")
        else:
            body_sections.append("- [ ] Manual testing required")

        # Notes
        body_sections.append("\n## Notes\n")
        body_sections.append(f"- Branch: `{current_branch}` → `{base_branch}`")
        body_sections.append(f"- Generated by Marcus PR Autopilot (heuristic mode)")

        body_md = '\n'.join(body_sections)

        # Summary
        summary = f"Changes to {len(files)} files ({stats['insertions']} insertions, {stats['deletions']} deletions)"

        return {
            'title': title,
            'body_md': body_md,
            'summary': summary,
            'confidence': confidence,
            'method': 'heuristic'
        }

    @staticmethod
    def _categorize_files(files: List[str]) -> Dict[str, List[str]]:
        """Categorize files by type."""
        categories = {
            'tests': [],
            'docs': [],
            'config': [],
            'primary': []
        }

        for file in files:
            file_lower = file.lower()
            if any(x in file_lower for x in ['test_', '_test.', 'tests/', '/test/']):
                categories['tests'].append(file)
            elif any(file_lower.endswith(x) for x in ['.md', '.txt', '.rst']):
                categories['docs'].append(file)
            elif any(x in file_lower for x in ['config', '.json', '.yaml', '.yml', '.toml', '.env']):
                categories['config'].append(file)
            else:
                categories['primary'].append(file)

        return categories

    @staticmethod
    def _generate_title_heuristic(files: List[str], categories: Dict, branch_name: str) -> str:
        """Generate PR title from file patterns and branch name."""
        # Extract action from branch name if possible
        action = None
        if '/' in branch_name:
            prefix = branch_name.split('/')[0].lower()
            if prefix in ['fix', 'feature', 'feat', 'bugfix', 'hotfix', 'refactor', 'docs', 'test', 'chore']:
                action = prefix.replace('feat', 'feature')

        # Find common directory
        if len(files) == 1:
            # Single file change
            file_name = Path(files[0]).name
            if action:
                return f"{action.capitalize()}: Update {file_name}"
            return f"Update {file_name}"

        # Multiple files - find common pattern
        common_dir = None
        if files:
            paths = [Path(f).parts for f in files]
            if all(len(p) > 1 for p in paths):
                # Check first directory component
                first_dirs = [p[0] for p in paths]
                if len(set(first_dirs)) == 1:
                    common_dir = first_dirs[0]

        # Build title
        if action:
            if common_dir:
                return f"{action.capitalize()}: Changes to {common_dir}"
            elif categories['tests']:
                return f"{action.capitalize()}: Update tests"
            elif categories['docs']:
                return f"{action.capitalize()}: Update documentation"
            else:
                return f"{action.capitalize()}: Update {len(files)} files"
        else:
            if common_dir:
                return f"Update {common_dir} files"
            return f"Update {len(files)} files"

    @staticmethod
    def _assess_confidence_heuristic(stats: Dict, files: List[str]) -> str:
        """Assess confidence level based on diff characteristics."""
        size = stats['diff_size_bytes']
        file_count = stats['files_changed']

        # High confidence: small, focused changes
        if size < 10 * 1024 and file_count <= 3:
            return 'high'

        # Medium confidence: moderate changes
        if size < 50 * 1024 and file_count <= 10:
            return 'medium'

        # Low confidence: large or scattered changes
        return 'low'

    @staticmethod
    def propose_pr_text(
        project_path: str,
        base_branch: str = 'main',
        current_branch: Optional[str] = None
    ) -> Dict:
        """
        Main entry point: analyze staged diff and propose PR text.

        Args:
            project_path: Path to git repository
            base_branch: Target branch (default: 'main')
            current_branch: Source branch (auto-detect if None)

        Returns:
            {
                'title': str,
                'body_md': str,
                'summary': str,
                'files_changed': List[str],
                'confidence': str,
                'method': str,  # 'heuristic' | 'llm'
                'diff_hash': str,
                'timestamp': str
            }

        Raises:
            PRAutopilotError: If operation fails
        """
        # Get current branch if not provided
        if not current_branch:
            branch_result = subprocess.run(
                ['git', 'branch', '--show-current'],
                cwd=project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            current_branch = branch_result.stdout.strip() or 'HEAD'

        # Get staged diff
        diff_data = PRAutopilotService.get_staged_diff(project_path)

        # Check if any files staged
        if not diff_data['files']:
            raise PRAutopilotError("No staged changes found. Stage your changes first.")

        # Try LLM if available, fall back to heuristic
        try:
            # TODO: Optional Ollama integration (future enhancement)
            # For v0.43, use heuristic only
            raise Exception("LLM not implemented yet")
        except Exception:
            # Heuristic fallback (always works)
            result = PRAutopilotService.propose_pr_text_heuristic(
                diff_data, base_branch, current_branch
            )

        # Add metadata
        result['files_changed'] = diff_data['files']
        result['diff_hash'] = diff_data['diff_hash']
        result['timestamp'] = datetime.utcnow().isoformat()

        return result
