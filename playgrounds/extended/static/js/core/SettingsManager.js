/**
 * Settings Manager Module
 * Handles loading, saving, and managing application settings
 */
class SettingsManager {
    constructor() {
        this.settings = null;
        this.app = null;
        this.modelOptions = {
            openai: ['gpt-5', 'gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
            anthropic: ['claude-opus-4-0', 'claude-sonnet-4-0', 'claude-haiku-3-0'],
            ollama: ['llama3.2', 'llama3.1', 'mistral', 'codellama'],
            google: ['gemini-pro', 'gemini-flash', 'gemini-nano']
        };
    }

    /**
     * Set reference to main app instance
     */
    setApp(app) {
        this.app = app;
    }

    /**
     * Load settings from the server
     */
    async loadSettings() {
        try {
            const response = await fetch('/api/settings');
            this.settings = await response.json();
            
            // Debug logging
            console.log('Settings loaded from server:', this.settings);
            console.log('Anthropic enabled:', this.settings?.providers?.anthropic?.enabled);
            console.log('GitHub enabled:', this.settings?.mcp?.github?.enabled);
            console.log('Postgres enabled:', this.settings?.mcp?.postgres?.enabled);
            
            // Update UI with loaded settings
            this.fillSettingsFormFromSettings();
            this.fillProviderDropdownFromSettings();
            this.renderMcpSelected();
            
            return this.settings;
        } catch (error) {
            console.error('Failed to load settings:', error);
            throw error;
        }
    }

    /**
     * Get current settings
     */
    getSettings() {
        return this.settings;
    }

    /**
     * Fill the settings form with current settings
     */
    fillSettingsFormFromSettings() {
        if (!this.settings) return;

        const providers = this.settings.providers || {};

        // OpenAI settings
        this.setFormValue('#openai_enabled', providers.openai?.enabled || false, 'checked');
        this.setFormValue('#openai_url', providers.openai?.base_url || '');
        this.setFormValue('#openai_key', providers.openai?.api_key || '');
        this.populateModelSelect('#openai_model', 'openai', providers.openai?.default_model);
        this.setFormValue('#openai_temp', providers.openai?.temperature || 0.2);
        this.setFormValue('#openai_cw', providers.openai?.context_window || 128000);

        // Anthropic settings
        this.setFormValue('#anthropic_enabled', providers.anthropic?.enabled || false, 'checked');
        this.setFormValue('#anthropic_url', providers.anthropic?.base_url || '');
        this.setFormValue('#anthropic_key', providers.anthropic?.api_key || '');
        this.populateModelSelect('#anthropic_model', 'anthropic', providers.anthropic?.default_model);
        this.setFormValue('#anthropic_temp', providers.anthropic?.temperature || 0.2);
        this.setFormValue('#anthropic_cw', providers.anthropic?.context_window || 200000);

        // Ollama settings
        this.setFormValue('#ollama_enabled', providers.ollama?.enabled || false, 'checked');
        this.setFormValue('#ollama_url', providers.ollama?.base_url || '');
        this.populateModelSelect('#ollama_model', 'ollama', providers.ollama?.default_model);
        this.setFormValue('#ollama_temp', providers.ollama?.temperature || 0.2);
        this.setFormValue('#ollama_cw', providers.ollama?.context_window || 8000);

        // Google settings
        this.setFormValue('#google_enabled', providers.google?.enabled || false, 'checked');
        this.setFormValue('#google_url', providers.google?.base_url || '');
        this.setFormValue('#google_key', providers.google?.api_key || '');
        this.populateModelSelect('#google_model', 'google', providers.google?.default_model);
        this.setFormValue('#google_temp', providers.google?.temperature || 0.2);
        this.setFormValue('#google_cw', providers.google?.context_window || 128000);

        // Optimizer settings
        const optimizer = this.settings.optimizer || { provider: 'anthropic', model: 'claude-4-sonnet', temperature: 0.2, max_tokens: 1000, max_context_usage: 0.8 };
        this.setOptimizerProviderRadio(optimizer.provider || 'anthropic');
        this.populateModelSelect('#opt_model', optimizer.provider || 'anthropic', optimizer.model || '');
        this.setFormValue('#opt_temp', optimizer.temperature ?? 0.2);
        
        // Default provider settings
        const defaultProvider = this.settings.default_provider || 'anthropic';
        this.setDefaultProviderRadio(defaultProvider);
        this.setFormValue('#opt_max_tokens', optimizer.max_tokens ?? 1000);
        this.setFormValue('#opt_max_context', (optimizer.max_context_usage ?? 0.8) * 100); // Convert to percentage

        this.wireOptimizerRadio();
        this.wireDefaultProviderRadio();

        // MCP settings
        const github = this.settings.mcp?.github || {};
        this.setFormValue('#gh_enabled', github.enabled || false, 'checked');
        this.setFormValue('#gh_url', github.url || '');
        this.setFormValue('#gh_token', github.auth_token || '');
        this.setFormValue('#gh_repo', github.repo || '');

        const postgres = this.settings.mcp?.postgres || {};
        this.setFormValue('#pg_enabled', postgres.enabled || false, 'checked');
        this.setFormValue('#pg_url', postgres.url || '');
        this.setFormValue('#pg_token', postgres.auth_token || '');
        this.setFormValue('#pg_sql', postgres.sample_sql || '');
    }

    /**
     * Fill provider dropdown from settings
     */
    fillProviderDropdownFromSettings() {
        console.log('Filling provider dropdown from settings:', this.settings);
        
        const providerSelect = document.getElementById('provider');
        const modelSelect = document.getElementById('model');
        
        if (!providerSelect || !modelSelect) {
            console.error('Provider or model select elements not found');
            return;
        }

        providerSelect.innerHTML = '';
        const providers = this.settings?.providers || {};
        
        console.log('Available providers:', providers);

        Object.entries(providers).forEach(([key, provider]) => {
            console.log(`Provider ${key}:`, provider);
            if (provider.enabled) {
                const option = document.createElement('option');
                option.value = key;
                option.textContent = `${provider.name} (${key})`;
                providerSelect.appendChild(option);
                console.log(`Added provider option: ${key}`);
            }
        });

        // Set default provider from settings
        let chosen = this.settings?.default_provider || 'anthropic';
        
        // Validate that the default provider is enabled and available
        if (!(providers[chosen] && providers[chosen].enabled)) {
            // Fallback to first available enabled provider
            const first = providerSelect.options[0];
            chosen = first ? first.value : 'anthropic';
        }
        
        providerSelect.value = chosen;
        console.log('Chosen provider:', chosen);

        const defaultModel = providers[chosen]?.default_model || '';
        this.populateModelSelect(modelSelect, chosen, defaultModel);

        // Add change listener
        providerSelect.addEventListener('change', () => {
            const key = providerSelect.value;
            const defModel = providers[key]?.default_model || '';
            this.populateModelSelect(modelSelect, key, defModel);
        });
    }

    /**
     * Populate model select dropdown
     */
    populateModelSelect(selectElement, providerKey, defaultValue) {
        console.log(`Populating model select for provider: ${providerKey}, default: ${defaultValue}`);
        
        if (typeof selectElement === 'string') {
            selectElement = document.querySelector(selectElement);
        }
        
        if (!selectElement) {
            console.error('Model select element not found');
            return;
        }

        selectElement.innerHTML = '';
        const options = this.modelOptions[providerKey] || [];
        
        console.log(`Available models for ${providerKey}:`, options);

        options.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            selectElement.appendChild(option);
            console.log(`Added model option: ${model}`);
        });

