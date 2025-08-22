"""
Refactored Flask application using SOLID principles and modular architecture.
"""
import os
import asyncio
import uuid
import glob
import time
from flask import Flask, render_template, request, jsonify, session
from dotenv import load_dotenv

from core.settings import FileSettingsRepository, SettingsManager
from core.chat_service import ChatService, ChatSessionManager
from core.logging_service import logging_service
from core.token_calculator import token_calculator

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Initialize core services
settings_repository = FileSettingsRepository(
    os.getenv("PLAYGROUND_SETTINGS_PATH", "../session-data/settings.json")
)
settings_manager = SettingsManager(settings_repository)
chat_session_manager = ChatSessionManager()

# Get default chat service
default_chat_service = ChatService(settings_manager)


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


def get_session_settings_repository():
    """Get or create session-specific settings repository."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        print(f"Created new session: {session['session_id']}")
    
    session_id = session['session_id']
    session_settings_path = f"../session-data/settings-{session_id}.json"
    
    return FileSettingsRepository(session_settings_path)


def get_session_settings_manager():
    """Get session-specific settings manager."""
    session_repo = get_session_settings_repository()
    return SettingsManager(session_repo)


@app.route("/")
def index():
    """Render the main application page."""
    # Clean up old session files on each request (optional)
    cleanup_old_session_files()
    
    # Get or create session logger
    session_id = session.get('session_id', str(uuid.uuid4()))
    session['session_id'] = session_id
    logger = logging_service.get_logger(session_id)
    logger.log_info("Application started - main page loaded")
    
    return render_template("index.html")


@app.route("/test")
def test():
    """Test page for debugging."""
    return render_template("test_token_api.html")


@app.get("/api/settings")
def api_get_settings():
    """Get current application settings."""
    session_settings_manager = get_session_settings_manager()
    settings = session_settings_manager.get_settings()
    
    # Get session logger
    session_id = session.get('session_id', str(uuid.uuid4()))
    logger = logging_service.get_logger(session_id)
    
    # Debug logging
    logger.log_info("Settings API called")
    logger.log_debug(f"Session settings loaded: anthropic_enabled={settings.providers['anthropic'].enabled}, github_enabled={settings.mcp['github']['enabled']}, postgres_enabled={settings.mcp['postgres']['enabled']}")
    
    response_data = {
        "providers": {k: v.to_dict() for k, v in settings.providers.items()},
        "mcp": settings.mcp,
        "optimizer": settings.optimizer.to_dict(),
        "default_provider": settings.default_provider,
    }
    
    logger.log_api_response("/api/settings", response_data)
    
    return jsonify(response_data)


@app.post("/api/settings")
def api_set_settings():
    """Update application settings."""
    data = request.get_json(force=True)
    session_settings_manager = get_session_settings_manager()
    updated_settings = session_settings_manager.update_settings(data)
    
    return jsonify({"ok": True})


@app.post("/api/optimize")
def api_optimize():
    """Optimize a user prompt using MCP context."""
    data = request.get_json(force=True)
    user_prompt = (data.get("user_prompt") or "").strip()
    provider = (data.get("provider") or "anthropic").strip()
    
    # Get session logger
    session_id = session.get('session_id', str(uuid.uuid4()))
    logger = logging_service.get_logger(session_id)
    
    logger.log_api_call("/api/optimize", "POST", {"user_prompt": user_prompt[:200], "provider": provider})
    
    try:
        result = asyncio.run(default_chat_service.optimize_prompt(user_prompt, provider, logger))
        
        # Get usage information for the optimization
        session_settings_manager = get_session_settings_manager()
        usage_info = session_settings_manager.get_provider_usage(provider)
        
        result["usage_tracking"] = usage_info
        
        logger.log_optimization(user_prompt, result.get("optimized_prompt", ""), result.get("debug", {}))
        logger.log_api_response("/api/optimize", result)
        
        return jsonify(result)
    except Exception as e:
        logger.log_error(f"Optimization failed: {str(e)}")
        return jsonify({
            "optimized_prompt": user_prompt,
            "debug": {"error": str(e)}
        }), 500


@app.post("/api/chat")
def api_chat():
    """Send a chat message and get a response."""
    data = request.get_json(force=True)
    provider = data.get("provider", "anthropic")
    model = data.get("model")
    user_prompt = (data.get("user_prompt") or "").strip()
    
    # Get session logger
    session_id = session.get('session_id', str(uuid.uuid4()))
    logger = logging_service.get_logger(session_id)
    
    logger.log_api_call("/api/chat", "POST", {"user_prompt": user_prompt[:200], "provider": provider, "model": model})
    
    try:
        response = asyncio.run(default_chat_service.send_message(user_prompt, provider, model))
        
        # Get usage information for the response
        session_settings_manager = get_session_settings_manager()
        usage_info = session_settings_manager.get_provider_usage(provider)
        
        response_data = {
            "text": response.text,
            "structured": response.structured,
            "debug": response.debug,
            "usage_tracking": usage_info
        }
        
        logger.log_llm_response(provider, response.text)
        logger.log_api_response("/api/chat", response_data)
        
        return jsonify(response_data)
    except Exception as e:
        logger.log_error(f"Chat failed: {str(e)}")
        return jsonify({
            "text": f"Error: {e}",
            "structured": json.dumps({"answer": f"Error: {e}", "used_connectors": [], "citations": []}),
            "debug": {"error": str(e)}
        }), 500


@app.get("/api/conversation")
def api_get_conversation():
    """Get the current conversation history."""
    history = default_chat_service.get_conversation_history()
    return jsonify([msg.to_dict() for msg in history])


@app.post("/api/conversation/clear")
def api_clear_conversation():
    """Clear the conversation history."""
    default_chat_service.clear_history()
    return jsonify({"ok": True})


@app.get("/api/usage/<provider_key>")
def api_get_usage(provider_key):
    """Get usage information for a specific provider."""
    session_settings_manager = get_session_settings_manager()
    
    try:
        usage_info = session_settings_manager.get_provider_usage(provider_key)
        if usage_info is None:
            return jsonify({"error": "Provider not found"}), 404
        
        return jsonify(usage_info)
    except Exception as e:
        print(f"Usage get error: {e}")
        return jsonify({"error": str(e)}), 500


@app.post("/api/usage/update")
def api_update_usage():
    """Update usage for a specific provider."""
    data = request.get_json(force=True)
    session_settings_manager = get_session_settings_manager()
    
    try:
        success = session_settings_manager.update_provider_usage(
            provider_key=data.get("provider"),
            user_tokens=data.get("user_tokens", 0),
            optimized_tokens=data.get("optimized_tokens", 0),
            response_tokens=data.get("response_tokens", 0),
            api_calls=data.get("api_calls", 1)
        )
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "usage_cap_exceeded"}), 400
    except Exception as e:
        print(f"Usage update error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.post("/api/usage/reset/<provider_key>")
def api_reset_usage(provider_key):
    """Reset usage for a specific provider."""
    session_settings_manager = get_session_settings_manager()
    
    try:
        success = session_settings_manager.reset_provider_usage(provider_key)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Provider not found"}), 404
    except Exception as e:
        print(f"Usage reset error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


# Log Management API Endpoints
@app.get("/api/logs/session/<session_id>")
def api_get_session_logs(session_id):
    """Get logs for a specific session."""
    try:
        logs = logging_service.get_session_logs(session_id)
        return jsonify({"session_id": session_id, "logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/logs/current")
def api_get_current_session_logs():
    """Get logs for the current session."""
    session_id = session.get('session_id', str(uuid.uuid4()))
    try:
        logs = logging_service.get_session_logs(session_id)
        return jsonify({"session_id": session_id, "logs": logs})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/logs/recent/<session_id>")
def api_get_recent_logs(session_id):
    """Get recent logs for a specific session."""
    lines = request.args.get('lines', 100, type=int)
    try:
        logs = logging_service.get_recent_logs(session_id, lines)
        return jsonify({"session_id": session_id, "logs": logs, "lines": lines})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/logs/clear/<session_id>")
def api_clear_session_logs(session_id):
    """Clear logs for a specific session."""
    try:
        logging_service.clear_session_logs(session_id)
        return jsonify({"success": True, "session_id": session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/logs/sessions")
def api_get_all_sessions():
    """Get all available session IDs."""
    try:
        session_ids = logging_service.get_all_session_ids()
        return jsonify({"sessions": session_ids})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/logs/session-id")
def api_get_current_session_id():
    """Get the current session ID."""
    session_id = session.get('session_id', str(uuid.uuid4()))
    return jsonify({"session_id": session_id})


# Token Calculation API Endpoints
@app.post("/api/tokens/count")
def api_count_tokens():
    """Count tokens for a given text and provider."""
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    provider = data.get("provider", "openai")
    model = data.get("model")
    
    # Get session logger
    session_id = session.get('session_id', str(uuid.uuid4()))
    logger = logging_service.get_logger(session_id)
    
    logger.log_api_call("/api/tokens/count", "POST", {
        "text_length": len(text),
        "provider": provider,
        "model": model
    })
    
    try:
        token_count = token_calculator.count_tokens(text, provider, model)
        
        result = {
            "input_tokens": token_count.input_tokens,
            "output_tokens": token_count.output_tokens,
            "total_tokens": token_count.total_tokens,
            "characters": token_count.characters,
            "words": token_count.words,
            "estimated_cost": token_count.estimated_cost,
            "model": token_count.model,
            "provider": token_count.provider
        }
        
        logger.log_api_response("/api/tokens/count", result)
        return jsonify(result)
    except Exception as e:
        logger.log_error(f"Token counting failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.post("/api/tokens/analyze")
def api_analyze_text():
    """Comprehensive text analysis with token counts for specified providers."""
    data = request.get_json(force=True)
    text = data.get("text", "").strip()
    providers = data.get("providers", ["openai", "anthropic", "google"])
    
    # Get session logger
    session_id = session.get('session_id', str(uuid.uuid4()))
    logger = logging_service.get_logger(session_id)
    
    logger.log_api_call("/api/tokens/analyze", "POST", {
        "text_length": len(text),
        "providers": providers
    })
    
    try:
        analysis = token_calculator.analyze_text(text, providers)
        logger.log_api_response("/api/tokens/analyze", analysis)
        return jsonify(analysis)
    except Exception as e:
        logger.log_error(f"Text analysis failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.get("/api/tokens/models/<provider>")
def api_get_models(provider):
    """Get available models for a specific provider."""
    try:
        models = token_calculator.get_available_models(provider)
        return jsonify({"provider": provider, "models": models})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/tokens/model-info/<provider>/<model>")
def api_get_model_info(provider, model):
    """Get detailed information about a specific model."""
    try:
        model_info = token_calculator.get_model_info(provider, model)
        if model_info:
            return jsonify(model_info)
        else:
            return jsonify({"error": "Model not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.post("/api/tokens/estimate-cost")
def api_estimate_cost():
    """Estimate cost for a complete request."""
    data = request.get_json(force=True)
    input_tokens = data.get("input_tokens", 0)
    output_tokens = data.get("output_tokens", 0)
    provider = data.get("provider", "openai")
    model = data.get("model")
    
    try:
        cost = token_calculator.estimate_cost(input_tokens, output_tokens, provider, model)
        return jsonify({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "provider": provider,
            "model": model,
            "estimated_cost": cost
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.get("/api/tokens/settings")
def api_get_token_settings():
    """Get settings for token calculator (enabled providers and their default models)."""
    try:
        session_settings_manager = get_session_settings_manager()
        settings = session_settings_manager.get_settings()
        
        # Get session logger
        session_id = session.get('session_id', str(uuid.uuid4()))
        logger = logging_service.get_logger(session_id)
        
        # Build provider settings for token calculator
        token_settings = {
            "providers": {},
            "default_provider": None
        }
        
        # Add enabled providers with their default models
        for provider_key, provider_config in settings.providers.items():
            if provider_config.enabled:
                token_settings["providers"][provider_key] = {
                    "name": provider_config.name,
                    "default_model": provider_config.default_model,
                    "enabled": provider_config.enabled
                }
                # Set first enabled provider as default
                if token_settings["default_provider"] is None:
                    token_settings["default_provider"] = provider_key
        
        logger.log_api_call("/api/tokens/settings", "GET", token_settings)
        return jsonify(token_settings)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1", 
        port=int(os.getenv("PORT", "5051")), 
        debug=True
    )
