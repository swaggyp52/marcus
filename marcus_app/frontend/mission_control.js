/**
 * Marcus v0.45 - Mission Control UI
 *
 * Manages mission lifecycle:
 * - Create missions from templates
 * - List/filter missions
 * - View mission summary
 * - Run boxes
 * - Display artifacts
 */

let allMissions = [];
let selectedMissionId = null;

// ============================================================================
// INITIALIZATION
// ============================================================================

async function initMissionControl() {
    console.log('[Mission Control] Initializing...');
    await loadMissions();
    await loadClassesForMissionModal();
}

// ============================================================================
// MISSION CRUD
// ============================================================================

async function loadMissions() {
    try {
        const response = await fetch('/api/missions');
        if (!response.ok) throw new Error('Failed to load missions');

        allMissions = await response.json();
        console.log(`[Mission Control] Loaded ${allMissions.length} missions`);
        renderMissionsList();
    } catch (error) {
        console.error('[Mission Control] Error loading missions:', error);
        showError('Failed to load missions');
    }
}

async function loadClassesForMissionModal() {
    try {
        const response = await fetch('/api/classes');
        if (!response.ok) return;

        const classes = await response.json();
        const select = document.getElementById('newMissionClassId');
        if (!select) return;

        classes.forEach(cls => {
            const option = document.createElement('option');
            option.value = cls.id;
            option.textContent = `${cls.code} - ${cls.name}`;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('[Mission Control] Error loading classes:', error);
    }
}

function showCreateMissionModal() {
    document.getElementById('createMissionModal').style.display = 'block';
}

async function createMission() {
    const name = document.getElementById('newMissionName').value.trim();
    const template = document.getElementById('newMissionTemplate').value;
    const classIdValue = document.getElementById('newMissionClassId').value;

    if (!name) {
        showError('Mission name is required');
        return;
    }

    try {
        const payload = {
            template_name: template,
            mission_name: name
        };

        if (classIdValue) {
            payload.class_id = parseInt(classIdValue);
        }

        const response = await fetch('/api/missions/create-from-template', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to create mission');
        }

        const mission = await response.json();
        console.log('[Mission Control] Created mission:', mission);

        closeModal('createMissionModal');
        document.getElementById('newMissionName').value = '';

        await loadMissions();
        selectMission(mission.id);

        showSuccess(`Mission "${name}" created successfully`);
    } catch (error) {
        console.error('[Mission Control] Error creating mission:', error);
        showError(error.message);
    }
}

// ============================================================================
// MISSION LIST RENDERING
// ============================================================================

function filterMissions() {
    const searchTerm = document.getElementById('missionSearch')?.value.toLowerCase() || '';
    const typeFilter = document.getElementById('missionTypeFilter')?.value || '';
    const stateFilter = document.getElementById('missionStateFilter')?.value || '';

    const filtered = allMissions.filter(mission => {
        const matchesSearch = mission.name.toLowerCase().includes(searchTerm);
        const matchesType = !typeFilter || mission.mission_type === typeFilter;
        const matchesState = !stateFilter || mission.state === stateFilter;
        return matchesSearch && matchesType && matchesState;
    });

    renderMissionsList(filtered);
}

function renderMissionsList(missions = allMissions) {
    const container = document.getElementById('missionsList');
    if (!container) return;

    if (missions.length === 0) {
        container.innerHTML = '<p style="color: #888; text-align: center; padding: 20px;">No missions found</p>';
        return;
    }

    container.innerHTML = missions.map(mission => {
        const stateColor = getStateColor(mission.state);
        const nextAction = computeNextAction(mission);

        return `
            <div class="mission-card" onclick="selectMission(${mission.id})" style="
                background: ${selectedMissionId === mission.id ? '#252525' : '#1a1a1a'};
                border: 1px solid ${selectedMissionId === mission.id ? '#667eea' : '#333'};
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
            ">
                <div style="font-weight: 600; margin-bottom: 5px;">${mission.name}</div>
                <div style="font-size: 0.85em; color: #888; margin-bottom: 8px;">
                    ${mission.mission_type} •
                    <span style="color: ${stateColor}; font-weight: 500;">${mission.state}</span>
                </div>
                <div style="font-size: 0.8em; color: #aaa;">
                    ${mission.box_count || 0} boxes • ${mission.artifact_count || 0} artifacts
                </div>
                ${nextAction ? `<div style="font-size: 0.8em; color: #667eea; margin-top: 5px;">
                    Next: ${nextAction}
                </div>` : ''}
            </div>
        `;
    }).join('');
}

function getStateColor(state) {
    switch(state) {
        case 'done': return '#2ecc71';
        case 'active': return '#3498db';
        case 'blocked': return '#e74c3c';
        case 'draft': return '#95a5a6';
        default: return '#888';
    }
}

function computeNextAction(mission) {
    // This is a simplified version - will be enhanced when we load full mission detail
    if (mission.state === 'done') return null;
    if (mission.state === 'draft') return 'Link artifacts (InboxBox)';
    return 'View mission for next step';
}

// ============================================================================
// MISSION SUMMARY
// ============================================================================

async function selectMission(missionId) {
    selectedMissionId = missionId;
    renderMissionsList(); // Re-render to highlight selection

    try {
        const response = await fetch(`/api/missions/${missionId}`);
        if (!response.ok) throw new Error('Failed to load mission detail');

        const detail = await response.json();
        renderMissionSummary(detail);
    } catch (error) {
        console.error('[Mission Control] Error loading mission detail:', error);
        showError('Failed to load mission detail');
    }
}

function renderMissionSummary(detail) {
    const container = document.getElementById('missionSummary');
    if (!container) return;

    const mission = detail.mission;
    const boxes = detail.boxes || [];
    const artifacts = detail.artifacts || [];

    const nextBox = findNextActionableBox(boxes);
    const nextActionHtml = nextBox
        ? `<button class="btn" onclick="runNextBox(${mission.id}, ${nextBox.id})">
            Run Next: ${nextBox.type}
           </button>`
        : '<p style="color: #2ecc71;">All boxes complete!</p>';

    const blockerMsg = nextBox && isBoxBlocked(nextBox, boxes)
        ? `<div style="background: #e74c3c; padding: 10px; border-radius: 6px; margin-top: 10px; font-size: 0.9em;">
            ⚠ Blocked: ${getBlockerReason(nextBox, boxes, detail)}
           </div>`
        : '';

    container.innerHTML = `
        <div style="margin-bottom: 20px;">
            <h3 style="color: #667eea; margin-bottom: 10px;">${mission.name}</h3>
            <div style="color: #888; font-size: 0.9em; margin-bottom: 5px;">
                Type: ${mission.mission_type} • State: ${mission.state}
            </div>
            <div style="color: #888; font-size: 0.85em;">
                Created: ${new Date(mission.created_at).toLocaleString()}
            </div>
        </div>

        <div style="margin-bottom: 20px;">
            ${nextActionHtml}
            ${blockerMsg}
            <button class="btn btn-secondary" onclick="openMissionDetail(${mission.id})" style="margin-left: 10px;">
                Open Full Detail
            </button>
        </div>

        <div style="margin-bottom: 20px;">
            <h4 style="color: #667eea; margin-bottom: 10px;">Boxes (${boxes.length})</h4>
            ${boxes.map((box, idx) => renderBoxCompact(box, idx)).join('')}
        </div>

        <div>
            <h4 style="color: #667eea; margin-bottom: 10px;">Recent Outputs (${Math.min(artifacts.length, 10)})</h4>
            ${artifacts.slice(0, 10).map(artifact => `
                <div style="background: #1a1a1a; border: 1px solid #333; padding: 10px; margin-bottom: 8px; border-radius: 6px; font-size: 0.9em;">
                    <div style="font-weight: 500;">${artifact.type}: ${artifact.title}</div>
                    <div style="color: #888; font-size: 0.85em;">
                        ${new Date(artifact.created_at).toLocaleString()}
                    </div>
                </div>
            `).join('') || '<p style="color: #888;">No artifacts yet</p>'}
        </div>
    `;
}

function renderBoxCompact(box, index) {
    const stateColor = getBoxStateColor(box.state);
    const stateBadge = `<span style="
        background: ${stateColor};
        color: white;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 0.75em;
        font-weight: 600;
    ">${box.state}</span>`;

    return `
        <div style="
            background: #1a1a1a;
            border-left: 3px solid ${stateColor};
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        ">
            <div>
                <span style="color: #888; font-size: 0.85em;">${index + 1}.</span>
                <span style="font-weight: 500; margin-left: 5px;">${box.type}</span>
            </div>
            ${stateBadge}
        </div>
    `;
}

function getBoxStateColor(state) {
    switch(state) {
        case 'done': return '#2ecc71';
        case 'running': return '#f39c12';
        case 'error': return '#e74c3c';
        case 'ready': return '#3498db';
        default: return '#555';
    }
}

function findNextActionableBox(boxes) {
    return boxes.find(box => box.state !== 'done' && box.state !== 'running');
}

function isBoxBlocked(box, allBoxes) {
    // Check if previous boxes in order are complete
    const currentIndex = allBoxes.findIndex(b => b.id === box.id);
    if (currentIndex === 0) return false; // First box never blocked by previous

    for (let i = 0; i < currentIndex; i++) {
        if (allBoxes[i].state !== 'done') {
            return true;
        }
    }
    return false;
}

function getBlockerReason(box, allBoxes, detail) {
    // Check previous boxes
    const currentIndex = allBoxes.findIndex(b => b.id === box.id);
    for (let i = 0; i < currentIndex; i++) {
        if (allBoxes[i].state !== 'done') {
            return `${allBoxes[i].type} must complete first`;
        }
    }

    // Check specific requirements
    if (box.type === 'extract' && detail.artifacts?.filter(a => a.type === 'document').length === 0) {
        return 'InboxBox incomplete: link at least 1 artifact';
    }
    if (box.type === 'practice' && detail.artifacts?.filter(a => a.type === 'document').length === 0) {
        return 'No documents linked: run InboxBox first';
    }

    return 'Unknown blocker';
}

async function runNextBox(missionId, boxId) {
    try {
        const response = await fetch(`/api/missions/${missionId}/boxes/${boxId}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_payload: {} })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to run box');
        }

        const result = await response.json();
        console.log('[Mission Control] Box execution result:', result);

        showSuccess(`Box completed: ${result.state}`);

        // Refresh mission detail
        await selectMission(missionId);
    } catch (error) {
        console.error('[Mission Control] Error running box:', error);
        showError(error.message);
    }
}

// ============================================================================
// MISSION DETAIL MODAL
// ============================================================================

async function openMissionDetail(missionId) {
    try {
        const response = await fetch(`/api/missions/${missionId}`);
        if (!response.ok) throw new Error('Failed to load mission detail');

        const detail = await response.json();
        renderMissionDetail(detail);

        // v0.46: Initialize operation panels
        if (window.missionOperationsAPI) {
            await initializeOperationPanels(missionId, detail);
        }

        document.getElementById('missionDetailModal').style.display = 'block';
    } catch (error) {
        console.error('[Mission Control] Error opening mission detail:', error);
        showError('Failed to load mission detail');
    }
}

async function initializeOperationPanels(missionId, detail) {
    // Get box IDs
    const boxes = detail.boxes || [];
    const inboxBox = boxes.find(b => b.type === 'inbox');
    const askBox = boxes.find(b => b.type === 'ask');
    const practiceBox = boxes.find(b => b.type === 'practice');
    const citationsBox = boxes.find(b => b.type === 'citations');

    // Initialize each panel
    if (inboxBox) {
        await window.missionOperationsAPI.renderInboxPanel(missionId, inboxBox.id, detail);
    }
    if (askBox) {
        await window.missionOperationsAPI.renderAskPanel(missionId, askBox.id, detail);
    }
    if (practiceBox) {
        await window.missionOperationsAPI.renderPracticePanel(missionId, practiceBox.id, detail);
    }
    if (citationsBox) {
        await window.missionOperationsAPI.renderCitationsPanel(missionId, citationsBox.id, detail);
    }

    // Render artifacts panel
    renderArtifactsPanel(detail);

    // Render extract panel with run button
    renderExtractPanel(missionId, boxes.find(b => b.type === 'extract'), detail);
}

function renderArtifactsPanel(detail) {
    const panel = document.getElementById('artifactsPanelContent');
    if (!panel) return;

    const artifacts = detail.artifacts || [];

    panel.innerHTML = `
        <h4 style="color: #667eea; margin-bottom: 10px;">All Artifacts (${artifacts.length})</h4>
        ${artifacts.length > 0 ? artifacts.map(artifact => `
            <div style="background: #1a1a1a; border: 1px solid #333; padding: 10px; margin-bottom: 8px; border-radius: 6px;">
                <div><strong>${artifact.type}:</strong> ${artifact.title}</div>
                <div style="color: #888; font-size: 0.85em;">
                    Created: ${new Date(artifact.created_at).toLocaleString()}
                    ${artifact.box_id ? ` • Box: ${artifact.box_id}` : ''}
                </div>
            </div>
        `).join('') : '<p style="color: #888;">No artifacts yet</p>'}
    `;
}

function renderExtractPanel(missionId, extractBox, detail) {
    const panel = document.getElementById('extractPanelContent');
    if (!panel || !extractBox) return;

    const canRun = extractBox.state === 'idle' || extractBox.state === 'ready' || extractBox.state === 'error';
    const linkedArtifacts = detail.artifacts.filter(a => a.type === 'document').length;

    panel.innerHTML = `
        <div style="margin-bottom: 15px;">
            <div style="background: #1a1a1a; border: 1px solid #333; padding: 15px; border-radius: 6px;">
                <div style="margin-bottom: 10px;">
                    <strong>Status:</strong>
                    <span style="background: ${getBoxStateColor(extractBox.state)}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.85em; margin-left: 10px;">
                        ${extractBox.state}
                    </span>
                </div>
                ${extractBox.last_run_at ? `<div style="color: #888; font-size: 0.85em; margin-bottom: 10px;">Last run: ${new Date(extractBox.last_run_at).toLocaleString()}</div>` : ''}
                ${extractBox.last_error ? `<div style="color: #e74c3c; font-size: 0.85em; margin-bottom: 10px;">Error: ${extractBox.last_error}</div>` : ''}

                <div style="margin-bottom: 15px; color: #888;">
                    <strong>Linked documents:</strong> ${linkedArtifacts}
                </div>

                ${canRun ? `
                    <button class="btn" onclick="runBox(${missionId}, ${extractBox.id})">
                        Run Extract Box
                    </button>
                ` : `
                    <p style="color: #888;">Box is ${extractBox.state}</p>
                `}
            </div>
        </div>

        <div>
            <h4 style="color: #667eea; margin-bottom: 10px;">Extracted Notes</h4>
            ${detail.artifacts.filter(a => a.type === 'note').map(note => `
                <div style="background: #1a1a1a; border: 1px solid #2ecc71; padding: 10px; margin-bottom: 8px; border-radius: 6px;">
                    <div><strong>${note.title}</strong></div>
                    <div style="color: #888; font-size: 0.85em;">
                        ${new Date(note.created_at).toLocaleString()}
                    </div>
                </div>
            `).join('') || '<p style="color: #888;">No notes extracted yet</p>'}
        </div>
    `;
}

function renderMissionDetail(detail) {
    const titleEl = document.getElementById('missionDetailTitle');
    if (!titleEl) return;
    titleEl.textContent = detail.mission.name;
}

function renderBoxDetail(box, missionId) {
    const canRun = box.state === 'idle' || box.state === 'ready' || box.state === 'error';
    const runButton = canRun
        ? `<button class="btn btn-secondary" onclick="runBox(${missionId}, ${box.id})" style="margin-left: 10px;">Run</button>`
        : '';

    return `
        <div style="background: #1a1a1a; border: 1px solid #333; padding: 15px; margin-bottom: 10px; border-radius: 6px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div>
                    <strong>${box.type}</strong>
                    <span style="background: ${getBoxStateColor(box.state)}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; margin-left: 10px;">
                        ${box.state}
                    </span>
                </div>
                ${runButton}
            </div>
            ${box.last_run_at ? `<div style="color: #888; font-size: 0.85em;">Last run: ${new Date(box.last_run_at).toLocaleString()}</div>` : ''}
            ${box.last_error ? `<div style="color: #e74c3c; font-size: 0.85em; margin-top: 5px;">Error: ${box.last_error}</div>` : ''}
        </div>
    `;
}

async function runBox(missionId, boxId) {
    try {
        const response = await fetch(`/api/missions/${missionId}/boxes/${boxId}/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ input_payload: {} })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to run box');
        }

        const result = await response.json();
        console.log('[Mission Control] Box execution result:', result);

        showSuccess(`Box completed: ${result.state}`);

        // Refresh mission detail
        await openMissionDetail(missionId);
        await selectMission(missionId); // Also refresh summary
    } catch (error) {
        console.error('[Mission Control] Error running box:', error);
        showError(error.message);
    }
}

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

function showSuccess(message) {
    // Use existing showSuccess if available, otherwise console
    if (window.showSuccess) {
        window.showSuccess(message);
    } else {
        console.log(`[SUCCESS] ${message}`);
        alert(message);
    }
}

function showError(message) {
    // Use existing showError if available, otherwise console
    if (window.showError) {
        window.showError(message);
    } else {
        console.error(`[ERROR] ${message}`);
        alert(`Error: ${message}`);
    }
}

// Export for use in app.js
if (typeof window !== 'undefined') {
    window.missionControlAPI = {
        initMissionControl,
        loadMissions,
        selectMission,
        createMission,
        runBox,
        runNextBox,
        openMissionDetail,
        filterMissions
    };
}
