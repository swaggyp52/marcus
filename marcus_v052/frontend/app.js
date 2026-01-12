/**
 * Marcus v052 - Main Application
 * Personal Knowledge Agent with offline AI capabilities
 */

const API_BASE = 'http://127.0.0.1:8000';
const API_ENDPOINTS = {
  health: `${API_BASE}/health`,
  chat: `${API_BASE}/api/chat`,
  upload: `${API_BASE}/api/upload`,
  graph: `${API_BASE}/api/graph`,
};

let state = {
  documents: [],
  messages: [],
  graph: { nodes: [], edges: [] },
  isOnline: false,
  settings: {
    port: 8000,
    model: 'mistral',
    autoSummarize: true,
    showReasoning: true,
  },
};

// ============================================================
// INITIALIZATION
// ============================================================

async function initializeApp() {
  console.log('Initializing Marcus...');
  
  // Check backend health
  await checkBackendHealth();
  
  // Load saved settings
  loadSettings();
  
  // Initialize event listeners
  setupEventListeners();
  
  // Load initial data
  await loadGraphData();
  
  // Set startup message
  addActivityLog('Marcus initialized and ready');
}

// ============================================================
// BACKEND HEALTH CHECK
// ============================================================

async function checkBackendHealth() {
  try {
    const response = await fetch(API_ENDPOINTS.health, { timeout: 3000 });
    if (response.ok) {
      setStatus('online');
      state.isOnline = true;
    } else {
      setStatus('offline');
    }
  } catch (error) {
    console.error('Health check failed:', error);
    setStatus('offline');
  }
}

function setStatus(status) {
  const dot = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  
  if (status === 'online') {
    dot.className = 'status-dot online';
    text.textContent = 'Online';
  } else if (status === 'offline') {
    dot.className = 'status-dot offline';
    text.textContent = 'Offline';
  } else {
    dot.className = 'status-dot';
    text.textContent = 'Initializing';
  }
}

// ============================================================
// GRAPH VISUALIZATION
// ============================================================

async function loadGraphData() {
  try {
    const response = await fetch(API_ENDPOINTS.graph);
    const data = await response.json();
    
    state.graph = data;
    updateGraphStats();
    renderGraph();
  } catch (error) {
    console.error('Failed to load graph:', error);
  }
}

function updateGraphStats() {
  document.getElementById('stat-documents').textContent = state.graph.nodes?.filter(n => n.type === 'document').length || 0;
  document.getElementById('stat-concepts').textContent = state.graph.nodes?.filter(n => n.type !== 'document').length || 0;
  document.getElementById('stat-connections').textContent = state.graph.edges?.length || 0;
}

function renderGraph() {
  const canvas = document.getElementById('graph-canvas');
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  const rect = canvas.getBoundingClientRect();
  canvas.width = rect.width;
  canvas.height = rect.height;
  
  // Clear canvas
  ctx.fillStyle = 'rgba(10, 14, 39, 0.5)';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  
  if (!state.graph.nodes || state.graph.nodes.length === 0) {
    ctx.fillStyle = 'rgba(123, 127, 155, 0.3)';
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Knowledge graph will appear here', canvas.width / 2, canvas.height / 2);
    return;
  }
  
  // Simple force-directed layout simulation
  const nodes = state.graph.nodes.map(n => ({
    ...n,
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: 0,
    vy: 0,
  }));
  
  // Draw edges
  ctx.strokeStyle = 'rgba(0, 230, 255, 0.2)';
  ctx.lineWidth = 1;
  state.graph.edges?.forEach(edge => {
    const from = nodes.find(n => n.id === edge.source);
    const to = nodes.find(n => n.id === edge.target);
    if (from && to) {
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    }
  });
  
  // Draw nodes
  nodes.forEach(node => {
    const color = node.type === 'document' ? '#7c00ff' : '#00e6ff';
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(node.x, node.y, 4, 0, Math.PI * 2);
    ctx.fill();
  });
}

