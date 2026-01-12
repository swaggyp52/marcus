/**
 * Agent Chat UI - v0.47b
 *
 * Central command interface for Marcus.
 * Executes real actions, not suggestions.
 *
 * Design Rule: Marcus EXECUTES, not suggests.
 */

class AgentChat {
    constructor() {
        this.messages = [];
        this.pendingConfirmation = null;
        this.isProcessing = false;
        this.inputController = new AgentInputController();
        this.autocompleteDebounceTimer = null;
    }

    init(containerId) {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            console.error('Agent chat container not found');
            return;
        }

        this.render();
        this.setupKeybindings();
        this.loadWelcomeMessage();
    }

    render() {
        this.container.innerHTML = `
            <div class="agent-chat">
                <div class="agent-messages" id="agentMessages">
                    <!-- Messages appear here -->
                </div>

                <div class="agent-input-container">
                    <textarea
                        id="agentInput"
                        class="agent-input"
                        placeholder="Type a command... (e.g., 'add task finish homework', 'what's next?', 'show inbox')"
                        rows="1"
                    ></textarea>
                    <button id="agentSend" class="agent-send-btn">
                        Send
                    </button>
                </div>

                <div class="agent-suggestions" id="agentSuggestions">
                    <!-- Quick suggestions -->
                </div>
            </div>
        `;

        // Bind events
        const input = document.getElementById('agentInput');
        const sendBtn = document.getElementById('agentSend');

        sendBtn.addEventListener('click', () => this.sendCommand());
        input.addEventListener('keydown', (e) => this.handleKeydown(e));
        input.addEventListener('input', () => this.handleInput());

        // Auto-resize textarea
        input.addEventListener('input', () => {
            input.style.height = 'auto';
            input.style.height = (input.scrollHeight) + 'px';
        });
    }

    /**
     * Setup keybindings (v0.48)
     * - Enter: send
     * - Shift+Enter: newline
     * - Up/Down: navigate history
     * - Tab: autocomplete
     */
    setupKeybindings() {
        // Already integrated in render's keydown handler
    }

    /**
     * Handle keydown events with v0.48 keybindings
     */
    handleKeydown(e) {
        const input = document.getElementById('agentInput');
        const text = input.value;

        // Tab: autocomplete
        if (e.key === 'Tab') {
            e.preventDefault();
            const suggestion = this.inputController.acceptSuggestion(0);
            if (suggestion) {
                input.value = suggestion;
                input.style.height = 'auto';
                input.style.height = (input.scrollHeight) + 'px';
                this.hideAutocomplete();
            }
            return;
        }

        // Up/Down: command history navigation
        if (e.key === 'ArrowUp' && !this.hasOpenAutocomplete()) {
            e.preventDefault();
            const historyCommand = this.inputController.navigateHistory('up');
            if (historyCommand !== null) {
                input.value = historyCommand;
                input.style.height = 'auto';
                input.style.height = (input.scrollHeight) + 'px';
                // Move cursor to end
                input.selectionStart = input.selectionEnd = input.value.length;
            }
            return;
        }

        if (e.key === 'ArrowDown' && !this.hasOpenAutocomplete()) {
            e.preventDefault();
            const historyCommand = this.inputController.navigateHistory('down');
            if (historyCommand !== null) {
                input.value = historyCommand;
                input.style.height = 'auto';
                input.style.height = (input.scrollHeight) + 'px';
                // Move cursor to end
                input.selectionStart = input.selectionEnd = input.value.length;
            }
            return;
        }

        // Enter: send (unless Shift+Enter for newline)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.sendCommand();
            return;
        }

        // Shift+Enter: allow newline
        if (e.key === 'Enter' && e.shiftKey) {
            // Default behavior: newline
            return;
        }
    }

    /**
     * Handle input for autocomplete (debounced)
     */
    handleInput() {
        clearTimeout(this.autocompleteDebounceTimer);
        const input = document.getElementById('agentInput');
        const text = input.value.trim();

        // Minimum length for autocomplete
        if (text.length < 2) {
            this.hideAutocomplete();
            return;
        }

        this.autocompleteDebounceTimer = setTimeout(async () => {
            const suggestions = await this.inputController.fetchSuggestions(text);
            if (suggestions.length > 0) {
                this.showAutocompleteSuggestions(suggestions);
            } else {
                this.hideAutocomplete();
            }
        }, 150); // 150ms debounce
    }

    /**
     * Show autocomplete suggestions
     */
    showAutocompleteSuggestions(suggestions) {
        let container = document.getElementById('agentAutocompleteDropdown');
        if (!container) {
            container = document.createElement('div');
            container.id = 'agentAutocompleteDropdown';
            container.className = 'agent-autocomplete-dropdown';
            document.querySelector('.agent-input-container').appendChild(container);
        }

        container.innerHTML = suggestions.map((s, idx) => `
            <div class="autocomplete-item" onclick="agentChat.acceptAutocompleteSuggestion('${s.replace(/'/g, "\\'")}')">
                ${s}
            </div>
        `).join('');
        container.style.display = 'block';
    }

    /**
     * Hide autocomplete suggestions
     */
    hideAutocomplete() {
        const container = document.getElementById('agentAutocompleteDropdown');
        if (container) {
            container.style.display = 'none';
        }
    }

    /**
     * Check if autocomplete is currently visible
     */
    hasOpenAutocomplete() {
        const container = document.getElementById('agentAutocompleteDropdown');
        return container && container.style.display !== 'none';
    }

    /**
     * Accept autocomplete suggestion
     */
    acceptAutocompleteSuggestion(text) {
        const input = document.getElementById('agentInput');
        input.value = text;
        input.style.height = 'auto';
        input.style.height = (input.scrollHeight) + 'px';
        this.hideAutocomplete();
        input.focus();
    }

    loadWelcomeMessage() {
        this.addMessage({
            type: 'system',
            message: "Hi! I'm Marcus. I can help you:\n\n" +
                     "• Create tasks, notes, and events\n" +
                     "• Check your inbox and upcoming items\n" +
                     "• Manage missions\n" +
                     "• Show what's next\n\n" +
                     "Try: \"add task finish lab report by Friday\" or \"what's next?\"",
            timestamp: new Date()
        });

        this.showSuggestions([
            "What's next?",
            "Show inbox",
            "Add task...",
            "Create mission..."
        ]);
    }

    async sendCommand() {
        const input = document.getElementById('agentInput');
        const text = input.value.trim();

        if (!text || this.isProcessing) return;

        // Add to history (v0.48)
        this.inputController.addToHistory(text);
        this.hideAutocomplete();

        // Add user message
        this.addMessage({
            type: 'user',
            message: text,
            timestamp: new Date()
        });

        // Clear input
        input.value = '';
        input.style.height = 'auto';
        this.inputController.reset();

        // Show processing indicator
        this.isProcessing = true;
        this.showProcessing();

        try {
            // Send to backend
            const response = await fetch('/api/agent/command', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                throw new Error('Command failed');
            }

            const result = await response.json();

            // Remove processing indicator
            this.removeProcessing();

            // Handle confirmation needed
            if (result.needs_confirmation) {
                this.pendingConfirmation = result.confirmation_id;
                this.addMessage({
                    type: 'agent',
                    message: result.message,
                    timestamp: new Date(),
                    needsConfirmation: true,
                    confirmationId: result.confirmation_id
                });
            } else {
                // Show result
                this.addMessage({
                    type: 'agent',
                    message: result.message,
                    timestamp: new Date(),
                    actionCard: result.action_card
                });
            }

        } catch (error) {
            console.error('Command error:', error);
            this.removeProcessing();
            this.addMessage({
                type: 'error',
                message: 'Failed to process command. Please try again.',
                timestamp: new Date()
            });
        } finally {
            this.isProcessing = false;
        }
    }

    async confirmAction(confirmationId, confirmed) {
        this.showProcessing();

        try {
            const response = await fetch('/api/agent/confirm', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    action_id: confirmationId,
                    confirmed
                })
            });

            if (!response.ok) {
                throw new Error('Confirmation failed');
            }

            const result = await response.json();

            this.removeProcessing();

            // Show result
            this.addMessage({
                type: 'agent',
                message: result.message,
                timestamp: new Date(),
                actionCard: result.action_card
            });

            this.pendingConfirmation = null;

        } catch (error) {
            console.error('Confirmation error:', error);
            this.removeProcessing();
            this.addMessage({
                type: 'error',
                message: 'Failed to confirm action.',
                timestamp: new Date()
            });
        }
    }

    addMessage(messageData) {
        this.messages.push(messageData);

        const messagesContainer = document.getElementById('agentMessages');
        const messageEl = this.createMessageElement(messageData);

        messagesContainer.appendChild(messageEl);

        // Scroll to bottom
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    createMessageElement(messageData) {
        const div = document.createElement('div');
        div.className = `agent-message agent-message-${messageData.type}`;

        let content = '';

        // Icon
        let icon = '';
        if (messageData.type === 'user') {
            icon = '👤';
        } else if (messageData.type === 'agent') {
            icon = '🤖';
        } else if (messageData.type === 'system') {
            icon = 'ℹ️';
        } else if (messageData.type === 'error') {
            icon = '⚠️';
        }

        content += `
            <div class="message-icon">${icon}</div>
            <div class="message-content">
                <div class="message-text">${this.formatMessage(messageData.message)}</div>
        `;

        // Add confirmation buttons if needed
        if (messageData.needsConfirmation) {
            content += `
                <div class="message-actions">
                    <button class="btn btn-small btn-success" onclick="agentChat.confirmAction('${messageData.confirmationId}', true)">
                        ✓ Confirm
                    </button>
                    <button class="btn btn-small btn-secondary" onclick="agentChat.confirmAction('${messageData.confirmationId}', false)">
                        ✗ Cancel
                    </button>
                </div>
            `;
        }

        // Add action card if present
        if (messageData.actionCard) {
            content += this.createActionCard(messageData.actionCard);
        }

        content += `
                <div class="message-timestamp">${messageData.timestamp.toLocaleTimeString()}</div>
            </div>
        `;

        div.innerHTML = content;
        return div;
    }

    createActionCard(card) {
        let html = `<div class="action-card action-card-${card.type}">`;

        if (card.type === 'item_created') {
            html += `
                <div class="action-card-header">
                    <span class="action-card-icon">✓</span>
                    <strong>${card.item_type.charAt(0).toUpperCase() + card.item_type.slice(1)} Created</strong>
                </div>
                <div class="action-card-body">
                    <div class="action-card-detail"><strong>${card.title}</strong></div>
                    <div class="action-card-detail">Context: ${card.context}</div>
                    ${card.due_at ? `<div class="action-card-detail">Due: ${new Date(card.due_at).toLocaleString()}</div>` : ''}
                </div>
            `;
        } else if (card.type === 'mission_created') {
            html += `
                <div class="action-card-header">
                    <span class="action-card-icon">🎯</span>
                    <strong>Mission Created</strong>
                </div>
                <div class="action-card-body">
                    <div class="action-card-detail"><strong>${card.name}</strong></div>
                    <div class="action-card-detail">Type: ${card.mission_type}</div>
                    <div class="action-card-detail">State: ${card.state}</div>
                </div>
            `;
        } else if (card.type === 'inbox_list') {
            html += `
                <div class="action-card-header">
                    <span class="action-card-icon">📥</span>
                    <strong>Inbox Items (${card.count})</strong>
                </div>
                <div class="action-card-body">
                    ${card.items.slice(0, 5).map(item => `
                        <div class="action-card-item">
                            <span class="badge badge-type">${item.type}</span>
                            ${item.title}
                            <small style="color: #888;">(${item.context}, ${Math.round(item.confidence * 100)}% confident)</small>
                        </div>
                    `).join('')}
                    ${card.items.length > 5 ? `<div class="action-card-detail"><em>...and ${card.items.length - 5} more</em></div>` : ''}
                </div>
            `;
        } else if (card.type === 'next_items' || card.type === 'due_items') {
            html += `
                <div class="action-card-header">
                    <span class="action-card-icon">${card.type === 'next_items' ? '→' : '⏰'}</span>
                    <strong>${card.type === 'next_items' ? 'Next Items' : 'Due Items'}</strong>
                </div>
                <div class="action-card-body">
                    ${card.items.map(item => `
                        <div class="action-card-item">
                            <span class="badge badge-type">${item.type}</span>
                            ${item.title}
                            <small style="color: #888;">(${item.context}, ${item.due})</small>
                        </div>
                    `).join('')}
                </div>
            `;
        } else if (card.type === 'mission_summary') {
            html += `
                <div class="action-card-header">
                    <span class="action-card-icon">📊</span>
                    <strong>Mission Summary</strong>
                </div>
                <div class="action-card-body">
                    <div class="stats-grid">
                        <div class="stat-mini"><strong>${card.stats.active}</strong><br>Active</div>
                        <div class="stat-mini"><strong>${card.stats.blocked}</strong><br>Blocked</div>
                        <div class="stat-mini"><strong>${card.stats.done}</strong><br>Done</div>
                        <div class="stat-mini"><strong>${card.stats.draft}</strong><br>Draft</div>
                    </div>
                </div>
            `;
        } else if (card.type === 'blocked_missions') {
            html += `
                <div class="action-card-header">
                    <span class="action-card-icon">🚧</span>
                    <strong>Blocked Missions</strong>
                </div>
                <div class="action-card-body">
                    ${card.missions.map(mission => `
                        <div class="action-card-item">
                            ${mission.name} <small style="color: #888;">(${mission.type})</small>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        // Add action buttons if present
        if (card.actions && card.actions.length > 0) {
            html += `<div class="action-card-actions">`;
            for (const action of card.actions) {
                if (action.type === 'navigate') {
                    html += `<button class="btn btn-small btn-secondary" onclick="window.location.href='${action.target}'">${action.label}</button>`;
                } else if (action.type === 'command') {
                    html += `<button class="btn btn-small btn-secondary" onclick="agentChat.sendQuickCommand('${action.command}')">${action.label}</button>`;
                }
            }
            html += `</div>`;
        }

        html += `</div>`;
        return html;
    }

    sendQuickCommand(command) {
        const input = document.getElementById('agentInput');
        input.value = command;
        this.sendCommand();
    }

    formatMessage(text) {
        // Convert newlines to <br>
        return text.replace(/\n/g, '<br>');
    }

    showProcessing() {
        const messagesContainer = document.getElementById('agentMessages');
        const processingEl = document.createElement('div');
        processingEl.id = 'processingIndicator';
        processingEl.className = 'agent-message agent-message-agent';
        processingEl.innerHTML = `
            <div class="message-icon">🤖</div>
            <div class="message-content">
                <div class="message-text processing-dots">Processing<span>.</span><span>.</span><span>.</span></div>
            </div>
        `;
        messagesContainer.appendChild(processingEl);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    removeProcessing() {
        const processingEl = document.getElementById('processingIndicator');
        if (processingEl) {
            processingEl.remove();
        }
    }

    showSuggestions(suggestions) {
        const container = document.getElementById('agentSuggestions');
        container.innerHTML = suggestions.map(s => `
            <button class="suggestion-chip" onclick="agentChat.sendQuickCommand('${s}')">
                ${s}
            </button>
        `).join('');
    }
}

// Initialize agent chat
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.agentChat = new AgentChat();
    });
} else {
    window.agentChat = new AgentChat();
}
