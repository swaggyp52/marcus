// Life View 2D Graph Visualization (Experimental)
// This is a minimal stub implementation behind a feature flag

class LifeView {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.nodes = [];
        this.edges = [];
        this.selectedNode = null;
        this.zoom = 1;
        this.pan = { x: 0, y: 0 };
        
        this.setupEventListeners();
    }

    setupEventListeners() {
        this.canvas.addEventListener('click', (e) => this.handleClick(e));
        this.canvas.addEventListener('wheel', (e) => this.handleZoom(e));
        this.canvas.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        this.canvas.addEventListener('mousedown', (e) => this.handleMouseDown(e));
    }

    async loadGraphData(graphData) {
        if (!graphData) {
            this.nodes = [];
            this.edges = [];
            return;
        }

        this.nodes = graphData.nodes || [];
        this.edges = graphData.edges || [];
        this.render();
    }

    render() {
        // Clear canvas
        this.ctx.fillStyle = '#0a0a0a';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Save context
        this.ctx.save();

        // Apply transformations
        this.ctx.translate(this.canvas.width / 2 + this.pan.x, this.canvas.height / 2 + this.pan.y);
        this.ctx.scale(this.zoom, this.zoom);

        // Draw edges
        this.drawEdges();

        // Draw nodes
        this.drawNodes();

        // Restore context
        this.ctx.restore();
    }

    drawEdges() {
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 1 / this.zoom;

        this.edges.forEach(edge => {
            const from = this.nodes.find(n => n.id === edge.source);
            const to = this.nodes.find(n => n.id === edge.target);

            if (from && to) {
                this.ctx.beginPath();
                this.ctx.moveTo(from.x || 0, from.y || 0);
                this.ctx.lineTo(to.x || 0, to.y || 0);
                this.ctx.stroke();

                // Draw arrow
                this.drawArrow(from.x || 0, from.y || 0, to.x || 0, to.y || 0);
            }
        });
    }

    drawArrow(fromX, fromY, toX, toY) {
        const headlen = 15 / this.zoom;
        const angle = Math.atan2(toY - fromY, toX - fromX);

        // Arrow back line
        const arrowX = toX - headlen * Math.cos(angle);
        const arrowY = toY - headlen * Math.sin(angle);

        // Arrow head
        this.ctx.beginPath();
        this.ctx.moveTo(toX, toY);
        this.ctx.lineTo(arrowX - headlen * Math.sin(angle), arrowY + headlen * Math.cos(angle));
        this.ctx.lineTo(arrowX + headlen * Math.sin(angle), arrowY - headlen * Math.cos(angle));
        this.ctx.closePath();
        this.ctx.fillStyle = '#667eea';
        this.ctx.fill();
    }

    drawNodes() {
        const nodeRadius = 15 / this.zoom;

        this.nodes.forEach(node => {
            const x = node.x || 0;
            const y = node.y || 0;

            // Determine node color based on type
            let color = '#667eea';
            if (node.type === 'commit') color = '#27ae60';
            else if (node.type === 'branch') color = '#f39c12';
            else if (node.type === 'tag') color = '#e74c3c';

            // Highlight selected node
            if (this.selectedNode && this.selectedNode.id === node.id) {
                this.ctx.fillStyle = '#fff';
                this.ctx.beginPath();
                this.ctx.arc(x, y, nodeRadius * 1.3, 0, Math.PI * 2);
                this.ctx.fill();
            }

            // Draw node circle
            this.ctx.fillStyle = color;
            this.ctx.beginPath();
            this.ctx.arc(x, y, nodeRadius, 0, Math.PI * 2);
            this.ctx.fill();

            // Draw node label
            this.ctx.fillStyle = '#e0e0e0';
            this.ctx.font = `${12 / this.zoom}px Arial`;
            this.ctx.textAlign = 'center';
            this.ctx.textBaseline = 'middle';
            
            const label = node.label || node.id.slice(0, 7);
            this.ctx.fillText(label, x, y + nodeRadius + 25 / this.zoom);
        });
    }

    handleClick(e) {
        const rect = this.canvas.getBoundingClientRect();
        const x = (e.clientX - rect.left - this.canvas.width / 2 - this.pan.x) / this.zoom;
        const y = (e.clientY - rect.top - this.canvas.height / 2 - this.pan.y) / this.zoom;

        // Check if click is on a node
        const nodeRadius = 15 / this.zoom;
        const clickedNode = this.nodes.find(node => {
            const dx = x - (node.x || 0);
            const dy = y - (node.y || 0);
            return Math.sqrt(dx * dx + dy * dy) < nodeRadius;
        });

        this.selectedNode = clickedNode;
        this.render();

        if (clickedNode) {
            this.showNodeDetails(clickedNode);
        }
    }

    showNodeDetails(node) {
        const details = `
            Node: ${node.id}
            Type: ${node.type}
            Label: ${node.label}
            ${node.metadata ? `Data: ${JSON.stringify(node.metadata)}` : ''}
        `;
        console.log('Selected Node:', details);
    }

    handleZoom(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? 0.9 : 1.1;
        this.zoom *= delta;
        this.zoom = Math.max(0.5, Math.min(3, this.zoom)); // Clamp zoom
        this.render();
    }

    handleMouseDown(e) {
        this.dragStart = { x: e.clientX, y: e.clientY };
    }

    handleMouseMove(e) {
        if (!this.dragStart) return;

        const dx = e.clientX - this.dragStart.x;
        const dy = e.clientY - this.dragStart.y;

        this.pan.x += dx;
        this.pan.y += dy;

        this.dragStart = { x: e.clientX, y: e.clientY };
        this.render();
    }

    clear() {
        this.nodes = [];
        this.edges = [];
        this.selectedNode = null;
        this.render();
    }
}

// Initialize Life View when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    const canvas = document.getElementById('lifeGraphCanvas');
    if (canvas) {
        window.lifeView = new LifeView('lifeGraphCanvas');
    }
});