// ============================================================
// FILE UPLOAD
// ============================================================

function setupDropZone() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const browseBtn = document.getElementById('btn-browse');
  
  browseBtn.addEventListener('click', () => fileInput.click());
  
  fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
  });
  
  // Drag and drop
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
  });
  
  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.add('dragging');
    });
  });
  
  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
      dropZone.classList.remove('dragging');
    });
  });
  
  dropZone.addEventListener('drop', (e) => {
    handleFiles(e.dataTransfer.files);
  });
}

function preventDefaults(e) {
  e.preventDefault();
  e.stopPropagation();
}

async function handleFiles(files) {
  const progressContainer = document.getElementById('upload-progress');
  progressContainer.style.display = 'flex';
  
  for (const file of files) {
    await uploadFile(file, progressContainer);
  }
}

async function uploadFile(file, progressContainer) {
  const formData = new FormData();
  formData.append('file', file);
  
  // Create progress item
  const progressTemplate = document.getElementById('progress-template');
  const progressItem = progressTemplate.cloneNode(true);
  progressItem.style.display = 'block';
  progressItem.querySelector('.progress-filename').textContent = file.name;
  progressItem.querySelector('.progress-status').textContent = 'Uploading...';
  progressContainer.appendChild(progressItem);
  
  try {
    const response = await fetch(API_ENDPOINTS.upload, {
      method: 'POST',
      body: formData,
    });
    
    if (response.ok) {
      const data = await response.json();
      progressItem.querySelector('.progress-status').textContent = 'Success!';
      progressItem.querySelector('.progress-fill').style.width = '100%';
      
      // Add document to list
      state.documents.push({
        name: file.name,
        size: file.size,
        uploadedAt: new Date(),
        excerpt: data.excerpt,
      });
      
      renderDocuments();
      await loadGraphData();
      addActivityLog(`Uploaded: ${file.name}`);
      
      setTimeout(() => {
        progressItem.remove();
        if (progressContainer.children.length === 0) {
          progressContainer.style.display = 'none';
        }
      }, 2000);
    }
  } catch (error) {
    progressItem.querySelector('.progress-status').textContent = 'Failed';
    progressItem.querySelector('.progress-status').style.color = 'var(--error)';
    showToast(`Failed to upload ${file.name}`, 'error');
  }
}

