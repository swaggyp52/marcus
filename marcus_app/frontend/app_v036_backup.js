/**
 * Marcus App - Main Application Logic
 * Handles UI interactions, API calls, and state management
 */

const API_BASE = 'http://127.0.0.1:8000/api';

// State
const app = {
    currentUser: null,
    currentTab: 'home',
    classes: [],
    assignments: [],
    inboxItems: [],
    searchResults: [],
};

// ============================================================================
// TAB SWITCHING
// ============================================================================

function switchTab(tabName) {
    // Hide all tab contents
    document.querySelectorAll('.tab-content').forEach(el => {
        el.classList.remove('active');
    });

    // Show selected tab
    const tabEl = document.getElementById(tabName + 'Tab');
    if (tabEl) {
        tabEl.classList.add('active');
        app.currentTab = tabName;
    }

    // Update sidebar navigation
    document.querySelectorAll('.sidebar-nav-link').forEach(el => {
        el.classList.remove('active');
    });
    document.querySelector(`[onclick*="'${tabName}'"]`)?.classList.add('active');

    // Update page title
    const titles = {
        'home': '🏠 Home',
        'inbox': '📥 Inbox',
        'classes': '📖 My Classes',
        'assignments': '✓ Assignments',
        'quickAdd': '➕ Quick Add',
        'search': '🔍 Search',
        'missions': '🎯 Missions',
        'audit': '📋 Audit Log'
    };
    document.getElementById('pageTitle').textContent = titles[tabName] || 'Marcus';

    // Load tab-specific data
    onTabActive(tabName);
}

function onTabActive(tabName) {
    switch (tabName) {
        case 'inbox':
            loadInbox();
            break;
        case 'classes':
            loadClasses();
            break;
        case 'assignments':
            loadAssignments();
            break;
        case 'search':
            initSearch();
            break;
        case 'home':
            loadDashboard();
            break;
    }
}

// ============================================================================
// MODALS
// ============================================================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

document.addEventListener('DOMContentLoaded', () => {
    // Close modals on backdrop click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
});

// ============================================================================
// SYLLABI UPLOAD
// ============================================================================

function openSyllabiUpload() {
    openModal('syllabiModal');
}

function closeSyllabiModal() {
    closeModal('syllabiModal');
}

