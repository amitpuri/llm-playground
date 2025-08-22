"""
LangChain-based Flask application using SOLID principles and modular architecture.
"""
import os
import asyncio
import uuid
import glob
import time
from flask import Flask, render_template, request, jsonify, session

from core.container import ServiceContainer
from core.controllers import (
    ChatController, SettingsController, UsageController, 
    TokenController, LoggingController
)
from core.exceptions import LLMPlaygroundException

# Initialize Flask app
app = Flask(__name__)
app.secret_key = "dev-secret-key-change-in-production"

# Initialize dependency injection container
service_container = ServiceContainer("../session-data/settings.json")


def cleanup_old_session_files(max_age_hours=24):
    """Clean up old session settings files."""
    try:
        current_time = time.time()
        max_age_seconds = max_age_hours * 3600
        
        # Find all session settings files in session-data folder
        session_files = glob.glob("../session-data/settings-*.json")
        
        for file_path in session_files:
            file_age = current_time - os.path.getmtime(file_path)
            if file_age > max_age_seconds:
                os.remove(file_path)
                print(f"Cleaned up old session file: {file_path}")
    except Exception as e:
        print(f"Error cleaning up session files: {e}")


def get_session_container():
    """Get or create session-specific service container."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        print(f"Created new session: {session['session_id']}")
    
    session_id = session['session_id']
    return service_container.create_session_container(session_id)


@app.route("/")
def index():
    """Render the main application page."""
    # Clean up old session files on each request (optional)
    cleanup_old_session_files()
    
    # Get or create session container
    session_container = get_session_container()
    logger = session_container.get_logger()
    logger.log_info("Application started - main page loaded")
    
    return render_template("index.html")


@app.route("/test")
def test():
    """Test page for debugging."""
    return render_template("test_token_api.html")


@app.get("/api/settings")
def api_get_settings():
    """Get current application settings."""
    session_container = get_session_container()
    controller = SettingsController(session_container)
    
    result = controller.get_settings()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/settings")
def api_set_settings():
    """Update application settings."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = SettingsController(session_container)
    
    result = controller.update_settings(data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/optimize")
def api_optimize():
    """Optimize a user prompt using MCP context."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = ChatController(session_container)
    
    result = asyncio.run(controller.optimize_prompt(data))
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/chat")
def api_chat():
    """Send a chat message and get a response."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = ChatController(session_container)
    
    result = asyncio.run(controller.send_message(data))
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/conversation")
def api_get_conversation():
    """Get the current conversation history."""
    session_container = get_session_container()
    controller = ChatController(session_container)
    
    result = controller.get_conversation_history()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/conversation/clear")
def api_clear_conversation():
    """Clear the conversation history."""
    session_container = get_session_container()
    controller = ChatController(session_container)
    
    result = controller.clear_conversation()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/usage/<provider_key>")
def api_get_usage(provider_key):
    """Get usage information for a specific provider."""
    session_container = get_session_container()
    controller = UsageController(session_container)
    
    result = controller.get_usage(provider_key)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/usage/update")
def api_update_usage():
    """Update usage for a specific provider."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = UsageController(session_container)
    
    result = controller.update_usage(data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/usage/reset/<provider_key>")
def api_reset_usage(provider_key):
    """Reset usage for a specific provider."""
    session_container = get_session_container()
    controller = UsageController(session_container)
    
    result = controller.reset_usage(provider_key)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


# Log Management API Endpoints
@app.get("/api/logs/session/<session_id>")
def api_get_session_logs(session_id):
    """Get logs for a specific session."""
    session_container = get_session_container()
    controller = LoggingController(session_container)
    
    result = controller.get_session_logs(session_id)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/logs/current")
def api_get_current_session_logs():
    """Get logs for the current session."""
    session_container = get_session_container()
    controller = LoggingController(session_container)
    
    result = controller.get_current_session_logs()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/logs/recent/<session_id>")
def api_get_recent_logs(session_id):
    """Get recent logs for a specific session."""
    lines = request.args.get('lines', 100, type=int)
    session_container = get_session_container()
    controller = LoggingController(session_container)
    
    result = controller.get_recent_logs(session_id, lines)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/logs/clear/<session_id>")
def api_clear_session_logs(session_id):
    """Clear logs for a specific session."""
    session_container = get_session_container()
    controller = LoggingController(session_container)
    
    result = controller.clear_session_logs(session_id)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/logs/sessions")
def api_get_all_sessions():
    """Get all available session IDs."""
    session_container = get_session_container()
    controller = LoggingController(session_container)
    
    result = controller.get_all_sessions()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/logs/session-id")
def api_get_current_session_id():
    """Get the current session ID."""
    session_container = get_session_container()
    controller = LoggingController(session_container)
    
    result = controller.get_current_session_id()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


# Token Calculation API Endpoints
@app.post("/api/tokens/count")
def api_count_tokens():
    """Count tokens for a given text and provider."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = TokenController(session_container)
    
    result = controller.count_tokens(data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/tokens/analyze")
def api_analyze_text():
    """Comprehensive text analysis with token counts for specified providers."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = TokenController(session_container)
    
    result = controller.analyze_text(data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/tokens/models/<provider>")
def api_get_models(provider):
    """Get available models for a specific provider."""
    session_container = get_session_container()
    controller = TokenController(session_container)
    
    result = controller.get_models(provider)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/tokens/model-info/<provider>/<model>")
def api_get_model_info(provider, model):
    """Get detailed information about a specific model."""
    session_container = get_session_container()
    controller = TokenController(session_container)
    
    result = controller.get_model_info(provider, model)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.post("/api/tokens/estimate-cost")
def api_estimate_cost():
    """Estimate cost for a complete request."""
    data = request.get_json(force=True)
    session_container = get_session_container()
    controller = TokenController(session_container)
    
    result = controller.estimate_cost(data)
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


@app.get("/api/tokens/settings")
def api_get_token_settings():
    """Get settings for token calculator (enabled providers and their default models)."""
    session_container = get_session_container()
    controller = TokenController(session_container)
    
    result = controller.get_token_settings()
    if isinstance(result, tuple):
        return jsonify(result[0]), result[1]
    return jsonify(result)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1", 
        port=int(os.getenv("PORT", "5052")), 
        debug=True
    )