function renderDocuments() {
  const grid = document.getElementById('documents-grid');
  
  if (state.documents.length === 0) {
    grid.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">📚</div>
        <p>No documents yet. Upload your first document to build your knowledge graph.</p>
      </div>
    `;
    return;
  }
  
  grid.innerHTML = state.documents.map(doc => `
    <div class="document-card">
      <div class="document-icon">📄</div>
      <div class="document-name" title="${doc.name}">${doc.name}</div>
      <div class="document-meta">${formatFileSize(doc.size)}</div>
    </div>
  `).join('');
}

function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ============================================================
// CHAT INTERFACE
// ============================================================

function setupChat() {
  const form = document.getElementById('chat-form');
  const input = document.getElementById('chat-input');
  const hints = document.querySelectorAll('.hint');
  
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const message = input.value.trim();
    if (message) {
      await sendMessage(message);
      input.value = '';
      input.focus();
    }
  });
  
  hints.forEach(hint => {
    hint.addEventListener('click', (e) => {
      e.preventDefault();
      const hintText = e.target.dataset.hint;
      input.value = hintText;
      input.focus();
    });
  });
}

async function sendMessage(message) {
  // Add user message
  addMessage(message, 'user');
  
  try {
    const response = await fetch(API_ENDPOINTS.chat, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    
    const data = await response.json();
    
    if (data.response) {
      addMessage(data.response, 'assistant');
    }
    
    // Update graph if new concepts were added
    await loadGraphData();
  } catch (error) {
    addMessage('Sorry, I encountered an error processing your message.', 'assistant');
  }
}

function addMessage(text, role) {
  const messages = document.getElementById('chat-messages');
  const messageEl = document.createElement('div');
  messageEl.className = `message ${role}`;
  
  const content = document.createElement('div');
  content.className = 'message-content';
  
  if (role === 'assistant') {
    content.innerHTML = `<strong>Marcus:</strong> ${text}`;
  } else {
    content.textContent = text;
  }
  
  messageEl.appendChild(content);
  messages.appendChild(messageEl);
  messages.scrollTop = messages.scrollHeight;
  
  state.messages.push({ role, text, timestamp: new Date() });
}

// ============================================================
// ACTIVITY LOG
// ============================================================

function addActivityLog(text) {
  const log = document.getElementById('activity-log');
  const item = document.createElement('div');
  item.className = 'activity-item';
  
  const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  item.innerHTML = `
    <span class="activity-time">${time}</span>
    <span class="activity-text">${text}</span>
  `;
  
  log.insertBefore(item, log.firstChild);
  if (log.children.length > 10) {
    log.removeChild(log.lastChild);
  }
}

// ============================================================
// SETTINGS
// ============================================================

function setupSettings() {
  const settingsBtn = document.getElementById('btn-settings');
  const settingsModal = document.getElementById('settings-modal');
  const closeBtn = document.getElementById('btn-close-settings');
  const saveBtn = document.getElementById('btn-save-settings');
  const resetBtn = document.getElementById('btn-reset-settings');
  
  settingsBtn.addEventListener('click', () => {
    settingsModal.classList.add('active');
    loadSettingsIntoForm();
  });
  
  closeBtn.addEventListener('click', () => {
    settingsModal.classList.remove('active');
  });
  
  settingsModal.addEventListener('click', (e) => {
    if (e.target === settingsModal) {
      settingsModal.classList.remove('active');
    }
  });
  
  saveBtn.addEventListener('click', saveSettings);
  resetBtn.addEventListener('click', resetSettings);
}

function loadSettingsIntoForm() {
  document.getElementById('setting-port').value = state.settings.port;
  document.getElementById('setting-model').value = state.settings.model;
  document.getElementById('setting-auto-summarize').checked = state.settings.autoSummarize;
  document.getElementById('setting-show-reasoning').checked = state.settings.showReasoning;
}

function saveSettings() {
  state.settings.port = parseInt(document.getElementById('setting-port').value);
  state.settings.model = document.getElementById('setting-model').value;
  state.settings.autoSummarize = document.getElementById('setting-auto-summarize').checked;
  state.settings.showReasoning = document.getElementById('setting-show-reasoning').checked;
  
  localStorage.setItem('marcus-settings', JSON.stringify(state.settings));
  document.getElementById('settings-modal').classList.remove('active');
  showToast('Settings saved', 'success');
}

function resetSettings() {
  state.settings = {
    port: 8000,
    model: 'mistral',
    autoSummarize: true,
    showReasoning: true,
  };
  localStorage.removeItem('marcus-settings');
  loadSettingsIntoForm();
  showToast('Settings reset to defaults', 'success');
}

function loadSettings() {
  const saved = localStorage.getItem('marcus-settings');
  if (saved) {
    try {
      state.settings = JSON.parse(saved);
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  }
}

// ============================================================
// NOTIFICATIONS
// ============================================================

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  
  container.appendChild(toast);
  
  setTimeout(() => {
    toast.style.animation = 'slideInRight 0.3s ease reverse';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// ============================================================
// EVENT LISTENERS
// ============================================================

function setupEventListeners() {
  setupDropZone();
  setupChat();
  setupSettings();
  
  document.getElementById('btn-refresh-graph').addEventListener('click', loadGraphData);
}

// ============================================================
// STARTUP
// ============================================================

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeApp);
} else {
  initializeApp();
}
