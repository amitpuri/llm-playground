/**
 * Modular Main Application Entry Point
 * Uses component-based architecture for better maintainability
 */

// Global utility functions
const $ = sel => document.querySelector(sel);
const $$ = sel => [...document.querySelectorAll(sel)];

// Main application instance
let app = null;

/**
 * Simple tab functionality that works immediately
 */
function initializeBasicTabs() {
    console.log('Initializing basic tab functionality...');
    
    document.querySelectorAll('.tab').forEach(button => {
        button.addEventListener('click', () => {
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('tab-active');
            });
            
            // Add active class to clicked tab
            button.classList.add('tab-active');
            
            // Show/hide tab content
            const tabName = button.dataset.tab;
            const tabNames = ['chat', 'debug', 'settings', 'templates', 'tokens'];
            
            tabNames.forEach(name => {
                const tabContent = document.getElementById(`tab-${name}`);
                if (tabContent) {
                    tabContent.classList.toggle('hidden', name !== tabName);
                }
            });
            
            console.log(`Switched to ${tabName} tab`);
        });
    });
    
    // Don't set default tab here - let the app handle it
    console.log('Basic tab functionality initialized (no default tab set)');
}

/**
 * Initialize the application when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', async () => {
    console.log('DOM loaded, initializing modular application...');
    
    // Immediately set chat tab as active and show chat content
    console.log('Setting initial chat tab state...');
    const chatTab = document.querySelector('.tab[data-tab="chat"]');
    if (chatTab) {
        chatTab.classList.add('tab-active');
    }
    
    // Show chat content and hide others
    const tabNames = ['chat', 'debug', 'settings', 'templates', 'tokens'];
    tabNames.forEach(name => {
        const tabContent = document.getElementById(`tab-${name}`);
        if (tabContent) {
            tabContent.classList.toggle('hidden', name !== 'chat');
        }
    });
    console.log('Initial chat tab state set');
    
    // Initialize basic tab functionality immediately
    initializeBasicTabs();
    
    try {
        // Check if required classes are available
        if (typeof App === 'undefined') {
            throw new Error('App class not found. Check if App.js is loaded.');
        }
        if (typeof SettingsManager === 'undefined') {
            throw new Error('SettingsManager class not found. Check if SettingsManager.js is loaded.');
        }
        if (typeof ChatManager === 'undefined') {
            throw new Error('ChatManager class not found. Check if ChatManager.js is loaded.');
        }
        if (typeof TemplateManager === 'undefined') {
            throw new Error('TemplateManager class not found. Check if TemplateManager.js is loaded.');
        }
        if (typeof DebugManager === 'undefined') {
            throw new Error('DebugManager class not found. Check if DebugManager.js is loaded.');
        }
        if (typeof TokenCalculator === 'undefined') {
            throw new Error('TokenCalculator class not found. Check if TokenCalculator.js is loaded.');
        }
        
        console.log('All required classes found, creating app instance...');
        
        // Create and initialize the main app
        app = new App();
        
        console.log('App instance created, initializing...');
        
        // Initialize the application
        await app.init();
        
        console.log('Modular application initialized successfully');
        
        // Force update MCP selected display
        if (app.settingsManager) {
            app.settingsManager.renderMcpSelected();
        }
        
    } catch (error) {
        console.error('Failed to initialize modular application:', error);
        
        // Show error in MCP selected area
        const mcpSelected = document.getElementById('mcpSelected');
        if (mcpSelected) {
            mcpSelected.innerHTML = '<span class="text-red-500 text-sm">Error loading settings</span>';
        }
        
        // Fallback: try to load settings directly
        try {
            console.log('Attempting fallback settings load...');
            const response = await fetch('/api/settings');
            if (response.ok) {
                const settings = await response.json();
                console.log('Settings loaded via fallback:', settings);
                
                // Update MCP display manually
                const wrapper = document.getElementById('mcpSelected');
                if (wrapper) {
                    const mcp = settings?.mcp || {};
                    const pills = [];
                    
                    if (mcp.github?.enabled) {
                        const label = mcp.github.repo ? `GitHub Issues (${mcp.github.repo})` : 'GitHub Issues';
                        pills.push(label);
                    }
                    
                    if (mcp.postgres?.enabled) {
                        pills.push('PostgreSQL');
                    }
                    
                    if (pills.length > 0) {
                        wrapper.innerHTML = pills.map(pill => 
                            `<span class="pill">${pill}</span>`
                        ).join(' ');
                    } else {
                        wrapper.innerHTML = '<span class="text-slate-500 text-sm">No connectors enabled</span>';
                    }
                }
            }
        } catch (fallbackError) {
            console.error('Fallback settings load also failed:', fallbackError);
        }
    }
});

/**
 * Legacy compatibility functions for backward compatibility
 */
function logDebug(section, obj) {
    if (app) {
        app.logDebug(section, obj);
    }
}

function activateTab(name) {
    if (app) {
        app.activateTab(name);
    } else {
        // Fallback tab activation
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('tab-active');
        });
        
        const targetTab = document.querySelector(`.tab[data-tab="${name}"]`);
        if (targetTab) {
            targetTab.classList.add('tab-active');
        }
        
        const tabNames = ['chat', 'debug', 'settings', 'templates'];
        tabNames.forEach(tabName => {
            const tabContent = document.getElementById(`tab-${tabName}`);
            if (tabContent) {
                tabContent.classList.toggle('hidden', tabName !== name);
            }
        });
    }
}

function renderDebug(debug) {
    if (app && app.debugManager) {
        app.debugManager.renderDebug(debug);
    }
}

// Export for global access if needed
window.app = app;
window.logDebug = logDebug;
window.activateTab = activateTab;
window.renderDebug = renderDebug;