async function submitSyllabiUpload() {
    const fileInput = document.getElementById('syllabiFile');
    const files = fileInput.files;

    if (files.length === 0) {
        alert('Please select at least one PDF file');
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }

    try {
        showLoading('Processing syllabi...');
        const response = await fetch(`${API_BASE}/intake`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.status}`);
        }

        const data = await response.json();
        showSuccess(`Processed ${files.length} syllabi successfully!`);
        fileInput.value = '';
        closeSyllabiModal();
        
        // Refresh classes and assignments
        loadClasses();
        loadAssignments();
        loadDashboard();
    } catch (error) {
        console.error('Upload error:', error);
        showError(`Upload failed: ${error.message}`);
    }
}

// ============================================================================
// CLASSES
// ============================================================================

function openAddClassModal() {
    openModal('addClassModal');
}

function closeAddClassModal() {
    closeModal('addClassModal');
}

async function submitAddClass() {
    const name = document.getElementById('className').value;
    const instructor = document.getElementById('classInstructor').value;
    const term = document.getElementById('classTerm').value;

    if (!name || !term) {
        showError('Please fill in required fields');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/classes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, instructor, term }),
        });

        if (!response.ok) throw new Error('Failed to create class');

        showSuccess('Class created successfully!');
        closeAddClassModal();
        loadClasses();
        loadDashboard();
    } catch (error) {
        console.error('Add class error:', error);
        showError(`Failed to create class: ${error.message}`);
    }
}

async function loadClasses() {
    try {
        const response = await fetch(`${API_BASE}/classes`);
        if (!response.ok) throw new Error('Failed to load classes');

        app.classes = await response.json();
        renderClasses();
    } catch (error) {
        console.error('Load classes error:', error);
        showError('Failed to load classes');
    }
}

function renderClasses() {
    const container = document.getElementById('classesContainer');

    if (app.classes.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📚</div>
                <div class="empty-state-title">No classes yet</div>
                <div class="empty-state-text">Create or import your classes</div>
            </div>
        `;
        return;
    }

    container.innerHTML = app.classes.map(cls => `
        <div class="list-item">
            <div class="list-item-content">
                <div class="list-item-title">${cls.name || 'Untitled'}</div>
                <div class="list-item-subtitle">${cls.instructor || 'No instructor'} • ${cls.term || 'No term'}</div>
            </div>
            <div class="list-item-meta">
                <span class="badge badge-primary">${cls.assignments_count || 0} assignments</span>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// ASSIGNMENTS
// ============================================================================

function openAddAssignmentModal() {
    openModal('addAssignmentModal');
}

async function loadAssignments() {
    try {
        const response = await fetch(`${API_BASE}/assignments`);
        if (!response.ok) throw new Error('Failed to load assignments');

        app.assignments = await response.json();
        renderAssignments();
    } catch (error) {
        console.error('Load assignments error:', error);
        showError('Failed to load assignments');
    }
}

function renderAssignments() {
    const container = document.getElementById('assignmentsContainer');

    if (app.assignments.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✓</div>
                <div class="empty-state-title">No assignments yet</div>
                <div class="empty-state-text">Create or import assignments from your syllabus</div>
            </div>
        `;
        return;
    }

    container.innerHTML = app.assignments.map(assign => {
        const dueDate = new Date(assign.due_date);
        const today = new Date();
        const status = dueDate < today ? 'danger' : 'warning';
        
        return `
            <div class="list-item">
                <div class="list-item-content">
                    <div class="list-item-title">${assign.title || 'Untitled'}</div>
                    <div class="list-item-subtitle">${assign.class_name || 'No class'} • Due ${dueDate.toLocaleDateString()}</div>
                </div>
                <div class="list-item-meta">
                    <span class="badge badge-${status}">Due ${dueDate.toLocaleDateString()}</span>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================================================
// INBOX
// ============================================================================

async function loadInbox() {
    try {
        const response = await fetch(`${API_BASE}/inbox`);
        if (!response.ok) throw new Error('Failed to load inbox');

        app.inboxItems = await response.json();
        renderInbox();
    } catch (error) {
        console.error('Load inbox error:', error);
        showError('Failed to load inbox');
    }
}

function renderInbox() {
    const container = document.getElementById('inboxContainer');

    if (app.inboxItems.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">📭</div>
                <div class="empty-state-title">Inbox empty</div>
                <div class="empty-state-text">Your inbox items will appear here</div>
            </div>
        `;
        return;
    }

    container.innerHTML = app.inboxItems.map(item => `
        <div class="list-item">
            <div class="list-item-content">
                <div class="list-item-title">${item.title || 'Untitled'}</div>
                <div class="list-item-subtitle">${item.description || 'No description'}</div>
            </div>
            <div class="list-item-meta">
                <span class="badge badge-primary">${item.type || 'item'}</span>
            </div>
        </div>
    `).join('');
}

function refreshInbox() {
    loadInbox();
}

// ============================================================================
// QUICK ADD
// ============================================================================

async function submitQuickAdd() {
    const title = document.getElementById('quickAddTitle').value;
    const description = document.getElementById('quickAddDesc').value;
    const type = document.getElementById('quickAddType').value;
    const dueDate = document.getElementById('quickAddDue').value;

    if (!title) {
        showError('Please enter a title');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/inbox`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title, description, type, due_date: dueDate }),
        });

        if (!response.ok) throw new Error('Failed to add item');

        showSuccess('Item added successfully!');
        document.getElementById('quickAddTitle').value = '';
        document.getElementById('quickAddDesc').value = '';
        document.getElementById('quickAddDue').value = '';
        
        loadInbox();
        loadDashboard();
    } catch (error) {
        console.error('Quick add error:', error);
        showError(`Failed to add item: ${error.message}`);
    }
}

function openQuickAddModal() {
    switchTab('quickAdd');
}

// ============================================================================
// DASHBOARD
// ============================================================================

async function loadDashboard() {
    try {
        // Load stats
        const classesRes = await fetch(`${API_BASE}/classes`);
        const assignmentsRes = await fetch(`${API_BASE}/assignments`);
        const inboxRes = await fetch(`${API_BASE}/inbox`);

        if (classesRes.ok) {
            app.classes = await classesRes.json();
            document.getElementById('statClasses').textContent = app.classes.length;
        }

        if (assignmentsRes.ok) {
            app.assignments = await assignmentsRes.json();
            document.getElementById('statAssignments').textContent = app.assignments.length;
            
            // Calculate due this week
            const today = new Date();
            const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
            const dueThisWeek = app.assignments.filter(a => {
                const due = new Date(a.due_date);
                return due >= today && due <= nextWeek;
            }).length;
            document.getElementById('statDueThisWeek').textContent = dueThisWeek;
            
            // Render recent
            renderRecentAssignments();
        }

        if (inboxRes.ok) {
            app.inboxItems = await inboxRes.json();
            document.getElementById('statInboxCount').textContent = app.inboxItems.length;
            const inboxBadge = document.getElementById('inboxBadge');
            if (app.inboxItems.length > 0) {
                inboxBadge.textContent = app.inboxItems.length;
                inboxBadge.style.display = 'inline-block';
            }
        }
    } catch (error) {
        console.error('Load dashboard error:', error);
    }
}

function renderRecentAssignments() {
    const container = document.getElementById('recentAssignmentsContainer');

    if (app.assignments.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✓</div>
                <div class="empty-state-title">No assignments yet</div>
                <div class="empty-state-text">Upload syllabi to get started</div>
            </div>
        `;
        return;
    }

    // Show latest 5
    const recent = app.assignments.slice(0, 5);
    container.innerHTML = recent.map(assign => {
        const dueDate = new Date(assign.due_date);
        return `
            <div class="list-item">
                <div class="list-item-content">
                    <div class="list-item-title">${assign.title || 'Untitled'}</div>
                    <div class="list-item-subtitle">${assign.class_name || 'No class'}</div>
                </div>
                <span class="badge badge-primary">Due ${dueDate.toLocaleDateString()}</span>
            </div>
        `;
    }).join('');
}

// ============================================================================
// SEARCH
// ============================================================================

function initSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', performSearch);
    }
}