        if (defaultValue && !options.includes(defaultValue)) {
            const option = document.createElement('option');
            option.value = defaultValue;
            option.textContent = defaultValue;
            selectElement.appendChild(option);
            console.log(`Added default model option: ${defaultValue}`);
        }

        selectElement.value = defaultValue || options[0] || '';
        console.log(`Set model select value to: ${selectElement.value}`);
    }

    /**
     * Set optimizer provider radio button
     */
    setOptimizerProviderRadio(value) {
        const radioMap = {
            openai: '#opt_openai',
            anthropic: '#opt_anthropic',
            ollama: '#opt_ollama',
            google: '#opt_google'
        };

        Object.values(radioMap).forEach(selector => {
            const element = document.querySelector(selector);
            if (element) element.checked = false;
        });

        const selector = radioMap[value] || '#opt_anthropic';
        const element = document.querySelector(selector);
        if (element) element.checked = true;
    }

    /**
     * Get optimizer provider radio value
     */
    getOptimizerProviderRadio() {
        const checked = document.querySelector('input[name="opt_provider"]:checked');
        return checked ? checked.value : 'anthropic';
    }
    
    /**
     * Set default provider radio button
     */
    setDefaultProviderRadio(value) {
        const radioMap = {
            openai: '#default_openai',
            anthropic: '#default_anthropic',
            ollama: '#default_ollama',
            google: '#default_google'
        };

        Object.values(radioMap).forEach(selector => {
            const element = document.querySelector(selector);
            if (element) element.checked = false;
        });

        const selector = radioMap[value] || '#default_anthropic';
        const element = document.querySelector(selector);
        if (element) element.checked = true;
    }
    
    /**
     * Get default provider radio value
     */
    getDefaultProviderRadio() {
        const checked = document.querySelector('input[name="default_provider"]:checked');
        return checked ? checked.value : 'anthropic';
    }

    /**
     * Wire optimizer radio buttons
     */
    wireOptimizerRadio() {
        document.querySelectorAll('input[name="opt_provider"]').forEach(radio => {
            radio.addEventListener('change', () => {
                const key = this.getOptimizerProviderRadio();
                const defModel = this.settings?.providers[key]?.default_model || 
                               (this.modelOptions[key]?.[0] || '');
                const defTemp = this.settings?.providers[key]?.temperature || 0.2;
                
                this.populateModelSelect('#opt_model', key, defModel);
                this.setFormValue('#opt_temp', defTemp);
                
                // Ensure the default model is selected
                const modelSelect = document.querySelector('#opt_model');
                if (modelSelect && defModel) {
                    modelSelect.value = defModel;
                }
            });
        });
    }
    
    /**
     * Wire default provider radio buttons
     */
    wireDefaultProviderRadio() {
        document.querySelectorAll('input[name="default_provider"]').forEach(radio => {
            radio.addEventListener('change', () => {
                // Update the default provider setting
                const defaultProvider = this.getDefaultProviderRadio();
                console.log('Default provider changed to:', defaultProvider);
            });
        });
    }

    /**
     * Render MCP selected indicators
     */
    renderMcpSelected() {
        const wrapper = document.getElementById('mcpSelected');
        if (!wrapper) return;

        wrapper.innerHTML = '';
        const mcp = this.settings?.mcp || {};
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
                `<span class="pill">${this.htmlEscape(pill)}</span>`
            ).join(' ');
        } else {
            wrapper.innerHTML = '<span class="text-slate-500 text-sm">No connectors enabled</span>';
        }
    }

    /**
     * Save settings from form
     */
    async saveSettingsFromForm(event) {
        event.preventDefault();
        
        const optProvider = this.getOptimizerProviderRadio();
        const payload = {
            providers: {
                openai: {
                    enabled: this.getFormValue('#openai_enabled', 'checked'),
                    name: 'OpenAI',
                    base_url: this.getFormValue('#openai_url'),
                    api_key: this.getFormValue('#openai_key'),
                    default_model: this.getFormValue('#openai_model'),
                    temperature: parseFloat(this.getFormValue('#openai_temp') || '0.2'),
                    context_window: parseInt(this.getFormValue('#openai_cw') || '128000', 10),
                },
                anthropic: {
                    enabled: this.getFormValue('#anthropic_enabled', 'checked'),
                    name: 'Anthropic',
                    base_url: this.getFormValue('#anthropic_url'),
                    api_key: this.getFormValue('#anthropic_key'),
                    default_model: this.getFormValue('#anthropic_model'),
                    temperature: parseFloat(this.getFormValue('#anthropic_temp') || '0.2'),
                    context_window: parseInt(this.getFormValue('#anthropic_cw') || '200000', 10),
                },
                ollama: {
                    enabled: this.getFormValue('#ollama_enabled', 'checked'),
                    name: 'Ollama',
                    base_url: this.getFormValue('#ollama_url'),
                    api_key: '',
                    default_model: this.getFormValue('#ollama_model'),
                    temperature: parseFloat(this.getFormValue('#ollama_temp') || '0.2'),
                    context_window: parseInt(this.getFormValue('#ollama_cw') || '8000', 10),
                },
                google: {
                    enabled: this.getFormValue('#google_enabled', 'checked'),
                    name: 'Google',
                    base_url: this.getFormValue('#google_url'),
                    api_key: this.getFormValue('#google_key'),
                    default_model: this.getFormValue('#google_model'),
                    temperature: parseFloat(this.getFormValue('#google_temp') || '0.2'),
                    context_window: parseInt(this.getFormValue('#google_cw') || '128000', 10),
                },
            },
            optimizer: {
                provider: optProvider,
                model: this.getFormValue('#opt_model'),
                temperature: parseFloat(this.getFormValue('#opt_temp') || '0.2'),
                max_tokens: parseInt(this.getFormValue('#opt_max_tokens') || '1000', 10),
                max_context_usage: parseFloat(this.getFormValue('#opt_max_context') || '80') / 100, // Convert percentage to decimal
            },
            default_provider: this.getDefaultProviderRadio(),
            mcp: {
                github: {
                    enabled: this.getFormValue('#gh_enabled', 'checked'),
                    url: this.getFormValue('#gh_url'),
                    auth_token: this.getFormValue('#gh_token'),
                    repo: this.getFormValue('#gh_repo'),
                },
                postgres: {
                    enabled: this.getFormValue('#pg_enabled', 'checked'),
                    url: this.getFormValue('#pg_url'),
                    auth_token: this.getFormValue('#pg_token'),
                    sample_sql: this.getFormValue('#pg_sql'),
                }
            }
        };

        try {
            const response = await fetch('/api/settings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            const result = await response.json();
            console.log('Settings saved:', result);
            
            // Reload settings
            await this.loadSettings();
            
            // Trigger callback to refresh chat dropdowns
            if (this.app && this.app.chatManager) {
                this.app.chatManager.refreshProviderDropdowns();
            }
            
            alert('Settings saved');
        } catch (error) {
            console.error('Failed to save settings:', error);
            alert('Failed to save settings');
        }
    }

    /**
     * Helper method to set form value
     */
    setFormValue(selector, value, property = 'value') {
        const element = document.querySelector(selector);
        if (element) {
            if (property === 'checked') {
                element.checked = value;
            } else {
                element.value = value;
            }
        }
    }

    /**
     * Helper method to get form value
     */
    getFormValue(selector, property = 'value') {
        const element = document.querySelector(selector);
        if (element) {
            if (property === 'checked') {
                return element.checked;
            } else {
                return element.value;
            }
        }
        return '';
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
}

// Export for use in other modules
window.SettingsManager = SettingsManager;
