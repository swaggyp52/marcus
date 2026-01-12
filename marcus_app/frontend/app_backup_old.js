// Marcus Frontend JavaScript

const API_BASE = '/api';
let currentAssignment = null;
let onlineMode = false;

// v0.47a: MarcusApp global object for integration
window.MarcusApp = {
    showInbox: function() {
        switchTab('inbox');
    }
};

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    loadStatus();
    loadHomeDashboard(); // v0.47a: Load home dashboard stats
    loadClasses();
    loadAssignments();
});

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API call failed');
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showError(error.message);
        throw error;
    }
}

function showError(message) {
    // Create error toast
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.textContent = message;
    document.querySelector('.container').insertBefore(errorDiv, document.querySelector('.container').firstChild);
    setTimeout(() => errorDiv.remove(), 5000);
}

function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'success';
    successDiv.textContent = message;
    document.querySelector('.container').insertBefore(successDiv, document.querySelector('.container').firstChild);
    setTimeout(() => successDiv.remove(), 3000);
}

function formatDate(dateString) {
    if (!dateString) return 'No due date';
    const date = new Date(dateString);
    return date.toLocaleString();
}

// ============================================================================
// TAB SWITCHING
// ============================================================================

function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tabName}Tab`).classList.add('active');

    // Load data for the tab
    if (tabName === 'home') {
        // v0.47a: Home Dashboard
        loadHomeDashboard();
        // v0.47b: Agent Chat
        if (window.agentChat && !document.querySelector('.agent-chat')) {
            window.agentChat.init('agentChatContainer');
        }
    } else if (tabName === 'classes') {
        loadClasses();
    } else if (tabName === 'assignments') {
        loadAssignments();
    } else if (tabName === 'inbox') {
        // v0.47a: Inbox
        if (window.inboxUI) {
            window.inboxUI.init();
        }
    } else if (tabName === 'audit') {
        loadAuditLogs();
    } else if (tabName === 'missions') {
        // v0.45: Mission Control
        if (window.missionControlAPI) {
            window.missionControlAPI.initMissionControl();
        }
    } else if (tabName === 'lifeview') {
        // v0.45: Life View v2
        if (window.lifeViewAPI) {
            window.lifeViewAPI.initLifeView();
        }
    }
}

// ============================================================================
// MODAL FUNCTIONS
// ============================================================================

function showCreateClassModal() {
    document.getElementById('createClassModal').classList.add('active');
}

async function showCreateAssignmentModal() {
    // Load classes for dropdown
    const classes = await apiCall('/classes');
    const select = document.getElementById('assignmentClassId');
    select.innerHTML = classes.map(c =>
        `<option value="${c.id}">${c.code} - ${c.name}</option>`
    ).join('');

    document.getElementById('createAssignmentModal').classList.add('active');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.remove('active');
}

// ============================================================================
// STATUS AND ONLINE MODE
// ============================================================================

async function loadStatus() {
    try {
        const status = await apiCall('/status');

        document.getElementById('statusStats').textContent =
            `${status.total_classes} Classes | ${status.total_assignments} Assignments | ${status.total_artifacts} Files`;

        onlineMode = status.online_mode;
        const toggle = document.getElementById('onlineToggle');
        const badge = document.getElementById('onlineBadge');

        if (onlineMode) {
            toggle.classList.add('active');
            badge.textContent = 'ONLINE';
            badge.className = 'badge badge-online';
        } else {
            toggle.classList.remove('active');
            badge.textContent = 'OFFLINE';
            badge.className = 'badge badge-offline';
        }
    } catch (error) {
        console.error('Failed to load status:', error);
    }
}

async function toggleOnlineMode() {
    const newMode = !onlineMode;

    try {
        await apiCall('/online-mode', {
            method: 'POST',
            body: JSON.stringify({ enabled: newMode })
        });

        onlineMode = newMode;
        loadStatus();
        showSuccess(`Online mode ${newMode ? 'enabled' : 'disabled'}`);
    } catch (error) {
        showError('Failed to toggle online mode');
    }
}

// ============================================================================
// CLASSES
// ============================================================================

async function loadClasses() {
    const container = document.getElementById('classesList');
    container.innerHTML = '<div class="loading">Loading classes...</div>';

    try {
        const classes = await apiCall('/classes');

        if (classes.length === 0) {
            container.innerHTML = '<div class="empty-state">No classes yet. Create your first class!</div>';
            return;
        }

        container.innerHTML = classes.map(cls => `
            <div class="list-item">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${cls.code}</strong> - ${cls.name}
                        <div style="color: #888; font-size: 0.9em; margin-top: 5px;">
                            Created: ${formatDate(cls.created_at)}
                        </div>
                    </div>
                    <span class="badge badge-${cls.status}">${cls.status.toUpperCase()}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load classes</div>';
    }
}

