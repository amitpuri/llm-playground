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
