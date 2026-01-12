/**
 * Marcus v0.45 - Life View v2 (2D Graph Visualization)
 *
 * Force-directed graph visualization of:
 * - Missions, Boxes, Artifacts
 * - Classes, Projects, Study Packs
 * - Practice Sessions/Items, Claims
 *
 * Navigation tool: click node → jump to underlying object
 */

let lifeGraphData = { nodes: [], edges: [] };
let lifeGraphNodes = [];
let lifeGraphEdges = [];
let lifeGraphCanvas = null;
let lifeGraphCtx = null;
let lifeGraphTransform = { x: 0, y: 0, scale: 1 };
let lifeGraphDragging = null;
let lifeGraphPanning = false;
let lifeGraphPanStart = { x: 0, y: 0 };

// Physics simulation
let lifeGraphSimulationRunning = false;
const REPULSION = 5000;
const ATTRACTION = 0.01;
const DAMPING = 0.8;
const MIN_DISTANCE = 50;

// ============================================================================
// INITIALIZATION
// ============================================================================

async function initLifeView() {
    console.log('[Life View v2] Initializing...');

    lifeGraphCanvas = document.getElementById('lifeGraphCanvas');
    if (!lifeGraphCanvas) {
        console.error('[Life View v2] Canvas not found');
        return;
    }

    lifeGraphCtx = lifeGraphCanvas.getContext('2d');

    // Setup event listeners
    lifeGraphCanvas.addEventListener('mousedown', onLifeGraphMouseDown);
    lifeGraphCanvas.addEventListener('mousemove', onLifeGraphMouseMove);
    lifeGraphCanvas.addEventListener('mouseup', onLifeGraphMouseUp);
    lifeGraphCanvas.addEventListener('wheel', onLifeGraphWheel);
    lifeGraphCanvas.addEventListener('click', onLifeGraphClick);

    await refreshLifeGraph();
}

// ============================================================================
// LOAD GRAPH DATA
// ============================================================================

async function refreshLifeGraph() {
    try {
        // Enable life-graph feature first
        await fetch('/api/life-graph/enable', { method: 'POST' });

        const response = await fetch('/api/life-graph');
        if (!response.ok) throw new Error('Failed to load life graph');

        lifeGraphData = await response.json();
        console.log(`[Life View v2] Loaded ${lifeGraphData.nodes.length} nodes, ${lifeGraphData.edges.length} edges`);

        processGraphData();
        startSimulation();
        renderLifeGraph();
        updateLifeGraphStats();
    } catch (error) {
        console.error('[Life View v2] Error loading graph:', error);
        showError('Failed to load life graph');
    }
}

function processGraphData() {
    // Convert API data to internal format with physics properties
    lifeGraphNodes = lifeGraphData.nodes.map(node => ({
        ...node,
        x: node.x || Math.random() * 800 + 200,
        y: node.y || Math.random() * 500 + 100,
        vx: 0,
        vy: 0,
        radius: getNodeRadius(node.node_type),
        color: getNodeColor(node.node_type),
        visible: true
    }));

    lifeGraphEdges = lifeGraphData.edges.map(edge => ({
        ...edge,
        source: lifeGraphNodes.find(n => n.id === edge.source_node_id),
        target: lifeGraphNodes.find(n => n.id === edge.target_node_id)
    })).filter(edge => edge.source && edge.target);

    console.log(`[Life View v2] Processed ${lifeGraphNodes.length} nodes, ${lifeGraphEdges.length} edges`);
}

function getNodeRadius(nodeType) {
    switch(nodeType) {
        case 'mission': return 12;
        case 'mission_box': return 8;
        case 'mission_artifact': return 6;
        case 'class': return 14;
        case 'project': return 12;
        case 'study_pack': return 10;
        default: return 8;
    }
}

function getNodeColor(nodeType) {
    switch(nodeType) {
        case 'mission': return '#667eea';
        case 'mission_box': return '#3498db';
        case 'mission_artifact': return '#2ecc71';
        case 'class': return '#e74c3c';
        case 'project': return '#f39c12';
        case 'study_pack': return '#9b59b6';
        case 'artifact': return '#1abc9c';
        default: return '#95a5a6';
    }
}

// ============================================================================
// PHYSICS SIMULATION (Force-Directed Layout)
// ============================================================================

