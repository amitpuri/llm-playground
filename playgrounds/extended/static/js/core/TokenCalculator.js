/**
 * Token Calculator Manager
 * Handles token counting and analysis for different AI providers
 */
class TokenCalculator {
    constructor() {
        this.currentProvider = 'anthropic';
        this.currentModel = 'claude-3-5-sonnet';
        this.providerModels = {};
        this.settings = null;
        // Don't call init() here - it will be called by the App
    }

    async init() {
        try {
            console.log('[TokenCalculator] Starting initialization...');
            this.bindEvents();
            await this.loadSettings();
            await this.loadProviderModels();
            this.updateModelOptions();
            console.log('[TokenCalculator] Initialization completed successfully');
        } catch (error) {
            console.error('[TokenCalculator] Initialization failed:', error);
            // Continue with fallback settings
        }
    }

    bindEvents() {
        // Provider selection change
        document.getElementById('token-provider')?.addEventListener('change', (e) => {
            this.currentProvider = e.target.value;
            this.updateModelDropdown('token-model', this.currentProvider);
        });

        // Model selection change
        document.getElementById('token-model')?.addEventListener('change', (e) => {
            this.currentModel = e.target.value;
        });

        // Count tokens button
        document.getElementById('count-tokens-btn')?.addEventListener('click', () => {
            this.countTokens();
        });

        // Analyze all providers button
        document.getElementById('analyze-text-btn')?.addEventListener('click', () => {
            this.analyzeAllProviders();
        });

        // Cost estimation
        document.getElementById('estimate-cost-btn')?.addEventListener('click', () => {
            this.estimateCost();
        });

        // Use current tokens button
        document.getElementById('use-current-tokens-btn')?.addEventListener('click', () => {
            this.useCurrentTokens();
        });

        // Cost provider change
        document.getElementById('cost-provider')?.addEventListener('change', (e) => {
            this.updateModelDropdown('cost-model', e.target.value);
        });

        // Real-time token counting on text input
        const textInput = document.getElementById('token-text-input');
        if (textInput) {
            let debounceTimer;
            textInput.addEventListener('input', () => {
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    this.updateCharacterCount();
                }, 500);
            });
        }
    }

    async loadSettings() {
        try {
            console.log('[TokenCalculator] Loading settings from /api/tokens/settings...');
            const response = await fetch('/api/tokens/settings');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            const data = await response.json();
            this.settings = data;
            
            console.log('[TokenCalculator] Settings loaded:', this.settings);
            
            // Set default provider from settings
            if (this.settings.default_provider) {
                this.currentProvider = this.settings.default_provider;
            }
            
            // Set default model from settings
            if (this.settings.providers[this.currentProvider]) {
                this.currentModel = this.settings.providers[this.currentProvider].default_model;
            }
            
            console.log('[TokenCalculator] Using provider:', this.currentProvider, 'model:', this.currentModel);
        } catch (error) {
            console.error('Failed to load token calculator settings:', error);
            // Fallback to default settings
            this.settings = {
                providers: {
                    'openai': { name: 'OpenAI', default_model: 'gpt-4', enabled: true },
                    'anthropic': { name: 'Anthropic', default_model: 'claude-3-5-sonnet', enabled: true },
                    'google': { name: 'Google', default_model: 'gemini-2.0-flash', enabled: true }
                },
                default_provider: 'anthropic'
            };
            console.log('[TokenCalculator] Using fallback settings:', this.settings);
        }
    }

    async loadProviderModels() {
        console.log('[TokenCalculator] Loading provider models...');
        
        // Only load models for enabled providers from settings
        const enabledProviders = Object.keys(this.settings.providers).filter(
            provider => this.settings.providers[provider].enabled
        );
        
        console.log('[TokenCalculator] Enabled providers:', enabledProviders);
        
        for (const provider of enabledProviders) {
            try {
                console.log(`[TokenCalculator] Loading models for ${provider}...`);
                const response = await fetch(`/api/tokens/models/${provider}`);
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                }
                const data = await response.json();
                this.providerModels[provider] = data.models || [];
                console.log(`[TokenCalculator] Loaded ${this.providerModels[provider].length} models for ${provider}:`, this.providerModels[provider]);
            } catch (error) {
                console.error(`Failed to load models for ${provider}:`, error);
                this.providerModels[provider] = [];
            }
        }
        
        console.log('[TokenCalculator] All provider models loaded:', this.providerModels);
    }

    updateModelOptions() {
        // Update provider dropdowns
        this.updateProviderDropdowns();
        
        // Update model dropdowns
        this.updateModelDropdown('token-model', this.currentProvider);
        this.updateModelDropdown('cost-model', this.currentProvider);
        
        // Ensure cost estimation tool is properly initialized
        this.initializeCostEstimationTool();
        
        console.log('[TokenCalculator] Model options updated - current provider:', this.currentProvider);
    }

    updateProviderDropdowns() {
        console.log('[TokenCalculator] Updating provider dropdowns with settings:', this.settings);
        
        // Update main token provider dropdown
        const tokenProviderSelect = document.getElementById('token-provider');
        if (tokenProviderSelect) {
            console.log('[TokenCalculator] Found token-provider select, populating...');
            tokenProviderSelect.innerHTML = '';
            Object.entries(this.settings.providers).forEach(([key, provider]) => {
                if (provider.enabled) {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = provider.name;
                    if (key === this.currentProvider) {
                        option.selected = true;
                    }
                    tokenProviderSelect.appendChild(option);
                    console.log(`[TokenCalculator] Added provider option: ${key} - ${provider.name}`);
                }
            });
        } else {
            console.warn('[TokenCalculator] token-provider select not found!');
        }

        // Update cost provider dropdown
        const costProviderSelect = document.getElementById('cost-provider');
        if (costProviderSelect) {
            console.log('[TokenCalculator] Found cost-provider select, populating...');
            costProviderSelect.innerHTML = '';
            Object.entries(this.settings.providers).forEach(([key, provider]) => {
                if (provider.enabled) {
                    const option = document.createElement('option');
                    option.value = key;
                    option.textContent = provider.name;
                    // Set the default provider as selected for cost estimation
                    if (key === this.currentProvider) {
                        option.selected = true;
                    }
                    costProviderSelect.appendChild(option);
                    console.log(`[TokenCalculator] Added cost provider option: ${key} - ${provider.name}`);
                }
            });
        } else {
            console.warn('[TokenCalculator] cost-provider select not found!');
        }
    }

    updateModelDropdown(selectId, provider) {
        console.log(`[TokenCalculator] Updating model dropdown ${selectId} for provider ${provider}`);
        
        const modelSelect = document.getElementById(selectId);
        if (!modelSelect) {
            console.warn(`[TokenCalculator] Model select ${selectId} not found!`);
            return;
        }

        const models = this.providerModels[provider] || [];
        console.log(`[TokenCalculator] Available models for ${provider}:`, models);
        
        modelSelect.innerHTML = '';

        models.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = this.formatModelName(model);
            modelSelect.appendChild(option);
            console.log(`[TokenCalculator] Added model option: ${model}`);
        });

        // Set default model from settings if available
        if (this.settings.providers[provider] && this.settings.providers[provider].default_model) {
            const defaultModel = this.settings.providers[provider].default_model;
            console.log(`[TokenCalculator] Default model from settings: ${defaultModel}`);
            if (models.includes(defaultModel)) {
                this.currentModel = defaultModel;
                modelSelect.value = this.currentModel;
                console.log(`[TokenCalculator] Set model to default: ${this.currentModel}`);
            } else if (models.length > 0) {
                this.currentModel = models[0];
                modelSelect.value = this.currentModel;
                console.log(`[TokenCalculator] Set model to first available: ${this.currentModel}`);
            }
        } else if (models.length > 0) {
            this.currentModel = models[0];
            modelSelect.value = this.currentModel;
            console.log(`[TokenCalculator] Set model to first available (no default): ${this.currentModel}`);
        }
    }



    formatModelName(model) {
        // Convert model names to more readable format
        const nameMap = {
            'gpt-5': 'GPT-5',
            'gpt-4o': 'GPT-4o',
            'gpt-4o-mini': 'GPT-4o Mini',
            'gpt-4': 'GPT-4',
            'gpt-3.5-turbo': 'GPT-3.5 Turbo',
            'claude-3-5-sonnet': 'Claude 3.5 Sonnet',
            'claude-3-5-haiku': 'Claude 3.5 Haiku',
            'claude-3-opus': 'Claude 3 Opus',
            'claude-3-sonnet': 'Claude 3 Sonnet',
            'claude-3-haiku': 'Claude 3 Haiku',
            'gemini-2.0-flash': 'Gemini 2.0 Flash',
            'gemini-1.5-pro': 'Gemini 1.5 Pro',
            'gemini-1.5-flash': 'Gemini 1.5 Flash'
        };
        return nameMap[model] || model;
    }

    updateCharacterCount() {
        const textInput = document.getElementById('token-text-input');
        const text = textInput?.value || '';
        const characterCount = text.length;
        const wordCount = text.trim() ? text.trim().split(/\s+/).length : 0;
        
        // Update character count display if available
        const charDisplay = document.getElementById('character-count');
        if (charDisplay) {
            charDisplay.textContent = characterCount.toLocaleString();
        }
        
        const wordDisplay = document.getElementById('word-count');
        if (wordDisplay) {
            wordDisplay.textContent = wordCount.toLocaleString();
        }
    }

    async countTokens() {
        const textInput = document.getElementById('token-text-input');
        const text = textInput?.value?.trim();
        
        if (!text) {
            this.showError('Please enter some text to analyze.');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            const response = await fetch('/api/tokens/count', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    provider: this.currentProvider,
                    model: this.currentModel
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displaySingleProviderResults(data);
            } else {
                this.showError(data.error || 'Failed to count tokens');
            }
        } catch (error) {
            console.error('Token counting error:', error);
            this.showError('Network error occurred while counting tokens');
        } finally {
            this.showLoading(false);
        }
    }

    async analyzeAllProviders() {
        const textInput = document.getElementById('token-text-input');
        const text = textInput?.value?.trim();
        
        if (!text) {
            this.showError('Please enter some text to analyze.');
            return;
        }

        this.showLoading(true);
        this.hideError();

        try {
            // Get enabled providers from settings
            const enabledProviders = Object.keys(this.settings.providers).filter(
                provider => this.settings.providers[provider].enabled
            );

            const response = await fetch('/api/tokens/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    providers: enabledProviders
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayMultiProviderResults(data);
            } else {
                this.showError(data.error || 'Failed to analyze text');
            }
        } catch (error) {
            console.error('Text analysis error:', error);
            this.showError('Network error occurred while analyzing text');
        } finally {
            this.showLoading(false);
        }
    }

    async estimateCost() {
        const inputTokens = parseInt(document.getElementById('input-tokens')?.value || 0);
        const outputTokens = parseInt(document.getElementById('output-tokens')?.value || 0);
        const provider = document.getElementById('cost-provider')?.value || 'openai';
        const model = document.getElementById('cost-model')?.value;

        if (inputTokens === 0 && outputTokens === 0) {
            this.showError('Please enter at least one token count.');
            return;
        }

        try {
            const response = await fetch('/api/tokens/estimate-cost', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input_tokens: inputTokens,
                    output_tokens: outputTokens,
                    provider: provider,
                    model: model
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.displayCostEstimate(data);
            } else {
                this.showError(data.error || 'Failed to estimate cost');
            }
        } catch (error) {
            console.error('Cost estimation error:', error);
            this.showError('Network error occurred while estimating cost');
        }
    }

    displaySingleProviderResults(data) {
        const resultsDiv = document.getElementById('token-results');
        const singleResultsDiv = document.getElementById('single-provider-results');
        const multiResultsDiv = document.getElementById('multi-provider-results');

        if (resultsDiv) resultsDiv.style.display = 'block';
        if (singleResultsDiv) singleResultsDiv.style.display = 'block';
        if (multiResultsDiv) multiResultsDiv.style.display = 'none';

        // Update metrics
        const tokenCount = document.getElementById('token-count');
        const characterCount = document.getElementById('character-count');
        const wordCount = document.getElementById('word-count');
        const estimatedCost = document.getElementById('estimated-cost');

        if (tokenCount) tokenCount.textContent = data.input_tokens?.toLocaleString() || '0';
        if (characterCount) characterCount.textContent = data.characters?.toLocaleString() || '0';
        if (wordCount) wordCount.textContent = data.words?.toLocaleString() || '0';
        if (estimatedCost) {
            const cost = data.estimated_cost || 0;
            estimatedCost.textContent = cost > 0 ? `$${cost.toFixed(4)}` : '$0.00';
        }

        // Auto-populate cost estimation fields with token counts
        this.populateCostEstimationFields(data.input_tokens || 0, data.output_tokens || 0);
    }

    displayMultiProviderResults(data) {
        const resultsDiv = document.getElementById('token-results');
        const singleResultsDiv = document.getElementById('single-provider-results');
        const multiResultsDiv = document.getElementById('multi-provider-results');
        const comparisonTable = document.getElementById('provider-comparison-table');

        if (resultsDiv) resultsDiv.style.display = 'block';
        if (singleResultsDiv) singleResultsDiv.style.display = 'none';
        if (multiResultsDiv) multiResultsDiv.style.display = 'block';

        if (comparisonTable) {
            comparisonTable.innerHTML = '';

            Object.entries(data.providers || {}).forEach(([provider, info]) => {
                if (info.error) {
                    const row = comparisonTable.insertRow();
                    row.innerHTML = `
                        <td><span class="badge provider-${provider}">${provider.toUpperCase()}</span></td>
                        <td colspan="5" class="text-danger">${info.error}</td>
                    `;
                } else {
                    const row = comparisonTable.insertRow();
                    row.innerHTML = `
                        <td><span class="badge provider-${provider}">${provider.toUpperCase()}</span></td>
                        <td>${this.formatModelName(info.model)}</td>
                        <td>${info.input_tokens?.toLocaleString() || '0'}</td>
                        <td>${info.estimated_cost ? `$${info.estimated_cost.toFixed(4)}` : '$0.00'}</td>
                        <td>${info.tokens_per_word?.toFixed(2) || '0.00'}</td>
                        <td>${info.tokens_per_character?.toFixed(3) || '0.000'}</td>
                    `;
                }
            });
        }

        // Auto-populate cost estimation fields with the first successful provider's results
        const firstProvider = Object.values(data.providers || {}).find(info => !info.error);
        if (firstProvider) {
            this.populateCostEstimationFields(firstProvider.input_tokens || 0, firstProvider.output_tokens || 0);
        }
    }

    displayCostEstimate(data) {
        const costResult = document.getElementById('cost-result');
        const costAmount = document.getElementById('cost-amount');

        if (costResult) costResult.style.display = 'block';
        if (costAmount) {
            const cost = data.estimated_cost || 0;
            costAmount.textContent = cost > 0 ? `$${cost.toFixed(4)}` : '$0.00';
        }
    }

    showLoading(show) {
        const loadingDiv = document.getElementById('token-loading');
        const resultsDiv = document.getElementById('token-results');
        
        if (loadingDiv) loadingDiv.style.display = show ? 'block' : 'none';
        if (resultsDiv && show) resultsDiv.style.display = 'none';
    }

    showError(message) {
        const errorDiv = document.getElementById('token-error');
        const errorMessage = document.getElementById('error-message');
        
        if (errorDiv) errorDiv.style.display = 'block';
        if (errorMessage) errorMessage.textContent = message;
    }

    hideError() {
        const errorDiv = document.getElementById('token-error');
        if (errorDiv) errorDiv.style.display = 'none';
    }

    // Public method to get current token count for external use
    async getTokenCount(text, provider = 'openai', model = null) {
        try {
            const response = await fetch('/api/tokens/count', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    text: text,
                    provider: provider,
                    model: model
                })
            });

            const data = await response.json();
            return response.ok ? data : null;
        } catch (error) {
            console.error('Error getting token count:', error);
            return null;
        }
    }

    // Public method to check if TokenCalculator is ready
    isReady() {
        return this.settings !== null && Object.keys(this.providerModels).length > 0;
    }

    // Public method to force refresh dropdowns
    refreshDropdowns() {
        if (this.isReady()) {
            console.log('[TokenCalculator] Refreshing dropdowns...');
            this.updateModelOptions();
        } else {
            console.warn('[TokenCalculator] Not ready, cannot refresh dropdowns');
        }
    }

    // Initialize cost estimation tool with default provider
    initializeCostEstimationTool() {
        const costProviderSelect = document.getElementById('cost-provider');
        if (costProviderSelect && this.currentProvider) {
            // Set the default provider for cost estimation
            costProviderSelect.value = this.currentProvider;
            console.log('[TokenCalculator] Cost estimation tool initialized with provider:', this.currentProvider);
            
            // Trigger change event to update the model dropdown
            const event = new Event('change', { bubbles: true });
            costProviderSelect.dispatchEvent(event);
        }
    }

    // Populate cost estimation fields with token counts
    populateCostEstimationFields(inputTokens, outputTokens) {
        const inputTokensField = document.getElementById('input-tokens');
        const outputTokensField = document.getElementById('output-tokens');
        
        if (inputTokensField) {
            inputTokensField.value = inputTokens;
            console.log('[TokenCalculator] Populated input tokens field with:', inputTokens);
        }
        
        if (outputTokensField) {
            outputTokensField.value = outputTokens;
            console.log('[TokenCalculator] Populated output tokens field with:', outputTokens);
        }
        
        // Also update the cost provider and model to match the current selection
        const costProviderSelect = document.getElementById('cost-provider');
        const costModelSelect = document.getElementById('cost-model');
        
        if (costProviderSelect && costProviderSelect.value !== this.currentProvider) {
            costProviderSelect.value = this.currentProvider;
            // Trigger change event to update the model dropdown
            const event = new Event('change', { bubbles: true });
            costProviderSelect.dispatchEvent(event);
        }
        
        console.log('[TokenCalculator] Cost estimation fields populated - Input:', inputTokens, 'Output:', outputTokens);
    }

    // Use current tokens from the last analysis
    useCurrentTokens() {
        const tokenCountElement = document.getElementById('token-count');
        if (tokenCountElement && tokenCountElement.textContent !== '0') {
            const currentTokens = parseInt(tokenCountElement.textContent.replace(/,/g, '')) || 0;
            this.populateCostEstimationFields(currentTokens, 0);
            console.log('[TokenCalculator] Used current tokens:', currentTokens);
        } else {
            this.showError('No token count available. Please run a token analysis first.');
        }
    }

    // Debug method to get current state
    getDebugInfo() {
        return {
            isReady: this.isReady(),
            settings: this.settings,
            currentProvider: this.currentProvider,
            currentModel: this.currentModel,
            providerModels: this.providerModels,
            hasTokenProviderSelect: !!document.getElementById('token-provider'),
            hasTokenModelSelect: !!document.getElementById('token-model'),
            hasCostProviderSelect: !!document.getElementById('cost-provider'),
            hasCostModelSelect: !!document.getElementById('cost-model'),
            costProviderValue: document.getElementById('cost-provider')?.value || 'not found'
        };
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TokenCalculator;
}
