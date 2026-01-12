/**
 * Marcus v0.51 - Chat-First Application
 * Real backend integration, file upload, action cards
 */

const API_BASE = '/api';

// State
const app = {
    chatHistory: [],
    uploadedFile: null,
    selectedTabId: null,
};

// ============================================================================
// CHAT FUNCTIONS
// ============================================================================

async function handleSendMessage(event) {
    event.preventDefault();

    const input = document.getElementById('chatInput');
    const message = input.value.trim();

    if (!message) return;

    // Add user message to history
    appendMessage('user', message);
    input.value = '';
    document.getElementById('sendBtn').disabled = true;

    try {
        // Send to backend
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                attachmentId: app.uploadedFile?.id || null,
            })
        });

        if (!response.ok) throw new Error(`API error: ${response.status}`);

        const data = await response.json();

        // Add assistant response
        appendMessage('assistant', data.reply);

        // Add action cards if present
        if (data.actions && data.actions.length > 0) {
            addActionCards(data.actions);
        }

        // Update context panel
        if (data.created) {
            updateContextPanel(data.created);
        }

        // Update stats
        updateStats();

        // Clear uploaded file after message is sent
        app.uploadedFile = null;
        document.getElementById('uploadedFileDisplay').innerHTML = '';
    } catch (error) {
        appendMessage('assistant', `❌ Error: ${error.message}`);
        console.error(error);
    }

    document.getElementById('sendBtn').disabled = false;
    document.getElementById('chatInput').focus();
}

function appendMessage(role, content) {
    const chatHistory = document.getElementById('chatHistory');
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;
    messageEl.innerHTML = `
        <div>
            <div class="message-bubble">${escapeHtml(content)}</div>
            <div class="message-meta">${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
        </div>
    `;
    chatHistory.appendChild(messageEl);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    app.chatHistory.push({ role, content, timestamp: new Date() });
}

function addActionCards(actions) {
    const chatHistory = document.getElementById('chatHistory');
    const container = document.createElement('div');
    container.style.display = 'flex';
    container.style.flexDirection = 'column';
    container.style.gap = 'var(--space-sm)';

    actions.forEach(action => {
        const card = document.createElement('div');
        card.className = 'action-card';
        card.innerHTML = `<div class="action-card-title">→ ${escapeHtml(action.label)}</div>`;
        card.onclick = () => handleAction(action);
        container.appendChild(card);
    });

    chatHistory.appendChild(container);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

function handleAction(action) {
    switch (action.type) {
        case 'open_class':
            console.log(`Opening class ${action.id}`);
            // TODO: Switch to classes tab and highlight
            break;
        case 'view_inbox':
            switchTab('inbox');
            break;
        case 'open_mission':
            console.log(`Opening mission ${action.id}`);
            break;
        case 'open_item':
            console.log(`Opening item ${action.id}`);
            break;
        default:
            console.log(`Unknown action: ${action.type}`);
    }
}

// ============================================================================
// FILE UPLOAD
// ============================================================================

async function handleFileSelect(event) {
    const file = event.target.files[0];
    if (!file) return;

    // Show loading state
    const display = document.getElementById('uploadedFileDisplay');
    display.innerHTML = `<div style="color: var(--text-tertiary); font-size: var(--font-size-xs);">Uploading ${file.name}...</div>`;

    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/chat/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error(`Upload failed: ${response.status}`);

        const data = await response.json();
        app.uploadedFile = { id: data.artifactId, name: file.name };

        // Show uploaded file with remove option
        display.innerHTML = `
            <div class="uploaded-file">
                <span class="uploaded-file-name">📄 ${escapeHtml(file.name)}</span>
                <button type="button" class="uploaded-file-remove" onclick="removeUploadedFile()">✕</button>
            </div>
        `;

        // Add message that file was uploaded
        appendMessage('assistant', `Uploaded: **${escapeHtml(file.name)}**. Now tell me what to do with it (e.g., "set this up" to create classes from the syllabus).`);
    } catch (error) {
        display.innerHTML = `<div style="color: var(--color-danger); font-size: var(--font-size-xs);">Upload failed: ${error.message}</div>`;
    }

    // Reset file input
    document.getElementById('fileInput').value = '';
}

function removeUploadedFile() {
    app.uploadedFile = null;
    document.getElementById('uploadedFileDisplay').innerHTML = '';
}

// ============================================================================
// TAB SWITCHING
// ============================================================================

function switchTab(tabName) {
    // Update sidebar nav
    document.querySelectorAll('.sidebar-nav-link').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelector(`[onclick*="'${tabName}'"]`)?.classList.add('active');

    // Log action
    updateStatusBar(`Opened: ${tabName}`);
}

// ============================================================================
// CONTEXT PANEL & STATS
// ============================================================================

async function updateStats() {
    try {
        const [classesResp, tasksResp, inboxResp] = await Promise.all([
            fetch(`${API_BASE}/classes`),
            fetch(`${API_BASE}/assignments`),
            fetch(`${API_BASE}/inbox`),
        ]);

        const classes = classesResp.ok ? await classesResp.json() : [];
        const tasks = tasksResp.ok ? await tasksResp.json() : [];
        const inbox = inboxResp.ok ? await inboxResp.json() : [];

        document.getElementById('statClasses').textContent = classes.length;
        document.getElementById('statTasks').textContent = tasks.length;
        document.getElementById('statInbox').textContent = inbox.length;
    } catch (error) {
        console.error('Failed to update stats:', error);
    }
}

function updateContextPanel(created) {
    const recent = document.getElementById('contextRecent');

    // Update recent items
    const items = created.map(item => `
        <div class="context-item" onclick="switchTab('${item.type}')">
            <div class="context-item-name">${escapeHtml(item.label)}</div>
            <div class="context-item-meta">${item.type}</div>
        </div>
    `).join('');

    recent.innerHTML = items || '<div style="color: var(--text-tertiary); font-size: var(--font-size-xs);">None yet</div>';
}

function updateStatusBar(message) {
    document.getElementById('statusLastAction').textContent = `Last: ${message}`;
}

// ============================================================================
// UTILITIES
// ============================================================================

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    updateStats();
    document.getElementById('chatInput').focus();
});
