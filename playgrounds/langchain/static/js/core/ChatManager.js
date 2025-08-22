/**
 * Chat Manager Module
 * Handles chat interactions, optimization, and conversation management
 */
class ChatManager {
    constructor() {
        this.app = null;
    }

    /**
     * Set reference to main app instance
     */
    async setApp(app) {
        this.app = app;
        this.initializePromptTabs();
        this.initializeContextTracking();
        this.initializeUsageControls();
        
        // Only populate provider dropdowns if settings and settingsManager are already loaded
        if (this.app.settings && this.app.settingsManager) {
            await this.populateProviderDropdowns();
        }
    }

    /**
     * Initialize prompt navigation tabs
     */
    initializePromptTabs() {
        const tabs = document.querySelectorAll('.prompt-tab');
        
        tabs.forEach(tab => {
            tab.addEventListener('click', async () => {
                await this.switchPromptTab(tab);
            });
        });
    }

    /**
     * Switch between prompt tabs
     */
    async switchPromptTab(selectedTab) {
        // Remove active class from all tabs
        document.querySelectorAll('.prompt-tab').forEach(tab => {
            tab.classList.remove('prompt-tab-active');
        });
        
        // Add active class to selected tab
        selectedTab.classList.add('prompt-tab-active');
        
        // Get the prompt template from data attribute
        const promptTemplate = selectedTab.getAttribute('data-prompt');
        if (promptTemplate) {
            // Replace {owner_repo} placeholder with actual repo from settings
            const settings = this.app.getSettings();
            const repo = settings?.mcp?.github?.repo || 'owner/repo';
            const finalPrompt = promptTemplate.replace('{owner_repo}', repo);
            
            // Set the prompt in the user prompt textarea
            await this.setUserPrompt(finalPrompt);
            
            // Set focus to the user prompt textarea
            this.setFocusToUserPrompt();
            
            // Log the tab switch
            this.app.debugManager.addLog('info', `Switched to ${selectedTab.getAttribute('data-tab')} tab`, {
                tab: selectedTab.getAttribute('data-tab'),
                repo: repo,
                prompt_length: finalPrompt.length
            });
        }
    }

    /**
     * Populate provider and model dropdowns from settings
     */
    async populateProviderDropdowns() {
        console.log('[ChatManager] populateProviderDropdowns called');
        console.log('[ChatManager] app.settings:', this.app?.settings);
        
        if (!this.app || !this.app.settings) {
            console.log('[ChatManager] No app or settings available, returning');
            return;
        }
        
        const providerSelect = document.getElementById('provider');
        const modelSelect = document.getElementById('model');
        
        if (!providerSelect || !modelSelect) {
            console.log('[ChatManager] Provider or model select elements not found');
            return;
        }
        
        // Clear existing options
        providerSelect.innerHTML = '';
        modelSelect.innerHTML = '';
        
        // Populate provider dropdown
        const providers = this.app.settings.providers || {};
        
        Object.keys(providers).forEach(providerKey => {
            const provider = providers[providerKey];
            if (provider && provider.enabled) {
                const option = document.createElement('option');
                option.value = providerKey;
                option.textContent = `${provider.name || providerKey} (${providerKey})`;
                providerSelect.appendChild(option);
            }
        });
        
        // Set default provider and populate models
        if (providerSelect.children.length > 0) {
            // Use the default provider from settings, or fallback to first available
            const settingsDefaultProvider = this.app.settings?.default_provider || 'anthropic';
            let defaultProvider = settingsDefaultProvider;
            
            // Validate that the default provider is available in the dropdown
            const availableProviders = Array.from(providerSelect.children).map(option => option.value);
            if (!availableProviders.includes(defaultProvider)) {
                defaultProvider = providerSelect.children[0].value;
            }
            
            providerSelect.value = defaultProvider;
            await this.populateModelDropdown(defaultProvider);
        }
        
        // Add change listeners
        providerSelect.addEventListener('change', async (e) => {
            await this.populateModelDropdown(e.target.value);
            this.updateDebugInfo();
            await this.updateContextWindowInfo();
        });
        
        this.updateDebugInfo();
    }

    /**
     * Initialize context window tracking
     */
    initializeContextTracking() {
        const userPromptTextarea = document.getElementById('userPrompt');
        const optimizedPromptTextarea = document.getElementById('optimizedPrompt');
        
        if (userPromptTextarea) {
            userPromptTextarea.addEventListener('input', async () => {
                await this.updateContextWindowInfo();
            });
        }
        
        if (optimizedPromptTextarea) {
            // For readonly textarea, use MutationObserver to detect programmatic changes
            const observer = new MutationObserver(async () => {
                await this.updateContextWindowInfo();
            });
            
            observer.observe(optimizedPromptTextarea, {
                attributes: true,
                attributeFilter: ['value'],
                childList: false,
                subtree: false
            });
            
            // Also listen for input events in case it becomes editable
            optimizedPromptTextarea.addEventListener('input', async () => {
                await this.updateContextWindowInfo();
            });
        }
        
        // Initial update
        setTimeout(async () => {
            await this.updateContextWindowInfo();
        }, 100);
    }

