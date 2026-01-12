/**
 * V0.41: Dev Mode Frontend Component
 * 
 * Handles:
 * - Git status/operations (offline)
 * - ChangeSet management
 * - Online Mode gating for push/PR
 * - All security: no token display, auth-required calls
 */

class DevModeUI {
    constructor(projectId) {
        this.projectId = projectId;
        this.currentBranch = null;
        this.statusData = null;
        this.onlineMode = false;
        this.diffCache = {};
    }

    /**
     * Main entry point - initialize Dev Mode for a project
     */
    async init() {
        try {
            // Load online mode status
            const modeStatus = await this.apiCall('/projects/dev-mode/online-status', { method: 'GET' });
            this.onlineMode = modeStatus.online_mode;

            // Load git status
            await this.refreshStatus();
            
            return true;
        } catch (error) {
            console.error('Dev Mode init failed:', error);
            return false;
        }
    }

    /**
     * Core API call wrapper - includes auth cookies
     */
    async apiCall(endpoint, options = {}) {
        try {
            const response = await fetch(`/api${endpoint}`, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                credentials: 'include', // Include auth cookies
                ...options
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`API Error: ${response.status} - ${error}`);
            }

            // Handle stream responses (patch download)
            if (response.headers.get('content-type')?.includes('application/octet-stream')) {
                return response;
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }

    /**
     * Refresh git status
     */
    async refreshStatus() {
        try {
            this.statusData = await this.apiCall(`/projects/${this.projectId}/git/status`);
            this.currentBranch = this.statusData.current_branch;
            return this.statusData;
        } catch (error) {
            throw new Error('Failed to refresh git status');
        }
    }

    /**
     * Get unified diff for a file or entire repo
     */
    async getDiff(stagedOnly = false) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/diff?staged_only=${stagedOnly}`
            );
            return response; // { summary, diff }
        } catch (error) {
            throw new Error('Failed to get diff');
        }
    }

    /**
     * Stage files
     */
    async stageFiles(files) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/stage`,
                {
                    method: 'POST',
                    body: JSON.stringify({ files })
                }
            );
            await this.refreshStatus();
            return response;
        } catch (error) {
            throw new Error('Failed to stage files');
        }
    }

    /**
     * Stage all changes
     */
    async stageAll() {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/stage-all`,
                { method: 'POST' }
            );
            await this.refreshStatus();
            return response;
        } catch (error) {
            throw new Error('Failed to stage all');
        }
    }

    /**
     * Commit changes
     */
    async commit(message, authorName, authorEmail) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/commit`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        message,
                        author_name: authorName,
                        author_email: authorEmail
                    })
                }
            );
            await this.refreshStatus();
            return response;
        } catch (error) {
            throw new Error('Failed to commit');
        }
    }

    /**
     * Revert a file to HEAD
     */
    async revertFile(filepath) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/revert-file?filepath=${encodeURIComponent(filepath)}`,
                { method: 'POST' }
            );
            await this.refreshStatus();
            return response;
        } catch (error) {
            throw new Error('Failed to revert file');
        }
    }

    /**
     * Create a branch
     */
    async createBranch(branchName, fromBranch = null) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/branch`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        branch_name: branchName,
                        from_branch: fromBranch
                    })
                }
            );
            await this.refreshStatus();
            return response;
        } catch (error) {
            throw new Error('Failed to create branch');
        }
    }

    /**
     * Switch branch
     */
    async switchBranch(branchName) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/checkout`,
                {
                    method: 'POST',
                    body: JSON.stringify({ branch_name: branchName })
                }
            );
            await this.refreshStatus();
            return response;
        } catch (error) {
            throw new Error('Failed to switch branch');
        }
    }

    /**
     * List branches
     */
    async listBranches() {
        try {
            return await this.apiCall(`/projects/${this.projectId}/git/branches`);
        } catch (error) {
            throw new Error('Failed to list branches');
        }
    }

    /**
     * Create a ChangeSet snapshot
     */
    async createChangeSet(branchName, title, description) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/changesets`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        branch_name: branchName,
                        title,
                        description
                    })
                }
            );
            return response;
        } catch (error) {
            throw new Error('Failed to create changeset');
        }
    }

    /**
     * List ChangeSets
     */
    async listChangeSets() {
        try {
            return await this.apiCall(`/projects/${this.projectId}/changesets`);
        } catch (error) {
            throw new Error('Failed to list changesets');
        }
    }

    /**
     * Export ChangeSet as .patch file
     * Returns a Response object for downloading
     */
    async exportChangeSetsAsPatch(changesetId) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/changesets/${changesetId}/export`,
                {
                    method: 'POST',
                    body: JSON.stringify({ format: 'patch' })
                }
            );
            return response; // This is already a Response from apiCall
        } catch (error) {
            throw new Error('Failed to export changeset');
        }
    }

    /**
     * Delete (archive) ChangeSet
     */
    async deleteChangeSet(changesetId) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/changesets/${changesetId}`,
                { method: 'DELETE' }
            );
            return response;
        } catch (error) {
            throw new Error('Failed to delete changeset');
        }
    }

    /**
     * Push branch to remote (GUARDED - requires Online Mode)
     */
    async pushBranch(branchName, force = false) {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/git/push`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        branch_name: branchName,
                        force
                    })
                }
            );
            return response;
        } catch (error) {
            throw new Error('Push failed');
        }
    }

    /**
     * Create GitHub PR (GUARDED - requires Online Mode)
     */
    async createPR(title, body, baseBranch = 'main') {
        try {
            const response = await this.apiCall(
                `/projects/${this.projectId}/github/create-pr`,
                {
                    method: 'POST',
                    body: JSON.stringify({
                        title,
                        body,
                        base_branch: baseBranch
                    })
                }
            );
            return response;
        } catch (error) {
            throw new Error('PR creation failed');
        }
    }

    /**
     * Enable Online Mode
     */
    async enableOnlineMode() {
        try {
            const response = await this.apiCall(
                '/projects/dev-mode/enable-online',
                { method: 'POST' }
            );
            this.onlineMode = true;
            return response;
        } catch (error) {
            throw new Error('Failed to enable Online Mode');
        }
    }

    /**
     * Disable Online Mode
     */
    async disableOnlineMode() {
        try {
            const response = await this.apiCall(
                '/projects/dev-mode/disable-online',
                { method: 'POST' }
            );
            this.onlineMode = false;
            return response;
        } catch (error) {
            throw new Error('Failed to disable Online Mode');
        }
    }

    /**
     * Get Life-Graph data (if enabled)
     */
    async getLifeGraph() {
        try {
            return await this.apiCall('/life-graph');
        } catch (error) {
            // Life-Graph might be disabled, return null gracefully
            return null;
        }
    }

    /**
     * Revert all unstaged files
     */
    async revertAllUnstaged() {
        try {
            const status = await this.refreshStatus();
            for (const file of status.unstaged_changes) {
                await this.revertFile(file);
            }
            await this.refreshStatus();
            return true;
        } catch (error) {
            throw new Error('Failed to revert files');
        }
    }

    /**
     * Update diff view (helper for UI)
     */
    async updateDiff() {
        // This is a UI refresh method called when diff options change
        // The actual diff fetching happens in getDiff()
        return true;
    }

    /**
     * Toggle online mode (wrapper for UI)
     */
    async toggleOnlineMode() {
        try {
            if (this.onlineMode) {
                await this.disableOnlineMode();
            } else {
                await this.enableOnlineMode();
            }
            return this.onlineMode;
        } catch (error) {
            throw new Error('Failed to toggle online mode');
        }
    }

    /**
     * Perform commit (app.js wrapper)
     */
    async performCommit() {
        // This is called from the UI - actual commit logic is in commit()
        return true;
    }

    /**
     * Perform push (app.js wrapper)
     */
    async performPush() {
        try {
            const status = await this.refreshStatus();
            await this.pushBranch(status.current_branch);
            return true;
        } catch (error) {
            throw new Error('Push failed: ' + error.message);
        }
    }

    /**
     * Perform PR creation (app.js wrapper)
     */
    async performCreatePR() {
        // This is a UI wrapper - actual PR creation is in createPR()
        return true;
    }

    /**
     * Restore selected changeset
     */
    async restoreSelectedChangeSet(changesetId) {
        try {
            await this.apiCall(
                `/projects/${this.projectId}/changesets/${changesetId}/restore`,
                { method: 'POST' }
            );
            await this.refreshStatus();
            return true;
        } catch (error) {
            throw new Error('Failed to restore changeset');
        }
    }

    /**
     * Restore a changeset by ID
     */
    async restoreChangeSet(changesetId) {
        try {
            await this.apiCall(
                `/projects/${this.projectId}/changesets/${changesetId}/restore`,
                { method: 'POST' }
            );
            await this.refreshStatus();
            return true;
        } catch (error) {
            throw new Error('Failed to restore changeset');
        }
    }

    /**
     * Alias for refreshStatus() - used by UI refresh button
     */
    async refreshGitStatus() {
        return await this.refreshStatus();
    }
}

// Export for use in HTML
window.DevModeUI = DevModeUI;