function startSimulation() {
    if (lifeGraphSimulationRunning) return;

    lifeGraphSimulationRunning = true;
    let iterations = 0;
    const maxIterations = 300;

    const simulate = () => {
        if (iterations >= maxIterations) {
            lifeGraphSimulationRunning = false;
            console.log('[Life View v2] Simulation complete');
            return;
        }

        applyForces();
        iterations++;

        if (iterations % 10 === 0) {
            renderLifeGraph();
        }

        if (lifeGraphSimulationRunning) {
            requestAnimationFrame(simulate);
        }
    };

    simulate();
}

function applyForces() {
    const visibleNodes = lifeGraphNodes.filter(n => n.visible);

    // Reset forces
    visibleNodes.forEach(node => {
        node.vx = 0;
        node.vy = 0;
    });

    // Repulsion between all nodes
    for (let i = 0; i < visibleNodes.length; i++) {
        for (let j = i + 1; j < visibleNodes.length; j++) {
            const nodeA = visibleNodes[i];
            const nodeB = visibleNodes[j];

            const dx = nodeB.x - nodeA.x;
            const dy = nodeB.y - nodeA.y;
            const distSq = dx * dx + dy * dy;
            const dist = Math.sqrt(distSq) || 1;

            if (dist < MIN_DISTANCE) continue;

            const force = REPULSION / distSq;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            nodeA.vx -= fx;
            nodeA.vy -= fy;
            nodeB.vx += fx;
            nodeB.vy += fy;
        }
    }

    // Attraction along edges
    lifeGraphEdges.forEach(edge => {
        if (!edge.source.visible || !edge.target.visible) return;

        const dx = edge.target.x - edge.source.x;
        const dy = edge.target.y - edge.source.y;
        const dist = Math.sqrt(dx * dx + dy * dy) || 1;

        const force = ATTRACTION * dist;
        const fx = (dx / dist) * force;
        const fy = (dy / dist) * force;

        edge.source.vx += fx;
        edge.source.vy += fy;
        edge.target.vx -= fx;
        edge.target.vy -= fy;
    });

    // Apply velocities with damping
    visibleNodes.forEach(node => {
        node.x += node.vx * DAMPING;
        node.y += node.vy * DAMPING;

        // Keep nodes in bounds
        node.x = Math.max(50, Math.min(1150, node.x));
        node.y = Math.max(50, Math.min(650, node.y));
    });
}

// ============================================================================
// RENDERING
// ============================================================================

function renderLifeGraph() {
    if (!lifeGraphCtx) return;

    const canvas = lifeGraphCanvas;
    const ctx = lifeGraphCtx;

    // Clear canvas
    ctx.fillStyle = '#0a0a0a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.save();
    ctx.translate(lifeGraphTransform.x, lifeGraphTransform.y);
    ctx.scale(lifeGraphTransform.scale, lifeGraphTransform.scale);

    // Draw edges
    ctx.strokeStyle = '#333';
    ctx.lineWidth = 1;
    lifeGraphEdges.forEach(edge => {
        if (!edge.source.visible || !edge.target.visible) return;

        ctx.beginPath();
        ctx.moveTo(edge.source.x, edge.source.y);
        ctx.lineTo(edge.target.x, edge.target.y);
        ctx.stroke();
    });

    // Draw nodes
    lifeGraphNodes.filter(n => n.visible).forEach(node => {
        ctx.fillStyle = node.color;
        ctx.beginPath();
        ctx.arc(node.x, node.y, node.radius, 0, Math.PI * 2);
        ctx.fill();

        // Border for selected/hover
        if (lifeGraphDragging === node) {
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
        }

        // Label (small)
        ctx.fillStyle = '#e0e0e0';
        ctx.font = '10px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(node.label.substring(0, 15), node.x, node.y + node.radius + 12);
    });

    ctx.restore();
}

// ============================================================================
// INTERACTION
// ============================================================================

function onLifeGraphMouseDown(e) {
    const rect = lifeGraphCanvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - lifeGraphTransform.x) / lifeGraphTransform.scale;
    const y = (e.clientY - rect.top - lifeGraphTransform.y) / lifeGraphTransform.scale;

    // Check if clicking on a node
    const node = findNodeAt(x, y);
    if (node) {
        lifeGraphDragging = node;
        lifeGraphSimulationRunning = false; // Stop simulation while dragging
        return;
    }

    // Start panning
    lifeGraphPanning = true;
    lifeGraphPanStart = { x: e.clientX - lifeGraphTransform.x, y: e.clientY - lifeGraphTransform.y };
}