function performSearch() {
    const query = document.getElementById('searchInput').value.toLowerCase();
    
    if (!query) {
        document.getElementById('searchResults').innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-title">Start typing to search</div>
            </div>
        `;
        return;
    }

    app.searchResults = [
        ...app.classes.filter(c => c.name.toLowerCase().includes(query)),
        ...app.assignments.filter(a => a.title.toLowerCase().includes(query)),
        ...app.inboxItems.filter(i => i.title.toLowerCase().includes(query))
    ];

    const container = document.getElementById('searchResults');
    if (app.searchResults.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">🔍</div>
                <div class="empty-state-title">No results found</div>
            </div>
        `;
        return;
    }

    container.innerHTML = app.searchResults.map(item => `
        <div class="list-item">
            <div class="list-item-content">
                <div class="list-item-title">${item.title || item.name || 'Untitled'}</div>
                <div class="list-item-subtitle">${item.class_name || 'Item'}</div>
            </div>
        </div>
    `).join('');
}

// ============================================================================
// NOTIFICATIONS
// ============================================================================

function showSuccess(message) {
    showAlert(message, 'success');
}

function showError(message) {
    showAlert(message, 'error');
}

function showLoading(message) {
    showAlert(message, 'info');
}

function showAlert(message, type = 'info') {
    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type}`;
    alert.innerHTML = `
        <span>${message}</span>
    `;
    
    // Insert at top of page
    const content = document.querySelector('.content');
    if (content) {
        content.insertAdjacentElement('afterbegin', alert);
        
        // Remove after 5 seconds
        setTimeout(() => alert.remove(), 5000);
    } else {
        console.log(`[${type}] ${message}`);
    }
}

// ============================================================================
// LOCK SESSION
// ============================================================================

async function lockSession() {
    try {
        const response = await fetch(`${API_BASE}/auth/lock`, {
            method: 'POST',
        });
        
        if (response.ok) {
            window.location.href = '/login.html';
        }
    } catch (error) {
        console.error('Lock error:', error);
        window.location.href = '/login.html';
    }
}

// ============================================================================
// INITIALIZATION
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
    console.log('Marcus app initialized');
    loadDashboard();
    initSearch();
});
