# Session Data Information - MCP Clients Playground

## Overview

The `session-data/` folder is a dedicated directory for storing session-related information, user data, and temporary files generated during MCP playground usage. This folder helps maintain state across sessions and provides a centralized location for data persistence.

## Purpose

### Primary Functions
- **Session Persistence**: Store user preferences, settings, and session state
- **Data Caching**: Cache frequently accessed data to improve performance
- **Temporary Storage**: Store intermediate results and processing artifacts
- **User Data**: Maintain user-specific configurations and history
- **Debug Information**: Store logs and debugging data for troubleshooting

## Folder Structure

```
session-data/
├── session-info.md           # This file - documentation and information
├── settings.json             # Current session settings
├── settings-*.json           # Session-specific settings files
├── logs/                     # Application logs and debugging (MOVED from extended/)
│   ├── session_*.log         # Session-specific log files
│   ├── debug_*.log           # Debug log files
│   ├── mcp-calls.log         # MCP connector call logs
│   ├── error-logs.log        # Error and exception logs
│   └── performance.log       # Performance metrics
├── user-sessions/            # User-specific session data
│   ├── session-001/          # Individual session directories
│   ├── session-002/
│   └── ...
├── cache/                    # Cached data for performance
│   ├── github-data/          # Cached GitHub API responses
│   ├── postgres-data/        # Cached PostgreSQL query results
│   └── ai-responses/         # Cached AI provider responses
├── temp/                     # Temporary files
│   ├── uploads/              # Temporary file uploads
│   ├── exports/              # Temporary export files
│   └── processing/           # Intermediate processing files
└── config/                   # Configuration files
    ├── user-preferences.json # User preference settings
    ├── mcp-config.json       # MCP connector configurations
    └── playground-settings.json # Playground-specific settings
```

## Data Types Stored

### 1. Session Information
- **User Sessions**: Individual user session data and preferences
- **Session State**: Current state of user interactions
- **Session History**: Historical session data for analysis
- **User Preferences**: Customized settings and configurations

### 2. Cached Data
- **GitHub Data**: Cached responses from GitHub API calls
- **PostgreSQL Data**: Cached database query results
- **AI Responses**: Cached responses from AI providers
- **MCP Tool Lists**: Cached available MCP tools and capabilities

### 3. Logging Data (Centralized)
- **Session Logs**: Individual session log files (session_*.log)
- **Debug Logs**: Detailed debug information (debug_*.log)
- **MCP Call Logs**: Detailed logs of all MCP connector interactions
- **Error Logs**: Error tracking and debugging information
- **Performance Logs**: Timing and performance metrics
- **User Activity Logs**: User interaction and behavior tracking

### 4. Configuration Data
- **User Preferences**: Individual user settings and customizations
- **MCP Configurations**: Connector settings and authentication data
- **Playground Settings**: Application-specific configurations
- **Template Data**: Saved prompt templates and configurations

## Usage Guidelines

### For Basic Playground
- **Minimal Storage**: Stores essential session data only
- **Simple Caching**: Basic caching for GitHub and PostgreSQL data
- **Basic Logging**: Essential error and performance logging
- **User Preferences**: Simple user preference storage

### For Extended Playground
- **Comprehensive Storage**: Full session state and history
- **Advanced Caching**: Multi-level caching with intelligent invalidation
- **Detailed Logging**: Comprehensive logging with multiple levels (now centralized in session-data/logs)
- **Rich Configuration**: Advanced user preferences and settings

## Data Management

### Privacy and Security
- **Local Storage**: All data stored locally on user's machine
- **No External Sharing**: Data never transmitted to external servers
- **User Control**: Users can clear data at any time
- **Secure Storage**: Sensitive data (tokens, keys) encrypted when stored

### Data Retention
- **Session Data**: Retained for current session only
- **Cache Data**: Automatically cleared based on age and usage
- **Log Data**: Retained for debugging and analysis (configurable)
- **User Preferences**: Persisted across sessions until manually cleared

### Cleanup and Maintenance
- **Automatic Cleanup**: Old cache and temporary files automatically removed
- **Manual Cleanup**: Users can manually clear specific data types
- **Storage Monitoring**: Built-in storage usage monitoring
- **Data Export**: Users can export their data for backup

## Integration with Playgrounds

### Basic Playground Integration
```python
# Example: Basic session data usage
session_data = {
    "user_id": "user_123",
    "current_session": "session_001",
    "preferences": {
        "theme": "light",
        "language": "en"
    },
    "cache": {
        "github_issues": {...},
        "postgres_queries": {...}
    }
}
```