function onLifeGraphMouseMove(e) {
    const rect = lifeGraphCanvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - lifeGraphTransform.x) / lifeGraphTransform.scale;
    const y = (e.clientY - rect.top - lifeGraphTransform.y) / lifeGraphTransform.scale;

    if (lifeGraphDragging) {
        lifeGraphDragging.x = x;
        lifeGraphDragging.y = y;
        renderLifeGraph();
    } else if (lifeGraphPanning) {
        lifeGraphTransform.x = e.clientX - lifeGraphPanStart.x;
        lifeGraphTransform.y = e.clientY - lifeGraphPanStart.y;
        renderLifeGraph();
    }
}

function onLifeGraphMouseUp(e) {
    lifeGraphDragging = null;
    lifeGraphPanning = false;
}

function onLifeGraphWheel(e) {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    lifeGraphTransform.scale = Math.max(0.5, Math.min(3, lifeGraphTransform.scale * delta));
    renderLifeGraph();
}

function onLifeGraphClick(e) {
    const rect = lifeGraphCanvas.getBoundingClientRect();
    const x = (e.clientX - rect.left - lifeGraphTransform.x) / lifeGraphTransform.scale;
    const y = (e.clientY - rect.top - lifeGraphTransform.y) / lifeGraphTransform.scale;

    const node = findNodeAt(x, y);
    if (node) {
        handleNodeClick(node);
    }
}

function findNodeAt(x, y) {
    return lifeGraphNodes.find(node => {
        if (!node.visible) return false;
        const dx = node.x - x;
        const dy = node.y - y;
        return Math.sqrt(dx * dx + dy * dy) < node.radius + 5;
    });
}

function handleNodeClick(node) {
    console.log('[Life View v2] Node clicked:', node);

    // Navigate based on node type
    switch(node.node_type) {
        case 'mission':
            // Switch to mission control and select this mission
            switchTab('missions');
            setTimeout(() => {
                if (window.missionControlAPI) {
                    window.missionControlAPI.selectMission(node.entity_id);
                }
            }, 100);
            break;

        case 'mission_box':
        case 'mission_artifact':
            // Try to find parent mission and open detail
            alert(`${node.node_type}: ${node.label}\n\nEntity ID: ${node.entity_id}\n\n(Full navigation coming soon)`);
            break;

        case 'class':
            switchTab('classes');
            break;

        case 'project':
            switchTab('projects');
            break;

        default:
            alert(`Node: ${node.label}\nType: ${node.node_type}\nID: ${node.entity_id}`);
    }
}

// ============================================================================
// CONTROLS
// ============================================================================

function filterLifeGraphNodes() {
    const showMissions = document.getElementById('showMissionsNodes')?.checked ?? true;
    const showBoxes = document.getElementById('showBoxesNodes')?.checked ?? true;
    const showArtifacts = document.getElementById('showArtifactsNodes')?.checked ?? true;
    const showClasses = document.getElementById('showClassesNodes')?.checked ?? true;

    lifeGraphNodes.forEach(node => {
        switch(node.node_type) {
            case 'mission':
                node.visible = showMissions;
                break;
            case 'mission_box':
                node.visible = showBoxes;
                break;
            case 'mission_artifact':
                node.visible = showArtifacts;
                break;
            case 'class':
            case 'project':
            case 'study_pack':
            case 'artifact':
                node.visible = showClasses;
                break;
            default:
                node.visible = true;
        }
    });

    renderLifeGraph();
}

function resetLifeGraphLayout() {
    // Re-randomize positions
    lifeGraphNodes.forEach(node => {
        node.x = Math.random() * 800 + 200;
        node.y = Math.random() * 500 + 100;
        node.vx = 0;
        node.vy = 0;
    });

    startSimulation();
}

function centerLifeGraph() {
    lifeGraphTransform.x = 0;
    lifeGraphTransform.y = 0;
    lifeGraphTransform.scale = 1;
    renderLifeGraph();
}

function updateLifeGraphStats() {
    const statsEl = document.getElementById('lifeGraphStats');
    if (!statsEl) return;

    const visibleNodes = lifeGraphNodes.filter(n => n.visible);
    const nodesByType = {};
    visibleNodes.forEach(node => {
        nodesByType[node.node_type] = (nodesByType[node.node_type] || 0) + 1;
    });

    const statsText = `${visibleNodes.length} nodes, ${lifeGraphEdges.length} edges | ` +
        Object.entries(nodesByType).map(([type, count]) => `${type}: ${count}`).join(', ');

    statsEl.textContent = statsText;
}

// Export for global access
if (typeof window !== 'undefined') {
    window.lifeViewAPI = {
        initLifeView,
        refreshLifeGraph,
        resetLifeGraphLayout,
        centerLifeGraph,
        filterLifeGraphNodes
    };
}
