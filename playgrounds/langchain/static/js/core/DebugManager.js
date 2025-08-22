/**
 * Debug Manager Module
 * Handles debug information display and logging
 */
class DebugManager {
    constructor() {
        this.app = null;
        this.logs = [];
        this.maxLogs = 1000; // Keep last 1000 logs
        this.sessionId = null;
        this.logRefreshInterval = null;
    }

    /**
     * Set reference to main app instance
     */
    setApp(app) {
        this.app = app;
        this.initializeDebugTabs();
        this.initializeLogFetching();
    }

    /**
     * Initialize debug tab functionality
     */
    initializeDebugTabs() {
        const infoTab = document.getElementById('debug-info-tab');
        const logsTab = document.getElementById('debug-logs-tab');
        const clearLogsBtn = document.getElementById('clear-logs');
        const debugTokenCalculatorBtn = document.getElementById('debug-token-calculator');

        if (infoTab) {
            infoTab.addEventListener('click', () => this.switchDebugTab('info'));
        }

        if (logsTab) {
            logsTab.addEventListener('click', () => this.switchDebugTab('logs'));
        }

        if (clearLogsBtn) {
            clearLogsBtn.addEventListener('click', () => this.clearLogs());
        }

        if (debugTokenCalculatorBtn) {
            debugTokenCalculatorBtn.addEventListener('click', () => this.debugTokenCalculator());
        }
    }

    /**
     * Switch between debug tabs
     */
    switchDebugTab(tabName) {
        const infoTab = document.getElementById('debug-info-tab');
        const logsTab = document.getElementById('debug-logs-tab');
        const infoContent = document.getElementById('debug-info-content');
        const logsContent = document.getElementById('debug-logs-content');

        if (tabName === 'info') {
            infoTab?.classList.add('debug-subtab-active', 'border-blue-500', 'text-blue-600');
            infoTab?.classList.remove('border-transparent', 'text-gray-500');
            logsTab?.classList.remove('debug-subtab-active', 'border-blue-500', 'text-blue-600');
            logsTab?.classList.add('border-transparent', 'text-gray-500');
            infoContent?.classList.remove('hidden');
            logsContent?.classList.add('hidden');
        } else {
            logsTab?.classList.add('debug-subtab-active', 'border-blue-500', 'text-blue-600');
            logsTab?.classList.remove('border-transparent', 'text-gray-500');
            infoTab?.classList.remove('debug-subtab-active', 'border-blue-500', 'text-blue-600');
            infoTab?.classList.add('border-transparent', 'text-gray-500');
            logsContent?.classList.remove('hidden');
            infoContent?.classList.add('hidden');
        }
    }

    /**
     * Add a log entry
     */
    addLog(level, message, data = null) {
        const timestamp = new Date().toISOString();
        const logEntry = {
            timestamp,
            level,
            message,
            data
        };

        this.logs.push(logEntry);

        // Keep only the last maxLogs entries
        if (this.logs.length > this.maxLogs) {
            this.logs = this.logs.slice(-this.maxLogs);
        }

        this.updateLogsDisplay();
    }

