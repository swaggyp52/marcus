/**
 * Marcus v0.50: Syllabus Intake UI
 * 
 * Vanilla JS, no frameworks. Works with existing marcus_app/frontend structure.
 * Batch upload -> classification -> confirmation -> creation -> receipt.
 */

class IntakeUI {
    constructor() {
        this.files = [];
        this.classifications = {};
        this.confirmations = {};
        this.receipts = [];
        this.currentStep = 'upload'; // 'upload' | 'classify' | 'confirm' | 'receipt'
    }

    /**
     * Initialize the Intake tab in the main UI.
     * Call this once when the app loads.
     */
    init() {
        this.createTabButton();
        this.createIntakePanel();
        this.bindEvents();
    }

    createTabButton() {
        const tabBar = document.querySelector('[data-component="tab-bar"]') || 
                       document.querySelector('.tab-bar') ||
                       document.querySelector('nav');
        
        if (!tabBar) return;

        const intakeTab = document.createElement('button');
        intakeTab.id = 'tab-intake';
        intakeTab.className = 'tab-button';
        intakeTab.innerHTML = '📚 Intake';
        intakeTab.onclick = () => this.showPanel();
        
        tabBar.appendChild(intakeTab);
    }

    createIntakePanel() {
        const container = document.body;
        
        const panel = document.createElement('div');
        panel.id = 'intake-panel';
        panel.className = 'intake-panel hidden';
        panel.innerHTML = `
            <div class="intake-header">
                <h2>📚 Syllabus Intake</h2>
                <p class="intake-subtitle">Bulk upload syllabi and extract deadlines</p>
            </div>

            <!-- UPLOAD STEP -->
            <div id="intake-upload-step" class="intake-step">
                <div class="intake-drop-zone" id="intake-drop-zone">
                    <p>Drop syllabi here (PDF, images, text)</p>
                    <input type="file" id="intake-file-input" multiple accept=".pdf,.jpg,.png,.txt">
                    <button id="intake-browse-btn">Browse Files</button>
                </div>
                
                <div id="intake-file-list" class="intake-file-list hidden">
                    <h3>Files to process</h3>
                    <ul id="intake-files-ul"></ul>
                    <button id="intake-process-btn" class="btn-primary">Process Files</button>
                </div>
            </div>

            <!-- CLASSIFY STEP -->
            <div id="intake-classify-step" class="intake-step hidden">
                <h3>Extracting class information...</h3>
                <div id="intake-classify-progress" class="progress-bar">
                    <div id="intake-classify-fill" class="progress-fill"></div>
                </div>
                <p id="intake-classify-status">Loading...</p>
            </div>

            <!-- CONFIRM STEP -->
            <div id="intake-confirm-step" class="intake-step hidden">
                <h3>Confirm class information</h3>
                <div id="intake-confirm-list" class="intake-confirm-list"></div>
                <div class="intake-actions">
                    <button id="intake-confirm-btn" class="btn-primary">Confirm & Create</button>
                    <button id="intake-back-btn" class="btn-secondary">Back</button>
                </div>
            </div>

            <!-- RECEIPT STEP -->
            <div id="intake-receipt-step" class="intake-step hidden">
                <h3>Intake Complete</h3>
                <div id="intake-receipt-content" class="intake-receipt"></div>
                <button id="intake-done-btn" class="btn-primary">Done</button>
            </div>
        `;
        
        container.appendChild(panel);
        this.panel = panel;
    }

    bindEvents() {
        // Upload step
        const dropZone = document.getElementById('intake-drop-zone');
        const fileInput = document.getElementById('intake-file-input');
        const browseBtn = document.getElementById('intake-browse-btn');
        const processBtn = document.getElementById('intake-process-btn');

        browseBtn.onclick = () => fileInput.click();

        fileInput.onchange = (e) => {
            this.files = Array.from(e.target.files);
            this.displayFileList();
        };

        dropZone.ondragover = (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        };

        dropZone.ondragleave = () => {
            dropZone.classList.remove('drag-over');
        };

        dropZone.ondrop = (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.files = Array.from(e.dataTransfer.files);
            this.displayFileList();
        };

        processBtn.onclick = () => this.processFiles();

        // Confirm step
        document.getElementById('intake-confirm-btn').onclick = () => this.confirmAndCreate();
        document.getElementById('intake-back-btn').onclick = () => this.goBack();

        // Receipt step
        document.getElementById('intake-done-btn').onclick = () => this.reset();
    }

