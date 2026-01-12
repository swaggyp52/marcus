"""
Git service for local-first development workflow.

Supports:
- Branch creation/switching
- Status checking
- Diff generation
- Staging/committing
- Offline-only (no network operations)
"""

import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime


class GitOperationError(Exception):
    """Git operation failed."""
    pass


class LocalGitClient:
    """
    Local Git client using subprocess + git CLI.
    
    All operations are offline and work within project directory.
    """
    
    def __init__(self, project_root: Path):
        """Initialize client for a project directory."""
        self.project_root = Path(project_root)
        self._validate_path()
    
    def _validate_path(self):
        """Prevent directory traversal attacks."""
        try:
            self.project_root.resolve()
        except Exception as e:
            raise GitOperationError(f"Invalid path: {e}")
    
    def _run_git(self, *args, check=True) -> str:
        """Run a git command in the project directory."""
        try:
            result = subprocess.run(
                ['git', *args],
                cwd=str(self.project_root),
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip()
        except FileNotFoundError:
            raise GitOperationError("Git not found. Install git CLI.")
        except subprocess.CalledProcessError as e:
            raise GitOperationError(f"Git command failed: {e.stderr}")
    
    def is_repository(self) -> bool:
        """Check if project is a git repository."""
        try:
            self._run_git('rev-parse', '--git-dir')
            return True
        except GitOperationError:
            return False
    
    def initialize(self) -> None:
        """Initialize a new git repository."""
        if self.is_repository():
            raise GitOperationError("Already a git repository")
        
        self._run_git('init')
        self._run_git('config', 'user.email', 'marcus@localhost')
        self._run_git('config', 'user.name', 'Marcus Dev')
    
    def get_status(self) -> Dict:
        """Get repository status."""
        if not self.is_repository():
            return {
                'is_repo': False,
                'current_branch': None,
                'changed_files': [],
                'staged_files': [],
                'untracked_files': [],
                'is_dirty': False
            }
        
        try:
            # Current branch
            try:
                branch = self._run_git('rev-parse', '--abbrev-ref', 'HEAD')
            except GitOperationError:
                branch = '(detached)'
            
            # Status porcelain format: first two chars indicate status
            status_output = self._run_git('status', '--porcelain')
            
            changed = []
            staged = []
            untracked = []
            
            for line in status_output.split('\n'):
                if not line.strip():
                    continue
                
                status_codes = line[:2]
                filepath = line[3:]
                
                if status_codes == '??':
                    untracked.append(filepath)
                elif status_codes[0] in ['M', 'A', 'D', 'R']:
                    staged.append(filepath)
                elif status_codes[1] in ['M', 'D']:
                    changed.append(filepath)
            
            return {
                'is_repo': True,
                'current_branch': branch,
                'changed_files': changed,
                'staged_files': staged,
                'untracked_files': untracked,
                'is_dirty': len(changed) > 0 or len(untracked) > 0
            }
        except GitOperationError as e:
            raise GitOperationError(f"Failed to get status: {e}")
    
    def get_diff(self, staged_only: bool = False) -> str:
        """Get unified diff of changes."""
        try:
            if staged_only:
                return self._run_git('diff', '--staged')
            else:
                return self._run_git('diff', 'HEAD')
        except GitOperationError:
            # If no commits yet, show all staged/unstaged
            try:
                return self._run_git('diff')
            except GitOperationError:
                return ""
    
    def get_diff_summary(self) -> str:
        """Get short summary of changes."""
        try:
            return self._run_git('diff', '--stat', 'HEAD')
        except GitOperationError:
            try:
                return self._run_git('diff', '--stat')
            except GitOperationError:
                return ""
    
    def create_branch(self, branch_name: str, from_branch: Optional[str] = None) -> str:
        """Create and switch to new branch."""
        if not self._is_valid_branch_name(branch_name):
            raise GitOperationError("Invalid branch name")
        
        try:
            if from_branch:
                self._run_git('checkout', '-b', branch_name, from_branch)
            else:
                self._run_git('checkout', '-b', branch_name)
            return branch_name
        except GitOperationError as e:
            raise GitOperationError(f"Failed to create branch: {e}")
    
    def switch_branch(self, branch_name: str) -> str:
        """Switch to an existing branch."""
        try:
            self._run_git('checkout', branch_name)
            return branch_name
        except GitOperationError as e:
            raise GitOperationError(f"Failed to switch branch: {e}")
    
    def list_branches(self) -> List[str]:
        """List all branches."""
        try:
            output = self._run_git('branch', '--list')
            branches = []
            for line in output.split('\n'):
                line = line.strip()
                if line:
                    # Remove leading * if current branch
                    branches.append(line.lstrip('* '))
            return branches
        except GitOperationError:
            return []
    
    def stage_files(self, files: List[str]) -> None:
        """Stage specific files."""
        if not files:
            return
        
        try:
            for filepath in files:
                # Validate path to prevent traversal
                full_path = (self.project_root / filepath).resolve()
                try:
                    full_path.relative_to(self.project_root.resolve())
                except ValueError:
                    raise GitOperationError(f"Path outside project: {filepath}")
                
                self._run_git('add', filepath)
        except GitOperationError as e:
            raise GitOperationError(f"Failed to stage files: {e}")
    
    def stage_all(self) -> None:
        """Stage all changes."""
        try:
            self._run_git('add', '-A')
        except GitOperationError as e:
            raise GitOperationError(f"Failed to stage all: {e}")
    
    def commit(self, message: str, author_name: Optional[str] = None,
               author_email: Optional[str] = None) -> str:
        """Commit staged changes."""
        if not message.strip():
            raise GitOperationError("Commit message required")
        
        try:
            cmd = ['commit', '-m', message]
            if author_name and author_email:
                author = f"{author_name} <{author_email}>"
                cmd.extend(['--author', author])
            
            self._run_git(*cmd)
            
            # Return commit hash
            return self._run_git('rev-parse', 'HEAD')
        except GitOperationError as e:
            raise GitOperationError(f"Failed to commit: {e}")
    
    def get_log(self, max_count: int = 10) -> List[Dict]:
        """Get commit history."""
        try:
            output = self._run_git('log', f'--max-count={max_count}', 
                                  '--format=%H|%an|%ae|%ai|%s')
            commits = []
            for line in output.split('\n'):
                if line.strip():
                    parts = line.split('|')
                    commits.append({
                        'hash': parts[0],
                        'author': parts[1],
                        'email': parts[2],
                        'date': parts[3],
                        'message': parts[4] if len(parts) > 4 else ''
                    })
            return commits
        except GitOperationError:
            return []
    
    def revert_file(self, filepath: str) -> None:
        """Revert a file to last commit."""
        try:
            # Validate path
            full_path = (self.project_root / filepath).resolve()
            try:
                full_path.relative_to(self.project_root.resolve())
            except ValueError:
                raise GitOperationError(f"Path outside project: {filepath}")
            
            self._run_git('checkout', 'HEAD', '--', filepath)
        except GitOperationError as e:
            raise GitOperationError(f"Failed to revert file: {e}")
    
    def reset_to_commit(self, commit_hash: str, hard: bool = False) -> None:
        """Reset to a specific commit."""
        try:
            if hard:
                self._run_git('reset', '--hard', commit_hash)
            else:
                self._run_git('reset', commit_hash)
        except GitOperationError as e:
            raise GitOperationError(f"Failed to reset: {e}")
    
    def get_remote_url(self, remote: str = 'origin') -> Optional[str]:
        """Get remote URL."""
        try:
            return self._run_git('config', '--get', f'remote.{remote}.url')
        except GitOperationError:
            return None
    
    def add_remote(self, name: str, url: str) -> None:
        """Add a remote."""
        try:
            self._run_git('remote', 'add', name, url)
        except GitOperationError as e:
            raise GitOperationError(f"Failed to add remote: {e}")
    
    def get_changed_files(self) -> List[str]:
        """Get list of changed files (unstaged)."""
        try:
            output = self._run_git('diff', '--name-only', 'HEAD')
            return [f for f in output.split('\n') if f.strip()]
        except GitOperationError:
            return []
    
    def get_staged_files(self) -> List[str]:
        """Get list of staged files."""
        try:
            output = self._run_git('diff', '--staged', '--name-only')
            return [f for f in output.split('\n') if f.strip()]
        except GitOperationError:
            return []
    
    @staticmethod
    def _is_valid_branch_name(name: str) -> bool:
        """Validate branch name."""
        # Basic validation: alphanumeric, -, _, /
        import re
        return bool(re.match(r'^[a-zA-Z0-9/_-]+$', name))
