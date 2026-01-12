/**
 * Globe rendering module using Canvas API
 * Creates an interactive 3D globe with neon styling
 */

export class Globe {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');
        this.rotation = 0;
        this.points = [];
        this.markers = [];
        this.resize();
        this.generatePoints();
        window.addEventListener('resize', () => this.resize());
    }

    resize() {
        const rect = this.canvas.getBoundingClientRect();
        this.canvas.width = rect.width;
        this.canvas.height = rect.height;
        this.centerX = this.canvas.width / 2;
        this.centerY = this.canvas.height / 2;
        this.radius = Math.min(this.canvas.width, this.canvas.height) / 2.5;
    }

    generatePoints() {
        // Generate points on sphere surface
        const numPoints = 500;
        this.points = [];
        
        for (let i = 0; i < numPoints; i++) {
            const phi = Math.acos(-1 + (2 * i) / numPoints);
            const theta = Math.sqrt(numPoints * Math.PI) * phi;
            
            this.points.push({
                phi: phi,
                theta: theta,
                x: 0,
                y: 0,
                z: 0
            });
        }
    }

    addMarker(lat, lon, name) {
        // Convert lat/lon to spherical coordinates
        const phi = (90 - lat) * Math.PI / 180;
        const theta = (lon + 180) * Math.PI / 180;
        
        this.markers.push({
            phi: phi,
            theta: theta,
            name: name,
            x: 0,
            y: 0,
            z: 0
        });
    }

    clearMarkers() {
        this.markers = [];
    }

    projectPoint(phi, theta, rotation) {
        // Rotate and project 3D point to 2D
        const x = Math.sin(phi) * Math.cos(theta + rotation);
        const y = Math.cos(phi);
        const z = Math.sin(phi) * Math.sin(theta + rotation);
        
        // Simple orthographic projection
        const scale = this.radius;
        const projX = this.centerX + x * scale;
        const projY = this.centerY + y * scale;
        
        return { x: projX, y: projY, z: z };
    }

    render() {
        // Clear canvas
        this.ctx.fillStyle = 'rgba(10, 10, 15, 0.1)';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw globe outline
        this.ctx.beginPath();
        this.ctx.arc(this.centerX, this.centerY, this.radius, 0, Math.PI * 2);
        this.ctx.strokeStyle = '#00f3ff';
        this.ctx.lineWidth = 2;
        this.ctx.shadowBlur = 15;
        this.ctx.shadowColor = '#00f3ff';
        this.ctx.stroke();
        this.ctx.shadowBlur = 0;
        
        // Draw latitude lines
        for (let lat = -60; lat <= 60; lat += 30) {
            this.ctx.beginPath();
            const phi = (90 - lat) * Math.PI / 180;
            for (let lon = 0; lon <= 360; lon += 5) {
                const theta = lon * Math.PI / 180;
                const proj = this.projectPoint(phi, theta, this.rotation);
                if (lon === 0) {
                    this.ctx.moveTo(proj.x, proj.y);
                } else {
                    this.ctx.lineTo(proj.x, proj.y);
                }
            }
            this.ctx.strokeStyle = 'rgba(0, 243, 255, 0.2)';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
        }
        
        // Draw longitude lines
        for (let lon = 0; lon < 360; lon += 30) {
            this.ctx.beginPath();
            const theta = lon * Math.PI / 180;
            for (let lat = -90; lat <= 90; lat += 5) {
                const phi = (90 - lat) * Math.PI / 180;
                const proj = this.projectPoint(phi, theta, this.rotation);
                if (lat === -90) {
                    this.ctx.moveTo(proj.x, proj.y);
                } else {
                    this.ctx.lineTo(proj.x, proj.y);
                }
            }
            this.ctx.strokeStyle = 'rgba(0, 243, 255, 0.2)';
            this.ctx.lineWidth = 1;
            this.ctx.stroke();
        }
        
        // Draw points
        const sortedPoints = [];
        
        for (const point of this.points) {
            const proj = this.projectPoint(point.phi, point.theta, this.rotation);
            point.x = proj.x;
            point.y = proj.y;
            point.z = proj.z;
            sortedPoints.push(point);
        }
        
        // Sort by z-index for proper depth
        sortedPoints.sort((a, b) => a.z - b.z);
        
        for (const point of sortedPoints) {
            if (point.z > 0) {
                // Point is on visible side
                const alpha = (point.z + 1) / 2;
                this.ctx.fillStyle = `rgba(0, 243, 255, ${alpha * 0.6})`;
                this.ctx.beginPath();
                this.ctx.arc(point.x, point.y, 1.5, 0, Math.PI * 2);
                this.ctx.fill();
            }
        }
        
        // Draw markers
        for (const marker of this.markers) {
            const proj = this.projectPoint(marker.phi, marker.theta, this.rotation);
            marker.x = proj.x;
            marker.y = proj.y;
            marker.z = proj.z;
            
            if (marker.z > 0) {
                // Marker is on visible side
                this.ctx.fillStyle = '#ff00ff';
                this.ctx.shadowBlur = 10;
                this.ctx.shadowColor = '#ff00ff';
                this.ctx.beginPath();
                this.ctx.arc(marker.x, marker.y, 5, 0, Math.PI * 2);
                this.ctx.fill();
                this.ctx.shadowBlur = 0;
                
                // Draw marker label
                this.ctx.fillStyle = '#ff00ff';
                this.ctx.font = '10px Courier New';
                this.ctx.fillText(marker.name, marker.x + 8, marker.y - 8);
            }
        }
        
        // Update rotation
        this.rotation += 0.005;
    }

    animate() {
        this.render();
        requestAnimationFrame(() => this.animate());
    }
}
