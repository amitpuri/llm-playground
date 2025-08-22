/**
 * Core Application Module
 * Manages the main application state and initialization
 */
class App {
    constructor() {
        this.settings = null;
        this.debug = [];
        
        // Initialize managers immediately
        this.settingsManager = new SettingsManager();
        this.chatManager = new ChatManager();
        this.templateManager = new TemplateManager();
        this.debugManager = new DebugManager();
        this.tokenCalculator = new TokenCalculator();
    }

    /**
     * Set app reference for all managers
     */
    async setManagerReferences() {
        this.settingsManager.setApp(this);
        await this.chatManager.setApp(this);
        this.templateManager.setApp(this);
        this.debugManager.setApp(this);
        // TokenCalculator doesn't need app reference as it's self-contained
    }

    /**
     * Initialize the application
     */
    async init() {
        try {
            console.log('[App] Starting application initialization...');
            
            // Add initialization log
            this.debugManager.addLog('info', 'Application initialization started');
            
            // Load settings FIRST
            console.log('[App] Loading settings...');
            await this.settingsManager.loadSettings();
            this.settings = this.settingsManager.getSettings();
            
            this.debugManager.addLog('info', 'Settings loaded successfully', {
                providers: Object.keys(this.settings.providers || {}),
                mcp_connectors: Object.keys(this.settings.mcp || {}),
                default_provider: this.settings.default_provider
            });

            // Set manager references AFTER settings are loaded
            await this.setManagerReferences();
            
            // Initialize TokenCalculator
            console.log('[App] Initializing TokenCalculator...');
            await this.tokenCalculator.init();
            
            // Initialize UI components
            console.log('[App] Initializing UI components...');
            this.initializeUI();
            
            // Now populate provider dropdowns with loaded settings
            if (this.chatManager) {
                this.chatManager.populateProviderDropdowns();
            }
            
            // IMPORTANT: Set initial tab AFTER all initialization is complete
            // Add a small delay to ensure everything is ready
            setTimeout(() => {
                console.log('[App] Setting initial tab to chat...');
                this.activateTab('chat');
                
                // Set focus to user prompt textarea
                console.log('[App] Setting focus to user prompt...');
                this.setFocusToUserPrompt();
            }, 100);
            
            this.debugManager.addLog('info', 'Application initialized successfully');
            console.log('[App] Application initialization completed successfully');
        } catch (error) {
            this.debugManager.addLog('error', 'Failed to initialize app', { error: error.message });
            console.error('[App] Failed to initialize app:', error);
        }
    }

    /**
     * Set focus to the user prompt textarea
     */
    setFocusToUserPrompt() {
        const userPromptTextarea = document.getElementById('userPrompt');
        if (userPromptTextarea) {
            userPromptTextarea.focus();
            this.debugManager.addLog('info', 'Focus set to user prompt textarea');
        }
    }