    /**
     * Update context window information display
     */
    async updateContextWindowInfo() {
        const userPromptTextarea = document.getElementById('userPrompt');
        const optimizedPromptTextarea = document.getElementById('optimizedPrompt');
        const providerSelect = document.getElementById('provider');
        
        if (!userPromptTextarea || !optimizedPromptTextarea || !providerSelect) {
            console.log('[ChatManager] updateContextWindowInfo: Missing required elements', {
                userPromptTextarea: !!userPromptTextarea,
                optimizedPromptTextarea: !!optimizedPromptTextarea,
                providerSelect: !!providerSelect
            });
            return;
        }
        
        const userPromptText = userPromptTextarea.value;
        const optimizedPromptText = optimizedPromptTextarea.value;
        const selectedProvider = providerSelect.value;
        
        // Update character counts
        const userPromptChars = userPromptText.length;
        const optimizedPromptChars = optimizedPromptText.length;
        
        document.getElementById('userPromptChars').textContent = `${userPromptChars} chars`;
        document.getElementById('optimizedPromptChars').textContent = `${optimizedPromptChars} chars`;
        
        // Update detailed optimized prompt display
        document.getElementById('optimizedPromptDetailedChars').textContent = `${optimizedPromptChars} chars`;
        
        // Use token calculator for accurate token counting
        let userPromptTokens = 0;
        let optimizedPromptTokens = 0;
        
        try {
            // Get accurate token counts using the token calculator
            if (userPromptText.trim()) {
                const userTokenResult = await this.app.tokenCalculator.getTokenCount(userPromptText, selectedProvider);
                userPromptTokens = userTokenResult?.input_tokens || Math.ceil(userPromptChars / 4);
            }
            
            if (optimizedPromptText.trim()) {
                const optimizedTokenResult = await this.app.tokenCalculator.getTokenCount(optimizedPromptText, selectedProvider);
                optimizedPromptTokens = optimizedTokenResult?.input_tokens || Math.ceil(optimizedPromptChars / 4);
            }
        } catch (error) {
            console.warn('[ChatManager] Token calculation failed, using fallback estimation:', error);
            // Fallback to character-based estimation
            userPromptTokens = Math.ceil(userPromptChars / 4);
            optimizedPromptTokens = Math.ceil(optimizedPromptChars / 4);
        }
        
        document.getElementById('userPromptTokens').textContent = `(~${userPromptTokens} tokens)`;
        document.getElementById('optimizedPromptTokens').textContent = `(~${optimizedPromptTokens} tokens)`;
        document.getElementById('optimizedPromptDetailedTokens').textContent = `(~${optimizedPromptTokens} tokens)`;
        
        // Get model context window
        const modelContextWindow = this.getModelContextWindow(selectedProvider);
        document.getElementById('modelContextWindow').textContent = modelContextWindow.toLocaleString();
        document.getElementById('optimizedModelContextWindow').textContent = modelContextWindow.toLocaleString();
        
        // Calculate usage for main context window (user + optimized)
        const totalTokens = userPromptTokens + optimizedPromptTokens;
        const usagePercentage = Math.min((totalTokens / modelContextWindow) * 100, 100);
        const remainingTokens = Math.max(modelContextWindow - totalTokens, 0);
        
        // Calculate usage for optimized prompt only
        const optimizedUsagePercentage = Math.min((optimizedPromptTokens / modelContextWindow) * 100, 100);
        const optimizedRemainingTokens = Math.max(modelContextWindow - optimizedPromptTokens, 0);
        
        console.log('[ChatManager] updateContextWindowInfo: Calculation details', {
            userPromptChars,
            optimizedPromptChars,
            userPromptTokens,
            optimizedPromptTokens,
            totalTokens,
            selectedProvider,
            modelContextWindow,
            usagePercentage,
            remainingTokens,
            optimizedUsagePercentage,
            optimizedRemainingTokens
        });
        
        // Update main progress bar
        const progressBar = document.getElementById('contextUsageBar');
        if (progressBar) {
            progressBar.style.width = `${usagePercentage}%`;
            
            // Change color based on usage
            if (usagePercentage > 90) {
                progressBar.className = 'bg-red-500 h-1.5 rounded-full transition-all duration-300';
            } else if (usagePercentage > 70) {
                progressBar.className = 'bg-yellow-500 h-1.5 rounded-full transition-all duration-300';
            } else {
                progressBar.className = 'bg-blue-500 h-1.5 rounded-full transition-all duration-300';
            }
        }
        
        // Update optimized prompt progress bar
        const optimizedProgressBar = document.getElementById('optimizedContextUsageBar');
        if (optimizedProgressBar) {
            optimizedProgressBar.style.width = `${optimizedUsagePercentage}%`;
            
            // Change color based on usage
            if (optimizedUsagePercentage > 90) {
                optimizedProgressBar.className = 'bg-red-500 h-1.5 rounded-full transition-all duration-300';
            } else if (optimizedUsagePercentage > 70) {
                optimizedProgressBar.className = 'bg-yellow-500 h-1.5 rounded-full transition-all duration-300';
            } else {
                optimizedProgressBar.className = 'bg-blue-500 h-1.5 rounded-full transition-all duration-300';
            }
        }
        
        // Update usage text
        document.getElementById('contextUsageText').textContent = `${usagePercentage.toFixed(1)}% used`;
        document.getElementById('contextRemainingText').textContent = `${remainingTokens.toLocaleString()} tokens remaining`;
        
        // Update optimized prompt usage text
        document.getElementById('optimizedContextUsageText').textContent = `${optimizedUsagePercentage.toFixed(1)}% used`;
        document.getElementById('optimizedContextRemainingText').textContent = `${optimizedRemainingTokens.toLocaleString()} tokens remaining`;
        
        // Update provider usage tracking
        this.updateProviderUsageDisplay(selectedProvider, userPromptTokens, optimizedPromptTokens);
        
        // Update optimizer limits display
        this.updateOptimizerLimitsDisplay(selectedProvider);
    }
    