async function createClass() {
    const code = document.getElementById('classCode').value.trim();
    const name = document.getElementById('className').value.trim();

    if (!code || !name) {
        showError('Please fill in all fields');
        return;
    }

    try {
        await apiCall('/classes', {
            method: 'POST',
            body: JSON.stringify({ code, name })
        });

        showSuccess('Class created successfully');
        closeModal('createClassModal');
        document.getElementById('classCode').value = '';
        document.getElementById('className').value = '';
        loadClasses();
        loadStatus();
    } catch (error) {
        // Error already shown by apiCall
    }
}

// ============================================================================
// ASSIGNMENTS
// ============================================================================

async function loadAssignments() {
    const container = document.getElementById('assignmentsList');
    container.innerHTML = '<div class="loading">Loading assignments...</div>';

    try {
        const assignments = await apiCall('/assignments');

        if (assignments.length === 0) {
            container.innerHTML = '<div class="empty-state">No assignments yet. Create your first assignment!</div>';
            return;
        }

        container.innerHTML = assignments.map(assignment => `
            <div class="list-item" onclick="viewAssignment(${assignment.id})">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>${assignment.title}</strong>
                        <div style="color: #888; font-size: 0.9em; margin-top: 5px;">
                            Due: ${formatDate(assignment.due_date)}
                        </div>
                    </div>
                    <span class="badge badge-${assignment.status}">${assignment.status.replace('_', ' ').toUpperCase()}</span>
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load assignments</div>';
    }
}

async function createAssignment() {
    const class_id = parseInt(document.getElementById('assignmentClassId').value);
    const title = document.getElementById('assignmentTitle').value.trim();
    const description = document.getElementById('assignmentDescription').value.trim();
    const due_date = document.getElementById('assignmentDueDate').value;

    if (!class_id || !title) {
        showError('Please fill in required fields');
        return;
    }

    const data = { class_id, title };
    if (description) data.description = description;
    if (due_date) data.due_date = new Date(due_date).toISOString();

    try {
        await apiCall('/assignments', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        showSuccess('Assignment created successfully');
        closeModal('createAssignmentModal');
        document.getElementById('assignmentTitle').value = '';
        document.getElementById('assignmentDescription').value = '';
        document.getElementById('assignmentDueDate').value = '';
        loadAssignments();
        loadStatus();
    } catch (error) {
        // Error already shown
    }
}

async function viewAssignment(assignmentId) {
    try {
        const assignment = await apiCall(`/assignments/${assignmentId}`);
        const artifacts = await apiCall(`/assignments/${assignmentId}/artifacts`);
        const plans = await apiCall(`/assignments/${assignmentId}/plans`);

        currentAssignment = assignment;

        let html = `
            <div class="modal-header">${assignment.title}</div>
            <div style="margin-bottom: 20px;">
                <p><strong>Status:</strong> <span class="badge badge-${assignment.status}">${assignment.status.replace('_', ' ').toUpperCase()}</span></p>
                <p><strong>Due:</strong> ${formatDate(assignment.due_date)}</p>
                ${assignment.description ? `<p><strong>Description:</strong> ${assignment.description}</p>` : ''}
            </div>

            <div class="card">
                <div class="card-header">Files</div>
                <input type="file" id="fileUpload" style="margin-bottom: 10px;">
                <button class="btn" onclick="uploadFile()">Upload File</button>
                <div id="artifactsList" style="margin-top: 15px;">
                    ${artifacts.length === 0 ? '<p>No files uploaded yet.</p>' :
                        artifacts.map(a => `
                            <div class="artifact-item">
                                <div>
                                    <strong>${a.original_filename}</strong>
                                    <span style="color: #888; margin-left: 10px;">${a.file_type}</span>
                                </div>
                                <button class="btn btn-secondary" onclick="extractText(${a.id})">Extract Text</button>
                            </div>
                        `).join('')
                    }
                </div>
            </div>

            <div class="card">
                <div class="card-header">Plans</div>
                <button class="btn" onclick="generatePlan()">Generate Plan</button>
                <div id="plansList" style="margin-top: 15px;">
                    ${plans.length === 0 ? '<p>No plans generated yet.</p>' :
                        plans.map(p => renderPlan(p)).join('')
                    }
                </div>
            </div>

            <div class="card">
                <div class="card-header">Extracted Text</div>
                <div id="extractedTextDisplay"></div>
            </div>
        `;

        document.getElementById('assignmentDetails').innerHTML = html;
        document.getElementById('viewAssignmentModal').classList.add('active');
    } catch (error) {
        showError('Failed to load assignment details');
    }
}

function renderPlan(plan) {
    const steps = JSON.parse(plan.steps || '[]');
    const materials = JSON.parse(plan.required_materials || '[]');
    const outputs = JSON.parse(plan.output_formats || '[]');

    return `
        <div style="background: #0a0a0a; padding: 15px; border-radius: 8px; margin-top: 10px; border: 1px solid #333;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h3 style="color: #667eea;">${plan.title}</h3>
                <span class="badge" style="background: ${plan.confidence === 'high' ? '#27ae60' : plan.confidence === 'medium' ? '#f39c12' : '#e74c3c'}">
                    ${plan.confidence ? plan.confidence.toUpperCase() : 'UNKNOWN'} CONFIDENCE
                </span>
            </div>

            <div class="plan-section">
                <h3>Steps</h3>
                ${steps.map(step => `
                    <div class="step-item">
                        <strong>${step.order}.</strong> ${step.description}
                        <span class="badge" style="background: #555; margin-left: 10px;">${step.effort}</span>
                    </div>
                `).join('')}
            </div>

            <div class="plan-section">
                <h3>Required Materials</h3>
                <ul style="margin-left: 20px;">
                    ${materials.map(m => `<li>${m}</li>`).join('')}
                </ul>
            </div>

            <div class="plan-section">
                <h3>Output Formats</h3>
                <ul style="margin-left: 20px;">
                    ${outputs.map(o => `<li>${o}</li>`).join('')}
                </ul>
            </div>

            ${plan.draft_outline ? `
                <div class="plan-section">
                    <h3>Draft Outline</h3>
                    <div class="extracted-text">${plan.draft_outline}</div>
                </div>
            ` : ''}

            ${plan.assumptions ? `
                <div class="plan-section">
                    <h3>Assumptions</h3>
                    <p>${plan.assumptions}</p>
                </div>
            ` : ''}

            ${plan.risks_unknowns && plan.risks_unknowns !== 'None identified at this time' ? `
                <div class="plan-section">
                    <h3>Risks & Unknowns</h3>
                    <p style="color: #f39c12;">${plan.risks_unknowns}</p>
                </div>
            ` : ''}

            <p style="color: #888; font-size: 0.9em; margin-top: 15px;">
                Generated: ${formatDate(plan.created_at)} | Effort: ${plan.effort_estimate}
            </p>
        </div>
    `;
}

async function uploadFile() {
    const fileInput = document.getElementById('fileUpload');
    const file = fileInput.files[0];

    if (!file) {
        showError('Please select a file');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE}/assignments/${currentAssignment.id}/artifacts`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        showSuccess('File uploaded successfully');
        fileInput.value = '';
        viewAssignment(currentAssignment.id); // Reload
    } catch (error) {
        showError('Failed to upload file');
    }
}

async function extractText(artifactId) {
    try {
        showSuccess('Extracting text...');
        const extracted = await apiCall(`/artifacts/${artifactId}/extract`, {
            method: 'POST'
        });

        if (extracted.extraction_status === 'success') {
            document.getElementById('extractedTextDisplay').innerHTML = `
                <div class="extracted-text">${extracted.content}</div>
                <p style="color: #888; margin-top: 10px;">
                    Extraction method: ${extracted.extraction_method} | Status: ${extracted.extraction_status}
                </p>
            `;
            showSuccess('Text extracted successfully');
        } else {
            showError(`Extraction ${extracted.extraction_status}: ${extracted.error_message || 'Unknown error'}`);
        }
    } catch (error) {
        showError('Failed to extract text');
    }
}

async function generatePlan() {
    if (!currentAssignment) return;

    try {
        showSuccess('Generating plan...');
        const plan = await apiCall('/plans', {
            method: 'POST',
            body: JSON.stringify({
                assignment_id: currentAssignment.id,
                use_online_mode: onlineMode
            })
        });

        showSuccess('Plan generated successfully');
        viewAssignment(currentAssignment.id); // Reload to show plan
    } catch (error) {
        // Error already shown
    }
}

// ============================================================================
// AUTHENTICATION
// ============================================================================

async function lockSession() {
    if (!confirm('Lock Marcus? You will need to log in again.')) {
        return;
    }

    try {
        await apiCall('/auth/lock', { method: 'POST' });
        window.location.href = '/login';
    } catch (error) {
        alert('Error locking session. Redirecting to login...');
        window.location.href = '/login';
    }
}

// ============================================================================
// AUDIT LOG
// ============================================================================

async function loadAuditLogs() {
    const container = document.getElementById('auditLogList');
    container.innerHTML = '<div class="loading">Loading audit logs...</div>';

    try {
        const logs = await apiCall('/audit-logs?limit=50');

        if (logs.length === 0) {
            container.innerHTML = '<div class="empty-state">No audit logs yet.</div>';
            return;
        }

        container.innerHTML = logs.map(log => `
            <div class="list-item">
                <div>
                    <div style="display: flex; justify-content: between; align-items: center; margin-bottom: 5px;">
                        <strong>${log.event_type}</strong>
                        <span class="badge badge-${log.online_mode}" style="margin-left: 10px;">
                            ${log.online_mode.toUpperCase()}
                        </span>
                    </div>
                    <p style="color: #aaa;">${log.user_action || 'N/A'}</p>
                    <p style="color: #666; font-size: 0.85em;">${formatDate(log.timestamp)}</p>
                </div>
            </div>
        `).join('');
    } catch (error) {
        container.innerHTML = '<div class="error">Failed to load audit logs</div>';
    }
}

// ============================================================================
// DEV MODE - INITIALIZATION & CORE FUNCTIONS
// ============================================================================

let devModeUI = null;
let currentProjectId = null;
let selectedFileForDiff = null;

async function initializeDevMode() {
    // For now, we'll initialize with a default project ID
    // In production, this would be selected from a project list
    const projectId = 1; // TODO: make this user-selectable
    currentProjectId = projectId;

    if (devModeUI) {
        devModeUI.projectId = projectId;
    } else {
        devModeUI = new DevModeUI(projectId);
    }

    // Show Dev Mode panel
    document.getElementById('devModePanel').classList.add('active');

    // Initialize git status
    await devModeUI.init();
    await refreshDevModeUI();

    showSuccess('Dev Mode initialized');
}

async function refreshDevModeUI() {
    if (!devModeUI) return;

    await refreshGitStatus();
    await refreshFileList();
    await refreshChangeSetList();
}

async function refreshGitStatus() {
    if (!devModeUI) return;

    try {
        const status = await devModeUI.refreshStatus();
        const gitStatusDiv = document.getElementById('gitStatus');

        const cleanStatus = status.is_clean ? '✓ Clean' : '✗ Dirty';
        const cleanColor = status.is_clean ? '#27ae60' : '#e74c3c';

        gitStatusDiv.innerHTML = `
            <div class="git-status-line">
                <strong>Branch:</strong>
                <span>${status.current_branch}</span>
            </div>
            <div class="git-status-line">
                <strong>Status:</strong>
                <span style="color: ${cleanColor};">${cleanStatus}</span>
            </div>
            <div class="git-status-line">
                <strong>Unstaged:</strong>
                <span>${status.unstaged_changes.length}</span>
            </div>
            <div class="git-status-line">
                <strong>Staged:</strong>
                <span>${status.staged_changes.length}</span>
            </div>
            <div class="git-status-line">
                <strong>Untracked:</strong>
                <span>${status.untracked_files.length}</span>
            </div>
        `;

        return status;
    } catch (error) {
        console.error('Failed to refresh git status:', error);
        document.getElementById('gitStatus').innerHTML = `
            <div class="error">Failed to load git status</div>
        `;
        return null;
    }
}

async function refreshFileList() {
    if (!devModeUI) return;

    try {
        const status = await devModeUI.refreshStatus();
        const fileListDiv = document.getElementById('fileList');

        if (status.unstaged_changes.length === 0 && status.staged_changes.length === 0 && status.untracked_files.length === 0) {
            fileListDiv.innerHTML = '<div class="no-content">No changes</div>';
            return;
        }

        let html = '';

        // Staged files
        if (status.staged_changes.length > 0) {
            html += '<div style="border-bottom: 1px solid #333; padding: 8px 0; color: #667eea; font-weight: 600;">Staged</div>';
            status.staged_changes.forEach(file => {
                html += `
                    <div class="file-item staged" onclick="selectFileForDiff('${file}', true)">
                        <div>
                            <span class="file-status staged">STAGED</span>
                            <span>${file}</span>
                        </div>
                        <button class="icon-btn" onclick="event.stopPropagation(); devModeUI.revertFile('${file}')">Revert</button>
                    </div>
                `;
            });
        }

        // Unstaged files
        if (status.unstaged_changes.length > 0) {
            html += '<div style="border-bottom: 1px solid #333; padding: 8px 0; margin-top: 8px; color: #f39c12; font-weight: 600;">Unstaged</div>';
            status.unstaged_changes.forEach(file => {
                html += `
                    <div class="file-item modified" onclick="selectFileForDiff('${file}', false)">
                        <div>
                            <span class="file-status modified">MODIFIED</span>
                            <span>${file}</span>
                        </div>
                        <button class="icon-btn" onclick="event.stopPropagation(); devModeUI.stageFiles(['${file}'])">Stage</button>
                    </div>
                `;
            });
        }

        // Untracked files
        if (status.untracked_files.length > 0) {
            html += '<div style="border-bottom: 1px solid #333; padding: 8px 0; margin-top: 8px; color: #27ae60; font-weight: 600;">Untracked</div>';
            status.untracked_files.forEach(file => {
                html += `
                    <div class="file-item new" onclick="selectFileForDiff('${file}', false)">
                        <div>
                            <span class="file-status new">NEW</span>
                            <span>${file}</span>
                        </div>
                        <button class="icon-btn" onclick="event.stopPropagation(); devModeUI.stageFiles(['${file}'])">Stage</button>
                    </div>
                `;
            });
        }

        fileListDiv.innerHTML = html;
    } catch (error) {
        console.error('Failed to refresh file list:', error);
        document.getElementById('fileList').innerHTML = '<div class="error">Failed to load file list</div>';
    }
}

async function selectFileForDiff(filename, stagedOnly) {
    selectedFileForDiff = filename;
    document.querySelectorAll('.file-item').forEach(item => item.classList.remove('selected'));
    event.target.closest('.file-item').classList.add('selected');

    // Load diff for this file
    await updateDiff();
}

async function updateDiff() {
    if (!devModeUI || !selectedFileForDiff) {
        document.getElementById('diffViewer').innerHTML = '<div class="no-content">Select a file to view diff</div>';
        return;
    }

    try {
        const stagedOnly = document.getElementById('diffStagedOnly')?.checked || false;
        const diff = await devModeUI.getDiff(stagedOnly);

        // Parse and display diff with syntax highlighting
        const diffLines = diff.split('\n');
        const diffHTML = diffLines.map(line => {
            let className = 'diff-line context';
            if (line.startsWith('+') && !line.startsWith('+++')) className = 'diff-line added';
            else if (line.startsWith('-') && !line.startsWith('---')) className = 'diff-line removed';
            else if (line.startsWith('@@') || line.startsWith('---') || line.startsWith('+++')) className = 'diff-line header';

            return `<div class="${className}">${escapeHtml(line)}</div>`;
        }).join('');

        document.getElementById('diffViewer').innerHTML = diffHTML || '<div class="no-content">No changes in diff</div>';
    } catch (error) {
        console.error('Failed to get diff:', error);
        document.getElementById('diffViewer').innerHTML = '<div class="error">Failed to load diff</div>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

async function copyDiffToClipboard() {
    const diffText = document.getElementById('diffViewer').innerText;
    try {
        await navigator.clipboard.writeText(diffText);
        showSuccess('Diff copied to clipboard');
    } catch (error) {
        showError('Failed to copy diff');
    }
}

// ============================================================================
// DEV MODE - CHANGESET MANAGEMENT
// ============================================================================

async function refreshChangeSetList() {
    if (!devModeUI) return;

    try {
        const changesets = await devModeUI.listChangeSets();
        const listDiv = document.getElementById('changesetList');

        if (!changesets || changesets.length === 0) {
            listDiv.innerHTML = '<div class="no-content">No changesets saved</div>';
            return;
        }

        const html = changesets.map((cs, idx) => `
            <div class="changeset-item">
                <div class="changeset-item-header">
                    <span class="changeset-item-name">${escapeHtml(cs.name || 'Unnamed')}</span>
                    <span class="changeset-item-timestamp">${formatDate(cs.created_at)}</span>
                </div>
                ${cs.notes ? `<div class="changeset-item-desc">${escapeHtml(cs.notes)}</div>` : ''}
                <div class="changeset-actions">
                    <button class="icon-btn" onclick="devModeUI.restoreChangeSet('${cs.id}')">↩️ Restore</button>
                    <button class="icon-btn" onclick="downloadChangeSetPatch('${cs.id}', '${escapeHtml(cs.name)}')">📥 Export</button>
                    <button class="icon-btn danger" onclick="devModeUI.deleteChangeSet('${cs.id}')">🗑️ Delete</button>
                </div>
            </div>
        `).join('');

        listDiv.innerHTML = html;
    } catch (error) {
        console.error('Failed to load changesets:', error);
        document.getElementById('changesetList').innerHTML = '<div class="error">Failed to load changesets</div>';
    }
}

async function showCreateChangeSetModal() {
    const status = await devModeUI?.refreshStatus();
    if (!status || (status.staged_changes.length === 0 && status.unstaged_changes.length === 0)) {
        showError('No changes to save in a ChangeSet');
        return;
    }

    document.getElementById('changesetName').value = `changeset-${new Date().toISOString().slice(0, 10)}`;
    document.getElementById('changesetNotes').value = '';
    document.getElementById('createChangeSetModal').classList.add('active');
}

async function showSelectChangeSetModal() {
    const changesets = await devModeUI?.listChangeSets();
    if (!changesets || changesets.length === 0) {
        showError('No changesets available to restore');
        return;
    }

    const html = changesets.map(cs => `
        <div class="list-item" onclick="selectChangeSetForRestore('${cs.id}')">
            <strong>${escapeHtml(cs.name)}</strong>
            <div style="color: #888; font-size: 0.9em; margin-top: 5px;">
                ${formatDate(cs.created_at)} - ${cs.notes ? cs.notes : 'No description'}
            </div>
        </div>
    `).join('');

    document.getElementById('selectChangeSetList').innerHTML = html;
    document.getElementById('selectChangeSetModal').classList.add('active');
}

let selectedChangeSetId = null;

function selectChangeSetForRestore(changesetId) {
    selectedChangeSetId = changesetId;
    document.querySelectorAll('#selectChangeSetList .list-item').forEach(item => item.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
}

async function downloadChangeSetPatch(changesetId, changesetName) {
    try {
        const patchContent = await devModeUI?.exportChangeSetsAsPatch([changesetId]);
        
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(patchContent));
        element.setAttribute('download', `${changesetName}.patch`);
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);

        showSuccess('Patch downloaded');
    } catch (error) {
        showError('Failed to export patch');
    }
}

// ============================================================================
// DEV MODE - COMMIT & PUSH
// ============================================================================

async function performCommit() {
    const message = document.getElementById('commitMessage').value.trim();
    const author = document.getElementById('commitAuthor').value.trim();
    const email = document.getElementById('commitEmail').value.trim();

    if (!message) {
        showError('Commit message required');
        return;
    }

    if (!author || !email) {
        showError('Author name and email required');
        return;
    }

    try {
        await devModeUI?.commit(message, author, email);
        showSuccess('Changes committed');

        // Clear form and refresh
        document.getElementById('commitMessage').value = '';
        document.getElementById('commitAuthor').value = author; // Keep author for next commit
        await refreshDevModeUI();
    } catch (error) {
        showError('Failed to commit: ' + error.message);
    }
}

// ============================================================================
// DEV MODE - ONLINE MODE & PUSH/PR
// ============================================================================

async function showPushConfirmModal() {
    try {
        const status = await devModeUI?.refreshStatus();
        if (!status) {
            showError('Failed to load repository status');
            return;
        }

        document.getElementById('pushRepoName').textContent = currentProjectId;
        document.getElementById('pushRemoteName').textContent = status.remote || 'origin';
        document.getElementById('pushBranchName').textContent = status.current_branch;
        document.getElementById('pushCommitCount').textContent = status.ahead_commits || 0;
        document.getElementById('pushFileCount').textContent = status.staged_changes.length + status.unstaged_changes.length;

        document.getElementById('pushConfirmModal').classList.add('active');
    } catch (error) {
        showError('Failed to load push details');
    }
}

async function showPRConfirmModal() {
    try {
        const status = await devModeUI?.refreshStatus();
        if (!status) {
            showError('Failed to load repository status');
            return;
        }

        document.getElementById('prRepoName').textContent = currentProjectId;
        document.getElementById('prSourceBranch').textContent = status.current_branch;
        document.getElementById('prBaseBranch').textContent = 'main'; // TODO: detect from remote
        document.getElementById('prFileCount').textContent = status.staged_changes.length;
        document.getElementById('prCommitCount').textContent = status.ahead_commits || 0;
        document.getElementById('prTitle').value = '';
        document.getElementById('prDescription').value = '';

        document.getElementById('prConfirmModal').classList.add('active');
    } catch (error) {
        showError('Failed to load PR details');
    }
}

async function performPush() {
    try {
        await devModeUI?.pushBranch();
        showSuccess('Changes pushed to remote successfully');
        closeModal('pushConfirmModal');
        await refreshDevModeUI();
    } catch (error) {
        showError('Push failed: ' + error.message);
    }
}

async function performCreatePR() {
    const title = document.getElementById('prTitle').value.trim();
    const description = document.getElementById('prDescription').value.trim();

    if (!title) {
        showError('PR title required');
        return;
    }

    try {
        await devModeUI?.createPR(title, description);
        showSuccess('Pull request created successfully');
        closeModal('prConfirmModal');
    } catch (error) {
        showError('Failed to create PR: ' + error.message);
    }
}

// ============================================================================
// DEV MODE - PR AUTOPILOT (v0.43)
// ============================================================================

async function suggestPRText() {
    if (!currentProjectId) {
        showError('No project selected');
        return;
    }

    const button = document.getElementById('suggestPRBtn');
    const statusSpan = document.getElementById('prSuggestionStatus');

    // Disable button and show loading state
    button.disabled = true;
    statusSpan.textContent = 'Analyzing staged diff...';
    statusSpan.style.color = '#667eea';

    try {
        const baseBranch = document.getElementById('prBaseBranch')?.textContent || 'main';

        const result = await apiCall(`/projects/${currentProjectId}/pr-autopilot`, {
            method: 'POST',
            body: JSON.stringify({ base_branch: baseBranch })
        });

        // Populate PR title and description fields
        document.getElementById('prTitle').value = result.title;
        document.getElementById('prDescription').value = result.body_md;

        // Show success with confidence and method
        const confidenceBadge = result.confidence.toUpperCase();
        const methodInfo = result.method === 'heuristic' ? '(offline heuristic)' : '(LLM)';
        statusSpan.textContent = `✓ Suggested (${confidenceBadge} confidence ${methodInfo})`;
        statusSpan.style.color = result.confidence === 'high' ? '#27ae60' :
                                 result.confidence === 'medium' ? '#f39c12' : '#888';

        showSuccess('PR text suggested - edit before creating');
    } catch (error) {
        statusSpan.textContent = '✗ Failed to generate suggestion';
        statusSpan.style.color = '#e74c3c';

        // Check for 200KB limit error
        if (error.message.includes('200') || error.message.includes('too large')) {
            showError('Diff exceeds 200KB limit. Split into smaller commits.');
        } else {
            showError('Failed to suggest PR text: ' + error.message);
        }
    } finally {
        // Re-enable button
        button.disabled = false;
    }
}

// ============================================================================
// DEV MODE - LIFE VIEW (EXPERIMENTAL)
// ============================================================================

async function loadLifeView() {
    const lifeViewSection = document.getElementById('lifeViewSection');
    
    // Check feature flag (for now, disabled by default)
    const featureFlag = true; // TODO: load from backend config

    if (!featureFlag) {
        lifeViewSection.style.display = 'none';
        return;
    }

    lifeViewSection.style.display = 'block';

    if (!devModeUI) {
        console.warn('DevModeUI not initialized for Life View');
        return;
    }

    try {
        const graphData = await devModeUI.getLifeGraph();
        
        if (window.lifeView) {
            window.lifeView.loadGraphData(graphData);
        }
    } catch (error) {
        console.error('Failed to load life view data:', error);
        // Life View is experimental, don't break main UI
    }
}

// ============================================================================
// V0.47a: HOME DASHBOARD
// ============================================================================

async function loadHomeDashboard() {
    try {
        const stats = await apiCall('/inbox/stats');

        document.getElementById('homeInboxCount').textContent = stats.inbox_count;
        document.getElementById('homeDueSoonCount').textContent = stats.due_soon_count;
        document.getElementById('homeOverdueCount').textContent = stats.overdue_count;

        // Update inbox tab badge
        const tabBadge = document.getElementById('inboxTabBadge');
        if (tabBadge && stats.inbox_count > 0) {
            tabBadge.textContent = stats.inbox_count;
            tabBadge.style.display = 'inline';
        } else if (tabBadge) {
            tabBadge.style.display = 'none';
        }

    } catch (error) {
        console.error('Failed to load home dashboard stats:', error);
        document.getElementById('homeInboxCount').textContent = '?';
        document.getElementById('homeDueSoonCount').textContent = '?';
        document.getElementById('homeOverdueCount').textContent = '?';
    }
}