    /**
     * Clear all logs
     */
    clearLogs() {
        this.logs = [];
        this.updateLogsDisplay();
        
        // Also clear server-side logs
        if (this.sessionId) {
            fetch(`/api/logs/clear/${this.sessionId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            }).then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.addLog('info', 'Server logs cleared');
                }
            }).catch(error => {
                this.addLog('error', 'Failed to clear server logs', error);
            });
        }
    }

    /**
     * Update logs display
     */
    updateLogsDisplay() {
        const logsElement = document.getElementById('debug-logs');
        if (!logsElement) return;

        if (this.logs.length === 0) {
            logsElement.innerHTML = '<pre class="text-xs text-gray-700 whitespace-pre-wrap">No logs yet...</pre>';
            return;
        }

        const logText = this.logs.map(log => {
            const time = new Date(log.timestamp).toLocaleTimeString();
            const levelColor = {
                'info': 'text-blue-600',
                'warn': 'text-yellow-600',
                'error': 'text-red-600',
                'debug': 'text-gray-600'
            }[log.level] || 'text-gray-600';

            let logLine = `[${time}] [${log.level.toUpperCase()}] ${log.message}`;
            
            if (log.data) {
                if (typeof log.data === 'object') {
                    logLine += '\n' + JSON.stringify(log.data, null, 2);
                } else {
                    logLine += ` - ${log.data}`;
                }
            }
            
            return logLine;
        }).join('\n\n');

        logsElement.innerHTML = `<pre class="text-xs text-gray-700 whitespace-pre-wrap">${this.htmlEscape(logText)}</pre>`;
        
        // Auto-scroll to bottom
        logsElement.scrollTop = logsElement.scrollHeight;
    }

    /**
     * Show current settings in debug panel
     */
    showCurrentSettings() {
        if (!this.app || !this.app.settings) return;
        
        const settings = this.app.settings;
        
        // Find the first enabled provider
        let enabledProvider = null;
        for (const [key, provider] of Object.entries(settings.providers || {})) {
            if (provider.enabled) {
                enabledProvider = { key, ...provider };
                break;
            }
        }
        
        const debugInfo = {
            provider: {
                name: enabledProvider ? enabledProvider.name : 'No provider enabled',
                model: enabledProvider ? enabledProvider.default_model : 'Not configured',
                endpoint: enabledProvider ? enabledProvider.base_url : 'Not configured',
                temperature: enabledProvider ? enabledProvider.temperature : 'Not configured'
            },
            mcp: {
                github: {
                    enabled: settings.mcp?.github?.enabled || false,
                    repo: settings.mcp?.github?.repo || 'Not configured',
                    url: settings.mcp?.github?.url || 'Not configured',
                    tools: ['GitHub Issues', 'GitHub Comments'],
                    calls: []
                },
                postgres: {
                    enabled: settings.mcp?.postgres?.enabled || false,
                    sql: settings.mcp?.postgres?.sample_sql || 'Not configured',
                    url: settings.mcp?.postgres?.url || 'Not configured',
                    tools: ['PostgreSQL Queries', 'Research Papers'],
                    calls: []
                }
            },
            optimizer: {
                provider: settings.optimizer?.provider || 'Not configured',
                model: settings.optimizer?.model || 'Not configured',
                temperature: settings.optimizer?.temperature || 0.2
            }
        };
        
        this.renderDebug(debugInfo);
        
        // Add initial logs
        this.addLog('info', 'Debug panel initialized');
        this.addLog('info', 'Current settings loaded', {
            provider: enabledProvider ? enabledProvider.name : 'None',
            github_enabled: settings.mcp?.github?.enabled || false,
            postgres_enabled: settings.mcp?.postgres?.enabled || false
        });
    }

    /**
     * Update debug log display
     */
    updateDebugLog(debugData) {
        const legacyLog = document.getElementById('debugLog');
        if (legacyLog) {
            legacyLog.textContent = JSON.stringify(debugData, null, 2);
        }
    }

    /**
     * Render debug information
     */
    renderDebug(debug) {
        const element = this.getDebugElement();
        if (!element) return;

        if (!debug) {
            element.innerHTML = '<em>No debug information available</em>';
            return;
        }

        const provider = debug.provider || {};
        const github = (debug.mcp && debug.mcp.github) || {};
        const postgres = (debug.mcp && debug.mcp.postgres) || {};
        const optimizer = debug.optimizer || {};

        element.innerHTML = `
            <section>
                <h3>Provider</h3>
                <div><strong>Name:</strong> ${this.htmlEscape(provider.name || 'Not configured')}</div>
                <div><strong>Model:</strong> ${this.htmlEscape(provider.model || 'Not configured')}</div>
                <div><strong>Endpoint:</strong> ${this.htmlEscape(provider.endpoint || 'Not configured')}</div>
                <div><strong>Temperature:</strong> ${this.htmlEscape(String(provider.temperature ?? 'Not configured'))}</div>
                ${provider.error ? `<div class="err"><strong>Error:</strong> ${this.htmlEscape(provider.error)}</div>` : ''}
                
                ${provider.request ? `
                <h4>Request</h4>
                <pre class="small-pre">System (preview):\n${this.htmlEscape(provider.request.system_preview || 'Not available')}</pre>
                <pre class="small-pre">Prompt (preview):\n${this.htmlEscape(provider.request.prompt_preview || 'Not available')}</pre>
                <div><strong>Temperature:</strong> ${this.htmlEscape(String(provider.request.temperature ?? 'Not available'))}</div>
                ` : ''}
                
                ${provider.response ? `
                <h4>Response</h4>
                <pre class="small-pre">${this.htmlEscape(provider.response.raw_preview || 'Not available')}</pre>
                ` : ''}
                
                ${provider.parsed ? `
                <h4>Parsed</h4>
                <pre class="small-pre">${this.htmlEscape(provider.parsed.structured_preview || 'Not available')}</pre>
                ` : ''}
            </section>

            <hr/>

            <section>
                <h3>MCP — GitHub</h3>
                <div><strong>Enabled:</strong> ${github.enabled ? '✅ Yes' : '❌ No'}</div>
                ${github.repo ? `<div><strong>Repository:</strong> ${this.htmlEscape(github.repo)}</div>` : ''}
                ${github.url ? `<div><strong>URL:</strong> ${this.htmlEscape(github.url)}</div>` : ''}
                ${github && github.error ? `<div class="err"><strong>Error:</strong> ${this.htmlEscape(github.error)}</div>` : ''}
                <div><strong>Tools:</strong> <code>${this.htmlEscape(JSON.stringify(github.tools || []))}</code></div>
                ${this.renderCallTable(github.calls)}
            </section>

            <hr/>

            <section>
                <h3>MCP — Postgres</h3>
                <div><strong>Enabled:</strong> ${postgres.enabled ? '✅ Yes' : '❌ No'}</div>
                ${postgres.url ? `<div><strong>URL:</strong> ${this.htmlEscape(postgres.url)}</div>` : ''}
                ${postgres.sql ? `<div><strong>Sample SQL:</strong> <code>${this.htmlEscape(postgres.sql)}</code></div>` : ''}
                ${postgres && postgres.error ? `<div class="err"><strong>Error:</strong> ${this.htmlEscape(postgres.error)}</div>` : ''}
                <div><strong>Tools:</strong> <code>${this.htmlEscape(JSON.stringify(postgres.tools || []))}</code></div>
                ${this.renderCallTable(postgres.calls)}
            </section>

            <hr/>

            <section>
                <h3>Optimizer</h3>
                <div><strong>Provider:</strong> ${this.htmlEscape(optimizer.provider || 'Not configured')}</div>
                <div><strong>Model:</strong> ${this.htmlEscape(optimizer.model || 'Not configured')}</div>
                <div><strong>Temperature:</strong> ${this.htmlEscape(String(optimizer.temperature ?? 'Not configured'))}</div>
                ${debug.final_prompt_tokens_est ? `<div><strong>Final prompt tokens (est):</strong> ${this.htmlEscape(String(debug.final_prompt_tokens_est))}</div>` : ''}
                ${debug.optimizer ? `<pre class="small-pre">${this.htmlEscape(JSON.stringify(debug.optimizer, null, 2))}</pre>` : ''}
            </section>
        `;
    }

    /**
     * Get debug element
     */
    getDebugElement() {
        return document.getElementById('debug-output') || document.getElementById('debugLog');
    }

    /**
     * Render call table
     */
    renderCallTable(calls = []) {
        if (!Array.isArray(calls) || !calls.length) {
            return '<em>No calls</em>';
        }

        const rows = calls.map(call => `
            <tr>
                <td>${this.htmlEscape(call.tool)}</td>
                <td><pre class="small-pre">${this.htmlEscape(JSON.stringify(call.input, null, 2))}</pre></td>
                <td>${call.ok ? '✅' : '❌'}</td>
                <td>${call.duration_ms ?? ''}</td>
                <td><pre class="small-pre">${this.htmlEscape(call.output_preview || call.error || '')}</pre></td>
            </tr>
        `).join('');

        return `
            <table class="debug-table">
                <thead>
                    <tr>
                        <th>Tool</th>
                        <th>Input</th>
                        <th>OK</th>
                        <th>ms</th>
                        <th>Output / Error (preview)</th>
                    </tr>
                </thead>
                <tbody>${rows}</tbody>
            </table>
        `;
    }

    /**
     * HTML escape helper
     */
    htmlEscape(text) {
        return String(text || "").replace(/[&<>"']/g, char => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;'
        }[char]));
    }

    /**
     * Initialize log fetching
     */
    initializeLogFetching() {
        // Get current session ID
        fetch('/api/logs/session-id')
            .then(response => response.json())
            .then(data => {
                this.sessionId = data.session_id;
                this.addLog('info', `Session initialized: ${this.sessionId}`);
                this.startLogRefresh();
            })
            .catch(error => {
                this.addLog('error', 'Failed to get session ID', error);
            });
    }

    /**
     * Start log refresh interval
     */
    startLogRefresh() {
        // Clear existing interval
        if (this.logRefreshInterval) {
            clearInterval(this.logRefreshInterval);
        }

        // Fetch logs immediately
        this.fetchServerLogs();

        // Set up interval to fetch logs every 2 seconds
        this.logRefreshInterval = setInterval(() => {
            this.fetchServerLogs();
        }, 2000);
    }

    /**
     * Stop log refresh interval
     */
    stopLogRefresh() {
        if (this.logRefreshInterval) {
            clearInterval(this.logRefreshInterval);
            this.logRefreshInterval = null;
        }
    }

    /**
     * Fetch logs from server
     */
    fetchServerLogs() {
        if (!this.sessionId) return;

        fetch(`/api/logs/current`)
            .then(response => response.json())
            .then(data => {
                if (data.logs && data.logs !== this.lastServerLogs) {
                    this.lastServerLogs = data.logs;
                    this.updateServerLogsDisplay(data.logs);
                }
            })
            .catch(error => {
                // Only log error once to avoid spam
                if (!this.logFetchErrorLogged) {
                    this.addLog('error', 'Failed to fetch server logs', error);
                    this.logFetchErrorLogged = true;
                }
            });
    }

    /**
     * Update server logs display
     */
    updateServerLogsDisplay(serverLogs) {
        const logsElement = document.getElementById('debug-logs');
        if (!logsElement) return;

        if (!serverLogs || serverLogs === 'No log file found for session ' + this.sessionId) {
            logsElement.innerHTML = '<pre class="text-xs text-gray-700 whitespace-pre-wrap">No server logs yet...</pre>';
            return;
        }

        // Format the server logs for display
        const formattedLogs = serverLogs
            .split('\n')
            .filter(line => line.trim()) // Remove empty lines
            .map(line => {
                // Add some basic formatting
                if (line.includes('[ERROR]')) {
                    return `<span class="text-red-600">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[WARNING]')) {
                    return `<span class="text-yellow-600">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[INFO]')) {
                    return `<span class="text-blue-600">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[DEBUG]')) {
                    return `<span class="text-gray-500">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[MCP]')) {
                    return `<span class="text-green-600">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[LLM]')) {
                    return `<span class="text-purple-600">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[OPTIMIZER]')) {
                    return `<span class="text-indigo-600">${this.htmlEscape(line)}</span>`;
                } else if (line.includes('[API]')) {
                    return `<span class="text-orange-600">${this.htmlEscape(line)}</span>`;
                }
                return this.htmlEscape(line);
            })
            .join('\n');

        logsElement.innerHTML = `<pre class="text-xs text-gray-700 whitespace-pre-wrap">${formattedLogs}</pre>`;
        
        // Auto-scroll to bottom
        logsElement.scrollTop = logsElement.scrollHeight;
    }

    /**
     * Debug TokenCalculator functionality
     */
    debugTokenCalculator() {
        if (!this.app || !this.app.tokenCalculator) {
            this.addLog('error', 'TokenCalculator not available');
            return;
        }

        try {
            const debugInfo = this.app.tokenCalculator.getDebugInfo();
            const debugDiv = document.getElementById('token-calculator-debug');
            if (debugDiv) {
                debugDiv.innerHTML = '<pre>' + JSON.stringify(debugInfo, null, 2) + '</pre>';
            }
            
            this.addLog('info', 'TokenCalculator debug info retrieved', debugInfo);
        } catch (error) {
            this.addLog('error', 'Failed to get TokenCalculator debug info', { error: error.message });
        }
    }
}

// Export for use in other modules
window.DebugManager = DebugManager;
