/**
 * Agent Input Controller - v0.48
 * 
 * Handles:
 * - Command history (ring buffer)
 * - Keybindings (Enter, Shift+Enter, Up/Down, Tab)
 * - Autocomplete with suggestions
 * - Command parsing and validation
 */

class AgentInputController {
    constructor(options = {}) {
        this.maxHistory = options.maxHistory || 50;
        this.commandHistory = [];
        this.historyIndex = -1;
        this.autocompleteCache = {};
        this.suggestedItems = [];
        this.selectedSuggestionIndex = -1;
        this.isAwaitingAutocomplete = false;
        
        this.loadHistoryFromStorage();
    }

    /**
     * Load command history from localStorage
     */
    loadHistoryFromStorage() {
        try {
            const stored = localStorage.getItem('agentCommandHistory');
            if (stored) {
                this.commandHistory = JSON.parse(stored);
                this.historyIndex = -1;
            }
        } catch (e) {
            console.error('Failed to load command history:', e);
        }
    }

    /**
     * Save command history to localStorage
     */
    saveHistoryToStorage() {
        try {
            // Keep only last maxHistory items
            const toSave = this.commandHistory.slice(-this.maxHistory);
            localStorage.setItem('agentCommandHistory', JSON.stringify(toSave));
        } catch (e) {
            console.error('Failed to save command history:', e);
        }
    }

    /**
     * Add command to history
     */
    addToHistory(command) {
        if (!command.trim()) return;
        
        // Don't add duplicate consecutive commands
        if (this.commandHistory.length > 0 && 
            this.commandHistory[this.commandHistory.length - 1] === command) {
            return;
        }
        
        this.commandHistory.push(command);
        if (this.commandHistory.length > this.maxHistory) {
            this.commandHistory.shift();
        }
        this.saveHistoryToStorage();
        this.historyIndex = -1; // Reset to bottom
    }

    /**
     * Navigate history (Up = previous, Down = next)
     */
    navigateHistory(direction) {
        if (this.commandHistory.length === 0) return null;

        if (direction === 'up') {
            if (this.historyIndex === -1) {
                this.historyIndex = this.commandHistory.length - 1;
            } else if (this.historyIndex > 0) {
                this.historyIndex--;
            }
        } else if (direction === 'down') {
            if (this.historyIndex < this.commandHistory.length - 1) {
                this.historyIndex++;
            } else if (this.historyIndex === this.commandHistory.length - 1) {
                this.historyIndex = -1;
                return '';
            }
        }

        return this.historyIndex === -1 ? '' : this.commandHistory[this.historyIndex];
    }

    /**
     * Fetch autocomplete suggestions
     */
    async fetchSuggestions(query) {
        if (!query || query.length < 1) {
            this.suggestedItems = [];
            return [];
        }

        // Check cache first
        const cacheKey = query.toLowerCase();
        if (this.autocompleteCache[cacheKey]) {
            this.suggestedItems = this.autocompleteCache[cacheKey];
            return this.suggestedItems;
        }

        try {
            // Determine what type of suggestion to fetch based on query
            let suggestions = [];

            // Try multiple suggestion endpoints
            const [classes, projects, missions, commands] = await Promise.all([
                this.getSuggestionType('classes', query),
                this.getSuggestionType('projects', query),
                this.getSuggestionType('missions', query),
                this.getSuggestionType('commands', query)
            ]);

            suggestions = [
                ...commands,      // Commands first (quick access)
                ...classes,       // Then classes
                ...projects,      // Then projects
                ...missions       // Then missions
            ].slice(0, 8);        // Limit to 8 suggestions

            this.autocompleteCache[cacheKey] = suggestions;
            this.suggestedItems = suggestions;
            return suggestions;
        } catch (e) {
            console.error('Autocomplete fetch failed:', e);
            return [];
        }
    }

    /**
     * Get suggestions for a specific type
     */
    async getSuggestionType(type, query) {
        try {
            const response = await fetch(`/api/suggest/${type}?q=${encodeURIComponent(query)}`);
            if (!response.ok) return [];
            const data = await response.json();
            return Array.isArray(data) ? data : [];
        } catch (e) {
            // Graceful failure
            return [];
        }
    }

    /**
     * Accept current autocomplete suggestion
     */
    acceptSuggestion(index = 0) {
        if (index < 0 || index >= this.suggestedItems.length) return null;
        return this.suggestedItems[index];
    }

    /**
     * Parse command for keybinding processing
     */
    parseCommand(text) {
        const trimmed = text.trim();
        const words = trimmed.split(/\s+/);
        const intent = words[0]?.toLowerCase() || '';

        return {
            raw: text,
            trimmed: trimmed,
            words: words,
            intent: intent,
            isQuery: intent.includes('?') || ['what', 'show', 'list', 'get'].includes(intent),
            isAction: ['add', 'create', 'delete', 'mark', 'schedule'].includes(intent)
        };
    }

    /**
     * Get command suggestions based on current input
     */
    getCommandSuggestions(text) {
        const commands = [
            'add task',
            'add note',
            'add mission',
            'schedule meeting',
            'what\'s next?',
            'show inbox',
            'show missions',
            'what\'s due today?',
            'what\'s overdue?',
            'mark done',
            'clear inbox',
            'mission status'
        ];

        const query = text.toLowerCase().trim();
        if (!query) return commands.slice(0, 5);

        return commands.filter(cmd => cmd.toLowerCase().includes(query));
    }

    /**
     * Clear all state
     */
    reset() {
        this.historyIndex = -1;
        this.suggestedItems = [];
        this.selectedSuggestionIndex = -1;
        this.isAwaitingAutocomplete = false;
    }
}

// Export for use
window.AgentInputController = AgentInputController;