    displayFileList() {
        const list = document.getElementById('intake-file-list');
        const ul = document.getElementById('intake-files-ul');
        const dropZone = document.getElementById('intake-drop-zone');

        ul.innerHTML = '';
        this.files.forEach(file => {
            const li = document.createElement('li');
            li.textContent = `${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
            ul.appendChild(li);
        });

        dropZone.classList.add('hidden');
        list.classList.remove('hidden');
    }

    processFiles() {
        if (this.files.length === 0) {
            alert('No files selected');
            return;
        }

        this.currentStep = 'classify';
        this.showStep('classify');

        // Simulate async file reading + classification
        let processed = 0;
        
        this.files.forEach((file, idx) => {
            const reader = new FileReader();
            
            reader.onload = (e) => {
                const content = e.target.result;
                
                // Call backend to classify
                fetch('/api/intake/classify', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        filename: file.name,
                        content: content.substring(0, 5000)  // limit size
                    })
                })
                .then(r => r.json())
                .then(classification => {
                    this.classifications[file.name] = classification;
                    processed++;
                    
                    const progress = Math.round((processed / this.files.length) * 100);
                    document.getElementById('intake-classify-fill').style.width = progress + '%';
                    document.getElementById('intake-classify-status').textContent = 
                        `${processed} of ${this.files.length} files processed`;
                    
                    if (processed === this.files.length) {
                        setTimeout(() => this.showConfirmStep(), 500);
                    }
                })
                .catch(err => {
                    console.error('Classification error:', err);
                    alert(`Error processing ${file.name}: ${err.message}`);
                });
            };
            
            reader.readAsText(file);
        });
    }

    showConfirmStep() {
        this.currentStep = 'confirm';
        this.showStep('confirm');
        
        const confirmList = document.getElementById('intake-confirm-list');
        confirmList.innerHTML = '';

        Object.entries(this.classifications).forEach(([filename, classification]) => {
            const item = document.createElement('div');
            item.className = 'intake-confirm-item';
            item.innerHTML = `
                <h4>${filename}</h4>
                
                <label>
                    Class Code
                    <input type="text" class="intake-input" 
                        value="${classification.class_code || ''}"
                        data-file="${filename}" data-field="class_code">
                </label>
                
                <label>
                    Class Name
                    <input type="text" class="intake-input"
                        value="${classification.class_name || ''}"
                        data-file="${filename}" data-field="class_name">
                </label>
                
                <label>
                    Instructor
                    <input type="text" class="intake-input"
                        value="${classification.instructor || ''}"
                        data-file="${filename}" data-field="instructor">
                </label>
                
                <p class="intake-confidence">
                    Confidence: ${(classification.confidence * 100).toFixed(0)}%
                </p>
            `;
            
            confirmList.appendChild(item);
        });

        // Bind input changes to confirmations
        document.querySelectorAll('.intake-input').forEach(input => {
            input.onchange = (e) => {
                const filename = e.target.dataset.file;
                const field = e.target.dataset.field;
                
                if (!this.confirmations[filename]) {
                    this.confirmations[filename] = {};
                }
                this.confirmations[filename][field] = e.target.value;
            };
        });
    }

    confirmAndCreate() {
        if (Object.keys(this.confirmations).length === 0) {
            alert('Please confirm at least one class');
            return;
        }

        // Call backend to create classes/items
        fetch('/api/intake/confirm', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                classifications: this.classifications,
                confirmations: this.confirmations
            })
        })
        .then(r => r.json())
        .then(receipt => {
            this.showReceiptStep(receipt);
        })
        .catch(err => {
            alert(`Error creating classes: ${err.message}`);
        });
    }

    showReceiptStep(receipt) {
        this.currentStep = 'receipt';
        this.showStep('receipt');
        
        const receiptContent = document.getElementById('intake-receipt-content');
        receiptContent.innerHTML = `
            <div class="intake-receipt-content">
                <p class="receipt-icon">✅</p>
                <p class="receipt-primary">${receipt.primary}</p>
                <p class="receipt-details">${receipt.details}</p>
                <p class="receipt-id">Receipt: ${receipt.secondary}</p>
                
                ${receipt.errors && receipt.errors.length > 0 ? `
                    <div class="receipt-errors">
                        <h4>⚠️ Errors</h4>
                        <ul>
                            ${receipt.errors.map(e => `<li>${e.file}: ${e.message}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
                
                ${receipt.low_confidence_items && receipt.low_confidence_items.length > 0 ? `
                    <div class="receipt-warnings">
                        <h4>📋 Needs Review (in Inbox)</h4>
                        <ul>
                            ${receipt.low_confidence_items.map(i => `<li>${i.title}</li>`).join('')}
                        </ul>
                    </div>
                ` : ''}
            </div>
        `;
        
        this.receipts.push(receipt);
    }

    showPanel() {
        // Hide other panels
        document.querySelectorAll('.panel:not(#intake-panel)').forEach(p => p.classList.add('hidden'));
        
        this.panel.classList.remove('hidden');
        document.getElementById('tab-intake').classList.add('active');
    }

    showStep(step) {
        document.querySelectorAll('.intake-step').forEach(s => s.classList.add('hidden'));
        document.getElementById(`intake-${step}-step`).classList.remove('hidden');
    }

    goBack() {
        this.showStep('upload');
        this.files = [];
        this.classifications = {};
    }

    reset() {
        this.goBack();
        this.confirmations = {};
    }
}

// Auto-initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    window.intakeUI = new IntakeUI();
    window.intakeUI.init();
});