    /**
     * Update optimizer limits display
     */
    updateOptimizerLimitsDisplay(providerKey) {
        if (!this.app || !this.app.settings) return;
        
        const optimizer = this.app.settings.optimizer || {};
        const providers = this.app.settings.providers || {};
        const provider = providers[providerKey];
        
        if (!provider) return;
        
        const maxTokens = optimizer.max_tokens || 1000;
        const maxContextUsage = (optimizer.max_context_usage || 0.8) * 100;
        const contextWindow = provider.context_window || 100000;
        const appliedBudget = Math.min(maxTokens, Math.floor(contextWindow * (optimizer.max_context_usage || 0.8) * 0.75));
        
        // Update optimizer limits display if elements exist
        const limitsElements = {
            'optimizerMaxTokens': document.getElementById('optimizerMaxTokens'),
            'optimizerMaxContext': document.getElementById('optimizerMaxContext'),
            'optimizerAppliedBudget': document.getElementById('optimizerAppliedBudget')
        };
        
        if (limitsElements.optimizerMaxTokens) {
            limitsElements.optimizerMaxTokens.textContent = maxTokens.toLocaleString();
        }
        
        if (limitsElements.optimizerMaxContext) {
            limitsElements.optimizerMaxContext.textContent = `${maxContextUsage.toFixed(0)}%`;
        }
        
        if (limitsElements.optimizerAppliedBudget) {
            limitsElements.optimizerAppliedBudget.textContent = appliedBudget.toLocaleString();
        }
    }
    
    /**
     * Update provider usage display
     */
    updateProviderUsageDisplay(providerKey, userTokens, optimizedTokens) {
        if (!this.app || !this.app.settings) return;
        
        const providers = this.app.settings.providers || {};
        const provider = providers[providerKey];
        
        if (!provider) return;
        
        // Get usage information from server
        this.getProviderUsage(providerKey).then(usage => {
            if (usage) {
                this.displayProviderUsage(usage, userTokens, optimizedTokens);
            }
        }).catch(error => {
            console.error('[ChatManager] Error getting provider usage:', error);
        });
    }
    
    /**
     * Get provider usage from server
     */
    async getProviderUsage(providerKey) {
        try {
            const response = await fetch(`/api/usage/${providerKey}`);
            if (response.ok) {
                return await response.json();
            }
        } catch (error) {
            console.error('[ChatManager] Error fetching provider usage:', error);
        }
        return null;
    }
    
    /**
     * Display provider usage information
     */
    displayProviderUsage(usage, userTokens, optimizedTokens) {
        // Update usage display elements if they exist
        const usageElements = {
            'totalTokensUsed': document.getElementById('providerTotalTokens'),
            'usagePercentage': document.getElementById('providerUsagePercentage'),
            'remainingTokens': document.getElementById('providerRemainingTokens'),
            'apiCalls': document.getElementById('providerApiCalls')
        };
        
        if (usageElements.totalTokensUsed) {
            usageElements.totalTokensUsed.textContent = usage.total_tokens_used.toLocaleString();
        }
        
        if (usageElements.usagePercentage) {
            usageElements.usagePercentage.textContent = `${usage.usage_percentage.toFixed(1)}%`;
        }
        
        if (usageElements.remainingTokens) {
            usageElements.remainingTokens.textContent = usage.remaining_tokens.toLocaleString();
        }
        
        if (usageElements.apiCalls) {
            usageElements.apiCalls.textContent = usage.api_calls.toLocaleString();
        }
        
        // Show warning if usage cap is exceeded
        if (usage.is_cap_exceeded) {
            this.showUsageCapWarning();
        }
    }
    
    /**
     * Show usage cap warning
     */
    showUsageCapWarning() {
        const warningElement = document.getElementById('usageCapWarning');
        if (warningElement) {
            warningElement.classList.remove('hidden');
            warningElement.textContent = '⚠️ Usage cap exceeded. Please check your settings or contact administrator.';
        }
    }
    
    /**
     * Track usage for a provider
     */
    trackUsage(providerKey, usageData) {
        const userPrompt = this.getFormValue('#userPrompt');
        const optimizedPrompt = this.getFormValue('#optimizedPrompt');
        
        // Estimate tokens
        const userTokens = Math.ceil(userPrompt.length / 4);
        const optimizedTokens = Math.ceil(optimizedPrompt.length / 4);
        const responseTokens = usageData.response_tokens || 0;
        
        // Send usage update to server
        this.updateProviderUsage(providerKey, userTokens, optimizedTokens, responseTokens);
    }
    