### Extended Playground Integration
```python
# Example: Extended session data usage with centralized logging
session_data = {
    "user_id": "user_123",
    "current_session": "session_001",
    "session_history": [...],
    "preferences": {
        "theme": "dark",
        "language": "en",
        "ai_provider": "anthropic",
        "debug_mode": True,
        "logging_level": "detailed"
    },
    "cache": {
        "github_issues": {...},
        "postgres_queries": {...},
        "ai_responses": {...},
        "mcp_tools": {...}
    },
    "analytics": {
        "usage_stats": {...},
        "performance_metrics": {...},
        "error_tracking": {...}
    },
    "logs": {
        "session_log": "session-data/logs/session_001.log",
        "debug_log": "session-data/logs/debug_001.log"
    }
}
```

## Logging Structure (Updated)

### Centralized Logging
All logs are now stored in `session-data/logs/` directory:

```
session-data/logs/
├── session_1305d397-ca81-4ea8-8d4d-796a72a29d8b.log  # Session-specific logs
├── debug_1305d397-ca81-4ea8-8d4d-796a72a29d8b.log    # Debug logs for session
├── mcp-calls.log                                      # MCP connector interactions
├── error-logs.log                                     # Error tracking
└── performance.log                                    # Performance metrics
```

### Log File Formats
- **Session Logs**: `session_{session_id}.log` - Main session activity
- **Debug Logs**: `debug_{session_id}.log` - Detailed debugging information
- **System Logs**: General application logs (mcp-calls.log, error-logs.log, etc.)

### Log Content Examples
```
2025-08-22 06:26:38 [INFO] session_1305d397-ca81-4ea8-8d4d-796a72a29d8b: === SESSION STARTED ===
2025-08-22 06:26:39 [INFO] session_1305d397-ca81-4ea8-8d4d-796a72a29d8b: [MCP] Connecting to GITHUB
2025-08-22 06:26:40 [INFO] session_1305d397-ca81-4ea8-8d4d-796a72a29d8b: [LLM] Request to ANTHROPIC
2025-08-22 06:26:41 [DEBUG] session_1305d397-ca81-4ea8-8d4d-796a72a29d8b: [DEBUG] Session settings loaded
```

## Best Practices

### For Developers
1. **Use Appropriate Storage**: Choose the right storage location for different data types
2. **Implement Cleanup**: Always implement proper cleanup mechanisms
3. **Handle Errors**: Gracefully handle storage errors and failures
4. **Respect Privacy**: Never store sensitive data without encryption
5. **Monitor Usage**: Track storage usage and implement limits
6. **Centralized Logging**: Use the session-data/logs directory for all logging

### For Users
1. **Regular Cleanup**: Periodically clear old session data
2. **Backup Important Data**: Export important configurations
3. **Monitor Storage**: Keep an eye on storage usage
4. **Report Issues**: Report any data-related issues or concerns
5. **Log Management**: Clear old log files to save space

## Troubleshooting

### Common Issues
- **Storage Full**: Clear cache and temporary files
- **Corrupted Data**: Reset session data and restart
- **Permission Errors**: Check folder permissions
- **Performance Issues**: Clear old cache data
- **Log File Issues**: Check session-data/logs directory for log files

### Recovery Options
- **Session Reset**: Clear all session data and start fresh
- **Selective Clear**: Clear specific data types only
- **Data Export**: Export data before clearing
- **Configuration Reset**: Reset to default configurations
- **Log Cleanup**: Clear old log files in session-data/logs/

## Recent Changes

### Logs Directory Migration
- **Previous**: Logs stored in `playgrounds/extended/logs/`
- **Current**: Logs centralized in `playgrounds/session-data/logs/`
- **Benefits**: 
  - Centralized logging for all playgrounds
  - Better organization and management
  - Easier backup and cleanup
  - Consistent structure across playgrounds

### Updated Code References
- **Logging Service**: Updated to use `session-data/logs/` directory
- **API Endpoints**: Continue to work with new structure
- **JavaScript**: No changes needed (uses API endpoints)
- **Configuration**: Updated to reflect new paths

## Future Enhancements

### Planned Features
- **Cloud Sync**: Optional cloud synchronization of user data
- **Advanced Analytics**: Enhanced usage analytics and insights
- **Data Compression**: Automatic compression of stored data
- **Backup Integration**: Integration with external backup services
- **Multi-User Support**: Support for multiple user profiles
- **Log Rotation**: Automatic log file rotation and archiving

### Development Roadmap
1. **Phase 1**: Basic session data management ✅
2. **Phase 2**: Advanced caching and optimization ✅
3. **Phase 3**: Centralized logging system ✅
4. **Phase 4**: Cloud sync and backup features
5. **Phase 5**: Advanced analytics and insights

## Conclusion

The `session-data/` folder is a crucial component of the MCP Clients Playground, providing essential data persistence, caching, and logging capabilities. With the recent migration of logs to the centralized `session-data/logs/` directory, the system now provides better organization, easier management, and consistent structure across all playgrounds while respecting user privacy and data security.

For more information about specific playground implementations, see the main `sample-outputs.md` file in the playgrounds directory.