    /**
     * Initialize UI event listeners and components
     */
    initializeUI() {
        // Tab navigation
        document.querySelectorAll('.tab').forEach(button => {
            button.addEventListener('click', () => {
                this.activateTab(button.dataset.tab);
            });
        });

        // Settings form
        const settingsForm = document.getElementById('settingsForm');
        if (settingsForm) {
            settingsForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.settingsManager.saveSettingsFromForm(e);
            });
        }

        // Chat buttons
        const optimizeBtn = document.getElementById('btnOptimize');
        if (optimizeBtn) {
            optimizeBtn.addEventListener('click', () => this.chatManager.optimize());
        }

        const sendBtn = document.getElementById('btnSend');
        if (sendBtn) {
            sendBtn.addEventListener('click', () => this.chatManager.send());
        }

        // Template UI
        this.templateManager.bindPromptTemplateUI();

        // Example buttons
        this.bindExampleButtons();
    }

    /**
     * Activate a specific tab
     */
    activateTab(name) {
        console.log(`[App] Activating tab: ${name}`);
        
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(button => {
            button.classList.remove('tab-active');
        });
        
        const activeTab = document.querySelector(`.tab[data-tab="${name}"]`);
        if (activeTab) {
            activeTab.classList.add('tab-active');
            console.log(`[App] Tab button activated: ${name}`);
        } else {
            console.warn(`[App] Tab button not found: ${name}`);
        }

        // Show/hide tab content
        const tabNames = ['chat', 'debug', 'settings', 'templates', 'tokens'];
        tabNames.forEach(tabName => {
            const tabContent = document.getElementById(`tab-${tabName}`);
            if (tabContent) {
                const shouldShow = tabName === name;
                tabContent.classList.toggle('hidden', !shouldShow);
                console.log(`[App] Tab content ${tabName}: ${shouldShow ? 'shown' : 'hidden'}`);
            } else {
                console.warn(`[App] Tab content not found: tab-${tabName}`);
            }
        });

        // Show current settings when debug tab is activated
        if (name === 'debug' && this.debugManager) {
            this.debugManager.showCurrentSettings();
        }
        
        // Set focus to user prompt when chat tab is activated
        if (name === 'chat') {
            console.log(`[App] Setting focus to user prompt for chat tab`);
            this.setFocusToUserPrompt();
            
            // Update context window info when chat tab is activated
            if (this.chatManager) {
                setTimeout(async () => {
                    await this.chatManager.updateContextWindowInfo();
                }, 50);
            }
        }
        
        // Ensure token calculator is ready when tokens tab is activated
        if (name === 'tokens' && this.tokenCalculator) {
            console.log(`[App] Tokens tab activated, ensuring token calculator is ready`);
            // The token calculator should already be initialized, just ensure dropdowns are populated
            setTimeout(() => {
                if (this.tokenCalculator.isReady()) {
                    console.log(`[App] TokenCalculator is ready, refreshing dropdowns`);
                    this.tokenCalculator.refreshDropdowns();
                } else {
                    console.warn(`[App] TokenCalculator not ready yet, attempting to initialize`);
                    this.tokenCalculator.init();
                }
            }, 100);
        }
        
        console.log(`[App] Tab activation complete: ${name}`);
    }

    /**
     * Bind example workflow buttons
     */
    bindExampleButtons() {
        const examples = [
            {
                id: 'btnExample1',
                text: `I need to build a recommendation system for e-commerce. What research papers and GitHub issues are relevant to this project? Please provide:
1. Key research papers on recommendation systems
2. Relevant GitHub issues that might inform the implementation
3. Implementation guidance based on the research findings`
            },
            {
                id: 'btnExample2',
                text: `Extract project requirements from GitHub issues and match them with relevant AI research papers. Focus on:
1. Technical specifications and implementation needs
2. Research papers that address similar requirements
3. Gap analysis between requirements and available research`
            },
            {
                id: 'btnExample3',
                text: `Based on the GitHub issues and research papers, provide implementation guidance for building an AI-powered system. Include:
1. Recommended approaches from research papers
2. Technical architecture suggestions
3. Potential challenges and solutions`
            }
        ];

        examples.forEach(example => {
            const button = document.getElementById(example.id);
            if (button) {
                button.addEventListener('click', () => {
                    const userPrompt = document.getElementById('userPrompt');
                    if (userPrompt) {
                        userPrompt.value = example.text;
                    }
                });
            }
        });
    }

    /**
     * Log debug information
     */
    logDebug(section, obj) {
        if (this.debugManager) {
            this.debugManager.addLog('debug', `${section}: ${JSON.stringify(obj, null, 2)}`);
        }
        console.log(`[DEBUG] ${section}:`, obj);
    }

    /**
     * Get current settings
     */
    getSettings() {
        return this.settings;
    }

    /**
     * Get debug information
     */
    getDebug() {
        return this.debug;
    }
}

// Export for use in other modules
window.App = App;