    /**
     * Update provider usage on server
     */
    async updateProviderUsage(providerKey, userTokens, optimizedTokens, responseTokens) {
        try {
            const response = await fetch('/api/usage/update', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: providerKey,
                    user_tokens: userTokens,
                    optimized_tokens: optimizedTokens,
                    response_tokens: responseTokens,
                    api_calls: 1
                })
            });
            
            if (response.ok) {
                const result = await response.json();
                if (result.success) {
                    console.log('[ChatManager] Usage updated successfully:', result);
                    // Refresh usage display
                    this.updateProviderUsageDisplay(providerKey, userTokens, optimizedTokens);
                } else {
                    console.warn('[ChatManager] Usage update failed:', result.error);
                    if (result.error === 'usage_cap_exceeded') {
                        this.showUsageCapWarning();
                    }
                }
            }
        } catch (error) {
            console.error('[ChatManager] Error updating provider usage:', error);
        }
    }
    
    /**
     * Initialize usage controls
     */
    initializeUsageControls() {
        const resetUsageBtn = document.getElementById('resetUsageBtn');
        if (resetUsageBtn) {
            resetUsageBtn.addEventListener('click', () => {
                this.resetProviderUsage();
            });
        }
    }
    
    /**
     * Reset provider usage
     */
    async resetProviderUsage() {
        const providerSelect = document.getElementById('provider');
        if (!providerSelect) return;
        
        const providerKey = providerSelect.value;
        
        if (confirm(`Are you sure you want to reset usage for ${providerKey}?`)) {
            try {
                const response = await fetch(`/api/usage/reset/${providerKey}`, {
                    method: 'POST'
                });
                
                if (response.ok) {
                    const result = await response.json();
                    if (result.success) {
                        console.log('[ChatManager] Usage reset successfully');
                        // Refresh usage display
                        this.updateProviderUsageDisplay(providerKey, 0, 0);
                        // Hide warning if it was showing
                        const warningElement = document.getElementById('usageCapWarning');
                        if (warningElement) {
                            warningElement.classList.add('hidden');
                        }
                    }
                }
            } catch (error) {
                console.error('[ChatManager] Error resetting provider usage:', error);
            }
        }
    }

    /**
     * Get context window size for the selected provider/model
     */
    getModelContextWindow(providerKey) {
        if (!this.app || !this.app.settings) return 100000; // Default fallback
        
        const providers = this.app.settings.providers || {};
        const provider = providers[providerKey];
        
        if (!provider) return 100000;
        
        // Get context window from model data if available
        const modelSelect = document.getElementById('model');
        const selectedModel = modelSelect ? modelSelect.value : provider.default_model;
        
        // Try to find the selected model in the provider's models array
        if (provider.models && Array.isArray(provider.models)) {
            const modelData = provider.models.find(model => model.id === selectedModel);
            if (modelData && modelData.context_window) {
                return modelData.context_window;
            }
        }
        
        // Fallback to provider's default context window
        return provider.context_window || 100000;
    }

    /**
     * Populate model dropdown based on selected provider
     */
    async populateModelDropdown(providerKey) {
        if (!this.app || !this.app.settings) return;
        
        const modelSelect = document.getElementById('model');
        if (!modelSelect) return;
        
        // Clear existing options
        modelSelect.innerHTML = '';
        
        const providers = this.app.settings.providers || {};
        const provider = providers[providerKey];
        
        // Get model options from SettingsManager
        const modelOptions = this.app.settingsManager?.modelOptions?.[providerKey] || [];
        
        if (provider && provider.models && Array.isArray(provider.models)) {
            // Use models from provider settings if available
            provider.models.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === provider.default_model) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
        } else if (modelOptions.length > 0) {
            // Use predefined model options
            modelOptions.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                if (model === provider?.default_model) {
                    option.selected = true;
                }
                modelSelect.appendChild(option);
            });
        } else if (provider && provider.default_model) {
            // Fallback: just add the default model
            const option = document.createElement('option');
            option.value = provider.default_model;
            option.textContent = provider.default_model;
            option.selected = true;
            modelSelect.appendChild(option);
        }
        
        // Set default selection if none is selected
        if (modelSelect.value === '' && modelSelect.children.length > 0) {
            modelSelect.children[0].selected = true;
        }
        
        // Add change event listener to model dropdown
        modelSelect.addEventListener('change', async () => {
            this.updateDebugInfo();
            await this.updateContextWindowInfo();
        });
        
        // Update context window info after populating models
        await this.updateContextWindowInfo();
    }

    /**
     * Refresh provider dropdowns (called when settings are updated)
     */
    async refreshProviderDropdowns() {
        await this.populateProviderDropdowns();
    }

    /**
     * Set focus to the user prompt textarea
     */
    setFocusToUserPrompt() {
        const userPromptTextarea = document.getElementById('userPrompt');
        if (userPromptTextarea) {
            userPromptTextarea.focus();
        }
    }

    /**
     * Set user prompt value and update context window info
     */
    async setUserPrompt(text) {
        const userPromptTextarea = document.getElementById('userPrompt');
        if (userPromptTextarea) {
            userPromptTextarea.value = text;
            await this.updateContextWindowInfo();
        }
    }

    /**
     * Optimize a user prompt
     */
    async optimize() {
        const userPrompt = this.getFormValue('#userPrompt');
        const provider = this.getFormValue('#provider') || this.app.settings?.default_provider || 'anthropic';
        const model = this.getFormValue('#model') || '';

        if (!userPrompt.trim()) {
            alert('Please enter a prompt to optimize.');
            return;
        }

        // Show progress
        this.showProgress('#optimizeProgress', '#optimizeStatus', '#optimizeProgressBar', '#optimizeText', '#btnOptimize');
        
        try {
            // Simulate progress steps with detailed logging
            this.app.logDebug('optimize.start', { userPrompt, provider, model });
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 10, 'Analyzing prompt...');
            this.app.logDebug('optimize.progress', { step: 'analyzing_prompt', percent: 10, status: 'Analyzing prompt...' });
            await this.delay(300);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 30, 'Fetching context...');
            this.app.logDebug('optimize.progress', { step: 'fetching_context', percent: 30, status: 'Fetching context...' });
            await this.delay(300);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 50, 'Summarizing content...');
            this.app.logDebug('optimize.progress', { step: 'summarizing_content', percent: 50, status: 'Summarizing content...' });
            await this.delay(300);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 70, 'Optimizing prompt...');
            this.app.logDebug('optimize.progress', { step: 'optimizing_prompt', percent: 70, status: 'Optimizing prompt...' });
            await this.delay(300);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 80, 'Building request...');
            this.app.logDebug('optimize.progress', { step: 'building_request', percent: 80, status: 'Building request...' });
            await this.delay(200);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 85, 'Sending to API...');
            this.app.logDebug('optimize.progress', { step: 'sending_to_api', percent: 85, status: 'Sending to API...' });
            
            const requestBody = { user_prompt: userPrompt, provider, model };
            this.app.logDebug('optimize.request', { url: '/api/optimize', method: 'POST', body: requestBody });
            
            // Simulate MCP calls progress
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 87, 'Calling GitHub MCP...');
            this.app.logDebug('optimize.progress', { step: 'calling_github_mcp', percent: 87, status: 'Calling GitHub MCP...' });
            await this.delay(150);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 89, 'Calling PostgreSQL MCP...');
            this.app.logDebug('optimize.progress', { step: 'calling_postgresql_mcp', percent: 89, status: 'Calling PostgreSQL MCP...' });
            await this.delay(150);
            
                         this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 91, 'Sending to LLM...');
             this.app.logDebug('optimize.progress', { step: 'sending_to_llm', percent: 91, status: 'Sending to LLM...' });
             
             // Start periodic usage updates during optimization
             const usageUpdateInterval = setInterval(() => {
                 this.updateProviderUsageDisplay(provider, 0, 0);
             }, 1000); // Update every second
             
             const response = await fetch('/api/optimize', {
                 method: 'POST',
                 headers: { 'Content-Type': 'application/json' },
                 body: JSON.stringify(requestBody)
             });
             
             // Clear the interval after response
             clearInterval(usageUpdateInterval);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 95, 'Processing response...');
            this.app.logDebug('optimize.progress', { step: 'processing_response', percent: 95, status: 'Processing response...', statusCode: response.status });
            await this.delay(200);
            
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 100, 'Complete!');
            this.app.logDebug('optimize.progress', { step: 'complete', percent: 100, status: 'Complete!' });
            await this.delay(200);
            
            const data = await response.json();
            this.app.logDebug('optimize.response', { status: response.status, data: data });
            
                         this.setFormValue('#optimizedPrompt', data.optimized_prompt || userPrompt);
             await this.updateContextWindowInfo(); // Update context window info after optimization
             
             // Final usage update after optimization
             this.updateProviderUsageDisplay(provider, 0, 0);

            // Track usage for optimization
            if (data.usage_tracking) {
                this.trackUsage(provider, data.usage_tracking);
            }

            // Rich debug
            this.app.debugManager.renderDebug(data.debug);
            this.app.logDebug('optimize.success', { optimized_prompt: data.optimized_prompt, debug: data.debug });
            this.app.activateTab('debug');
            
        } catch (error) {
            this.updateProgress('#optimizeProgressBar', '#optimizeStatus', 100, 'Error occurred');
            this.app.logDebug('optimize.error', { error: error.message, stack: error.stack });
            console.error('Optimize error:', error);
        } finally {
            // Hide progress after a short delay
            setTimeout(() => {
                this.hideProgress('#optimizeProgress', '#optimizeStatus', '#optimizeText', '#btnOptimize', 'Summarize → Optimize');
                this.app.logDebug('optimize.complete', { finalStatus: 'Progress hidden, operation complete' });
            }, 1000);
        }
    }

    /**
     * Send a chat message
     */
    async send() {
        const provider = this.getFormValue('#provider') || this.app.settings?.default_provider || 'anthropic';
        const model = this.getFormValue('#model') || '';
        const userPrompt = this.getFormValue('#userPrompt');
        const optimizedPrompt = this.getFormValue('#optimizedPrompt') || userPrompt;

        // Show progress
        this.showProgress('#sendProgress', '#sendStatus', '#sendProgressBar', '#sendText', '#btnSend');
        
        try {
            // Simulate progress steps with detailed logging
            this.app.logDebug('send.start', { userPrompt, optimizedPrompt, provider, model });
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 10, 'Fetching fresh data...');
            this.app.logDebug('send.progress', { step: 'fetching_fresh_data', percent: 10, status: 'Fetching fresh data...' });
            await this.delay(200);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 30, 'Building optimized prompt...');
            this.app.logDebug('send.progress', { step: 'building_optimized_prompt', percent: 30, status: 'Building optimized prompt...' });
            await this.delay(200);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 50, 'Sending to AI provider...');
            this.app.logDebug('send.progress', { step: 'sending_to_ai_provider', percent: 50, status: 'Sending to AI provider...' });
            await this.delay(200);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 70, 'Processing response...');
            this.app.logDebug('send.progress', { step: 'processing_response', percent: 70, status: 'Processing response...' });
            await this.delay(200);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 80, 'Building request...');
            this.app.logDebug('send.progress', { step: 'building_request', percent: 80, status: 'Building request...' });
            await this.delay(200);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 85, 'Sending to AI provider...');
            this.app.logDebug('send.progress', { step: 'sending_to_ai_provider_api', percent: 85, status: 'Sending to AI provider...' });
            
            const requestBody = { provider, model, user_prompt: userPrompt, optimized_prompt: optimizedPrompt };
            this.app.logDebug('send.request', { url: '/api/chat', method: 'POST', body: requestBody });
            
            // Simulate MCP calls progress
            this.updateProgress('#sendProgressBar', '#sendStatus', 87, 'Calling GitHub MCP...');
            this.app.logDebug('send.progress', { step: 'calling_github_mcp', percent: 87, status: 'Calling GitHub MCP...' });
            await this.delay(150);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 89, 'Calling PostgreSQL MCP...');
            this.app.logDebug('send.progress', { step: 'calling_postgresql_mcp', percent: 89, status: 'Calling PostgreSQL MCP...' });
            await this.delay(150);
            
                         this.updateProgress('#sendProgressBar', '#sendStatus', 91, 'Sending to LLM...');
             this.app.logDebug('send.progress', { step: 'sending_to_llm', percent: 91, status: 'Sending to LLM...' });
             
             // Start periodic usage updates during send operation
             const sendUsageUpdateInterval = setInterval(() => {
                 this.updateProviderUsageDisplay(provider, 0, 0);
             }, 1000); // Update every second
             
             const response = await fetch('/api/chat', {
                 method: 'POST',
                 headers: { 'Content-Type': 'application/json' },
                 body: JSON.stringify(requestBody)
             });
             
             // Clear the interval after response
             clearInterval(sendUsageUpdateInterval);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 95, 'Parsing response...');
            this.app.logDebug('send.progress', { step: 'parsing_response', percent: 95, status: 'Parsing response...', statusCode: response.status });
            await this.delay(200);
            
            this.updateProgress('#sendProgressBar', '#sendStatus', 100, 'Complete!');
            this.app.logDebug('send.progress', { step: 'complete', percent: 100, status: 'Complete!' });
            await this.delay(200);
            
            const data = await response.json();
            this.app.logDebug('send.response', { status: response.status, data: data });

                         this.addToConversation(userPrompt, data.structured || data.text || "(no response)");
             
             // Final usage update after send operation
             this.updateProviderUsageDisplay(provider, 0, 0);

            this.app.logDebug('send.conversation', { 
                userMessage: userPrompt, 
                botResponse: data.structured || data.text || "(no response)",
                conversationLength: document.getElementById('conversation')?.children?.length || 0
            });

            // Track usage for send
            if (data.usage_tracking) {
                this.trackUsage(provider, data.usage_tracking);
            }

            // Rich debug
            this.app.debugManager.renderDebug(data.debug);
            this.app.logDebug('send.success', { 
                structured: data.structured, 
                text: data.text, 
                debug: data.debug 
            });
            this.app.activateTab('debug');
            
        } catch (error) {
            this.updateProgress('#sendProgressBar', '#sendStatus', 100, 'Error occurred');
            this.app.logDebug('send.error', { error: error.message, stack: error.stack });
            console.error('Send error:', error);
        } finally {
            // Hide progress after a short delay
            setTimeout(() => {
                this.hideProgress('#sendProgress', '#sendStatus', '#sendText', '#btnSend', 'Send');
                this.app.logDebug('send.complete', { finalStatus: 'Progress hidden, operation complete' });
            }, 1000);
        }
    }

    /**
     * Add message to conversation
     */
    addToConversation(userMessage, botResponse) {
        const conversation = document.getElementById('conversation');
        if (!conversation) return;

        const userDiv = document.createElement('div');
        userDiv.className = "p-3 rounded-lg bg-slate-100 border border-slate-200";
        userDiv.innerHTML = `<div class="font-medium text-slate-700 mb-1">👤 You:</div><div class="text-slate-800">${this.escapeHtml(userMessage)}</div>`;

        const botDiv = document.createElement('div');
        botDiv.className = "p-3 rounded-lg bg-blue-50 border border-blue-200";
        
        // Check if response is JSON and format it
        const formattedResponse = this.formatResponse(botResponse);
        
        botDiv.innerHTML = `<div class="font-medium text-blue-700 mb-1">🤖 Assistant:</div><div class="text-blue-800">${formattedResponse}</div>`;

        conversation.appendChild(userDiv);
        conversation.appendChild(botDiv);
        conversation.scrollTop = conversation.scrollHeight;
    }

    /**
     * Clear conversation history
     */
    clearConversation() {
        const conversation = document.getElementById('conversation');
        if (conversation) {
            conversation.innerHTML = '';
        }
    }

    /**
     * Show progress indicator
     */
    showProgress(progressId, statusId, progressBarId, textId, buttonId) {
        const elements = {
            progress: document.querySelector(progressId),
            status: document.querySelector(statusId),
            button: document.querySelector(buttonId),
            text: document.querySelector(textId)
        };

        if (elements.progress) elements.progress.classList.remove('hidden');
        if (elements.status) elements.status.classList.remove('hidden');
        if (elements.button) elements.button.disabled = true;
        if (elements.text) elements.text.textContent = 'Processing...';

        this.app.logDebug('progress.show', { 
            progressId, 
            statusId, 
            progressBarId, 
            textId, 
            buttonId,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Update progress indicator
     */
    updateProgress(progressBarId, statusId, percent, status) {
        const progressBar = document.querySelector(progressBarId);
        const statusElement = document.querySelector(statusId);

        if (progressBar) progressBar.style.width = `${percent}%`;
        if (statusElement) statusElement.textContent = status;

        this.app.logDebug('progress.update', { 
            progressBarId, 
            statusId, 
            percent, 
            status,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Hide progress indicator
     */
    hideProgress(progressId, statusId, textId, buttonId, originalText) {
        const elements = {
            progress: document.querySelector(progressId),
            status: document.querySelector(statusId),
            button: document.querySelector(buttonId),
            text: document.querySelector(textId)
        };

        if (elements.progress) elements.progress.classList.add('hidden');
        if (elements.status) elements.status.classList.add('hidden');
        if (elements.button) elements.button.disabled = false;
        if (elements.text) elements.text.textContent = originalText;

        // Reset progress bar width
        const progressBar = elements.progress?.querySelector('div');
        if (progressBar) {
            progressBar.style.width = '0%';
        }

        this.app.logDebug('progress.hide', { 
            progressId, 
            statusId, 
            textId, 
            buttonId, 
            originalText,
            timestamp: new Date().toISOString()
        });
    }

    /**
     * Helper method to get form value
     */
    getFormValue(selector) {
        const element = document.querySelector(selector);
        return element ? element.value : '';
    }

    /**
     * Helper method to set form value
     */
    setFormValue(selector, value) {
        const element = document.querySelector(selector);
        if (element) {
            element.value = value;
        }
    }

    /**
     * Helper method for delays
     */
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Format response content (detect and format JSON)
     */
    formatResponse(response) {
        // Handle null/undefined response
        if (!response) {
            return this.escapeHtml('(no response)');
        }

        // If response is already an object, format it directly
        if (typeof response === 'object') {
            return this.formatJsonResponse(response);
        }

        // If response is a string, process it
        if (typeof response === 'string') {
            const trimmedResponse = response.trim();
            
            // Check if it starts with { and ends with } (likely JSON)
            if (trimmedResponse.startsWith('{') && trimmedResponse.endsWith('}')) {
                try {
                    const parsed = JSON.parse(trimmedResponse);
                    return this.formatJsonResponse(parsed);
                } catch (e) {
                    // Not valid JSON, treat as regular text
                    return this.escapeHtml(response);
                }
            }
            
            // Check if it contains JSON blocks (like ```json)
            if (trimmedResponse.includes('```json')) {
                return this.formatCodeBlocks(response);
            }
            
            // Regular text response
            return this.escapeHtml(response);
        }

        // Fallback for other types
        return this.escapeHtml(String(response));
    }

    /**
     * Format JSON response with proper structure
     */
    formatJsonResponse(jsonData) {
        if (!jsonData || typeof jsonData !== 'object') {
            return this.escapeHtml(JSON.stringify(jsonData, null, 2));
        }

        let html = '<div class="space-y-3">';
        
        // Handle answer field specially
        if (jsonData.answer) {
            html += `<div class="bg-white p-3 rounded border border-gray-200">
                <div class="font-semibold text-gray-800 mb-2">📄 Analysis:</div>
                <div class="prose prose-sm max-w-none">${this.formatMarkdown(jsonData.answer)}</div>
            </div>`;
        }
        
        // Handle text field (fallback for simple responses)
        if (jsonData.text && !jsonData.answer) {
            html += `<div class="bg-white p-3 rounded border border-gray-200">
                <div class="font-semibold text-gray-800 mb-2">💬 Response:</div>
                <div class="prose prose-sm max-w-none">${this.formatMarkdown(jsonData.text)}</div>
            </div>`;
        }
        
        // Handle structured field (main response content)
        if (jsonData.structured && !jsonData.answer && !jsonData.text) {
            if (typeof jsonData.structured === 'string') {
                html += `<div class="bg-white p-3 rounded border border-gray-200">
                    <div class="font-semibold text-gray-800 mb-2">📋 Structured Response:</div>
                    <div class="prose prose-sm max-w-none">${this.formatMarkdown(jsonData.structured)}</div>
                </div>`;
            } else if (typeof jsonData.structured === 'object') {
                html += `<div class="bg-white p-3 rounded border border-gray-200">
                    <div class="font-semibold text-gray-800 mb-2">📋 Structured Response:</div>
                    <pre class="text-xs text-gray-600 overflow-x-auto">${this.escapeHtml(JSON.stringify(jsonData.structured, null, 2))}</pre>
                </div>`;
            }
        }
        
        // Handle used_connectors
        if (jsonData.used_connectors && Array.isArray(jsonData.used_connectors) && jsonData.used_connectors.length > 0) {
            html += `<div class="bg-green-50 p-3 rounded border border-green-200">
                <div class="font-semibold text-green-800 mb-2">🔗 Used Connectors:</div>
                <div class="flex flex-wrap gap-2">${jsonData.used_connectors.map(connector => 
                    `<span class="px-2 py-1 bg-green-100 text-green-800 rounded-full text-sm">${connector}</span>`
                ).join('')}</div>
            </div>`;
        }
        
        // Handle citations
        if (jsonData.citations && Array.isArray(jsonData.citations) && jsonData.citations.length > 0) {
            html += `<div class="bg-purple-50 p-3 rounded border border-purple-200">
                <div class="font-semibold text-purple-800 mb-2">📚 Citations:</div>
                <div class="space-y-1">${jsonData.citations.map(citation => 
                    `<div class="text-sm"><a href="${citation}" target="_blank" class="text-purple-600 hover:text-purple-800 underline">${citation}</a></div>`
                ).join('')}</div>
            </div>`;
        }
        
        // Handle any other fields
        const otherFields = Object.keys(jsonData).filter(key => 
            !['answer', 'text', 'structured', 'used_connectors', 'citations'].includes(key)
        );
        
        if (otherFields.length > 0) {
            html += `<div class="bg-gray-50 p-3 rounded border border-gray-200">
                <div class="font-semibold text-gray-800 mb-2">📋 Additional Data:</div>
                <pre class="text-xs text-gray-600 overflow-x-auto">${this.escapeHtml(JSON.stringify(jsonData, null, 2))}</pre>
            </div>`;
        }
        
        html += '</div>';
        return html;
    }

    /**
     * Format markdown content (basic implementation)
     */
    formatMarkdown(markdown) {
        if (!markdown) return '';
        
        return markdown
            // Headers
            .replace(/^### (.*$)/gim, '<h3 class="text-lg font-semibold text-gray-800 mt-4 mb-2">$1</h3>')
            .replace(/^## (.*$)/gim, '<h2 class="text-xl font-bold text-gray-900 mt-6 mb-3">$1</h2>')
            .replace(/^# (.*$)/gim, '<h1 class="text-2xl font-bold text-gray-900 mt-6 mb-4">$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>')
            // Code blocks
            .replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre class="bg-gray-100 p-3 rounded text-sm overflow-x-auto my-3"><code>$2</code></pre>')
            // Inline code
            .replace(/`([^`]+)`/g, '<code class="bg-gray-100 px-1 py-0.5 rounded text-sm">$1</code>')
            // Lists
            .replace(/^\* (.*$)/gim, '<li class="ml-4">$1</li>')
            .replace(/^- (.*$)/gim, '<li class="ml-4">$1</li>')
            // Line breaks
            .replace(/\n/g, '<br>');
    }

    /**
     * Format code blocks in response
     */
    formatCodeBlocks(response) {
        return response.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            const language = lang || 'text';
            return `<pre class="bg-gray-100 p-3 rounded text-sm overflow-x-auto my-3 border border-gray-200">
                <div class="text-xs text-gray-500 mb-2 font-mono">${language}</div>
                <code class="text-gray-800">${this.escapeHtml(code)}</code>
            </pre>`;
        });
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Update debug information when provider/model changes
     */
    updateDebugInfo() {
        if (!this.app || !this.app.debugManager) return;
        
        const providerSelect = document.getElementById('provider');
        const modelSelect = document.getElementById('model');
        
        if (!providerSelect || !modelSelect) return;
        
        const selectedProvider = providerSelect.value;
        const selectedModel = modelSelect.value;
        
        // Get provider configuration
        const providers = this.app.settings?.providers || {};
        const providerConfig = providers[selectedProvider];
        
        if (providerConfig) {
            // Create debug info with current selection
            const debugInfo = {
                provider: {
                    name: providerConfig.name || selectedProvider,
                    model: selectedModel,
                    endpoint: providerConfig.base_url || 'Not configured',
                    temperature: providerConfig.temperature || 0.2
                },
                mcp: {
                    github: {
                        enabled: this.app.settings?.mcp?.github?.enabled || false,
                        repo: this.app.settings?.mcp?.github?.repo || 'Not configured',
                        url: this.app.settings?.mcp?.github?.url || 'Not configured',
                        tools: ['GitHub Issues', 'GitHub Comments'],
                        calls: []
                    },
                    postgres: {
                        enabled: this.app.settings?.mcp?.postgres?.enabled || false,
                        sql: this.app.settings?.mcp?.postgres?.sample_sql || 'Not configured',
                        url: this.app.settings?.mcp?.postgres?.url || 'Not configured',
                        tools: ['PostgreSQL Queries', 'Research Papers'],
                        calls: []
                    }
                },
                optimizer: {
                    provider: selectedProvider,
                    model: selectedModel,
                    temperature: providerConfig.temperature || 0.2
                }
            };
            
            // Update debug panel
            this.app.debugManager.renderDebug(debugInfo);
        }
    }
}

// Export for use in other modules
window.ChatManager = ChatManager;
