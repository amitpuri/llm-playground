"""
Controllers for handling HTTP requests and coordinating between routes and services.
"""
import asyncio
from typing import Dict, Any, Optional, List
from .container import SessionServiceContainer
from .exceptions import (
    ValidationError, ChatServiceError, SessionError, 
    ProviderError, MCPError, UsageLimitError
)
from .validation import RequestValidator
from .models import ChatMessage


class BaseController:
    """Base controller with common functionality."""
    
    def __init__(self, session_container: SessionServiceContainer):
        self.session_container = session_container
        self.logger = session_container.get_logger()
        self.validator = RequestValidator()
    
    def _validate_required_fields(self, data: Dict[str, Any], required_fields: List[str]) -> None:
        """Validate that required fields are present in request data."""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValidationError(
                f"Missing required fields: {', '.join(missing_fields)}",
                details={"missing_fields": missing_fields}
            )
    
    def _log_api_call(self, endpoint: str, method: str, data: Dict[str, Any]) -> None:
        """Log API call details."""
        if self.logger:
            self.logger.log_api_call(endpoint, method, data)
    
    def _log_api_response(self, endpoint: str, response_data: Dict[str, Any]) -> None:
        """Log API response details."""
        if self.logger:
            self.logger.log_api_response(endpoint, response_data)
    
    def _handle_error(self, error: Exception, endpoint: str) -> Dict[str, Any]:
        """Handle and log errors."""
        if self.logger:
            self.logger.log_error(f"{endpoint} failed: {str(error)}")
        
        if isinstance(error, ValidationError):
            return {"error": "validation_error", "message": str(error), "details": error.details}, 400
        elif isinstance(error, UsageLimitError):
            return {"error": "usage_limit_exceeded", "message": str(error), "details": error.details}, 429
        elif isinstance(error, (ProviderError, MCPError)):
            return {"error": "service_error", "message": str(error), "details": error.details}, 503
        else:
            return {"error": "internal_error", "message": "An unexpected error occurred"}, 500


class ChatController(BaseController):
    """Controller for chat-related operations."""
    
    async def send_message(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chat message request."""
        self._log_api_call("/api/chat", "POST", request_data)
        
        try:
            # Validate request data
            self.validator.validate_chat_request(request_data)
            
            # Extract parameters
            provider = request_data.get("provider", "anthropic")
            model = request_data.get("model")
            user_prompt = request_data["user_prompt"].strip()
            
            # Get services
            chat_service = self.session_container.get_chat_service()
            settings_manager = self.session_container.get_settings_manager()
            
            # Send message
            response = await chat_service.send_message(
                user_prompt, provider, model, 
                self.session_container.session_id, self.logger
            )
            
            # Get usage information
            usage_info = settings_manager.get_provider_usage(provider)
            
            # Prepare response
            response_data = {
                "text": response.content,
                "structured": {
                    "answer": response.content, 
                    "used_connectors": [], 
                    "citations": []
                },
                "debug": response.debug_info,
                "usage_tracking": usage_info
            }
            
            self._log_api_response("/api/chat", response_data)
            return response_data
            
        except Exception as e:
            return self._handle_error(e, "/api/chat")
    
    async def optimize_prompt(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompt optimization request."""
        self._log_api_call("/api/optimize", "POST", request_data)
        
        try:
            # Validate request data
            self.validator.validate_optimize_request(request_data)
            
            # Extract parameters
            user_prompt = request_data["user_prompt"].strip()
            provider = request_data.get("provider", "anthropic")
            
            # Get services
            chat_service = self.session_container.get_chat_service()
            settings_manager = self.session_container.get_settings_manager()
            
            # Optimize prompt
            result = await chat_service.optimize_prompt(
                user_prompt, provider, 
                self.session_container.session_id, self.logger
            )
            
            # Get usage information
            usage_info = settings_manager.get_provider_usage(provider)
            result["usage_tracking"] = usage_info
            
            self._log_api_response("/api/optimize", result)
            return result
            
        except Exception as e:
            return self._handle_error(e, "/api/optimize")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get conversation history for current session."""
        try:
            chat_service = self.session_container.get_chat_service()
            history = chat_service.get_conversation_history(self.session_container.session_id)
            return [msg.to_dict() for msg in history]
        except Exception as e:
            return self._handle_error(e, "/api/conversation")
    
    def clear_conversation(self) -> Dict[str, Any]:
        """Clear conversation history for current session."""
        try:
            chat_service = self.session_container.get_chat_service()
            chat_service.clear_history(self.session_container.session_id)
            return {"ok": True}
        except Exception as e:
            return self._handle_error(e, "/api/conversation/clear")


class SettingsController(BaseController):
    """Controller for settings-related operations."""
    
    def get_settings(self) -> Dict[str, Any]:
        """Get current application settings."""
        try:
            settings_manager = self.session_container.get_settings_manager()
            settings = settings_manager.get_settings()
            
            response_data = {
                "providers": {k: v.to_dict() for k, v in settings.providers.items()},
                "mcp": settings.mcp,
                "optimizer": settings.optimizer.to_dict(),
                "default_provider": settings.default_provider,
            }
            
            self._log_api_response("/api/settings", response_data)
            return response_data
            
        except Exception as e:
            return self._handle_error(e, "/api/settings")
    
    def update_settings(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update application settings."""
        try:
            # Validate settings data
            self.validator.validate_settings_update(request_data)
            
            settings_manager = self.session_container.get_settings_manager()
            updated_settings = settings_manager.update_settings(request_data)
            return {"ok": True}
        except Exception as e:
            return self._handle_error(e, "/api/settings")


class UsageController(BaseController):
    """Controller for usage tracking operations."""
    
    def get_usage(self, provider_key: str) -> Dict[str, Any]:
        """Get usage information for a specific provider."""
        try:
            settings_manager = self.session_container.get_settings_manager()
            usage_info = settings_manager.get_provider_usage(provider_key)
            
            if usage_info is None:
                return {"error": "Provider not found"}, 404
            
            return usage_info
            
        except Exception as e:
            return self._handle_error(e, f"/api/usage/{provider_key}")
    
    def update_usage(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update usage for a specific provider."""
        try:
            # Validate usage data
            self.validator.validate_usage_request(request_data)
            
            settings_manager = self.session_container.get_settings_manager()
            success = settings_manager.update_provider_usage(
                provider_key=request_data["provider"],
                user_tokens=request_data.get("user_tokens", 0),
                optimized_tokens=request_data.get("optimized_tokens", 0),
                response_tokens=request_data.get("response_tokens", 0),
                api_calls=request_data.get("api_calls", 1)
            )
            
            if success:
                return {"success": True}
            else:
                return {"success": False, "error": "usage_cap_exceeded"}, 400
                
        except Exception as e:
            return self._handle_error(e, "/api/usage/update")
    
    def reset_usage(self, provider_key: str) -> Dict[str, Any]:
        """Reset usage for a specific provider."""
        try:
            settings_manager = self.session_container.get_settings_manager()
            success = settings_manager.reset_provider_usage(provider_key)
            
            if success:
                return {"success": True}
            else:
                return {"success": False, "error": "Provider not found"}, 404
                
        except Exception as e:
            return self._handle_error(e, f"/api/usage/reset/{provider_key}")


class TokenController(BaseController):
    """Controller for token calculation operations."""
    
    def count_tokens(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Count tokens for a given text and provider."""
        self._log_api_call("/api/tokens/count", "POST", request_data)
        
        try:
            # Validate token request data
            self.validator.validate_token_request(request_data)
            
            text = request_data["text"].strip()
            provider = request_data.get("provider", "openai")
            model = request_data.get("model")
            
            token_calculator = self.session_container.get_token_calculator()
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
            
            self._log_api_response("/api/tokens/count", result)
            return result
            
        except Exception as e:
            return self._handle_error(e, "/api/tokens/count")
    
    def analyze_text(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive text analysis with token counts for specified providers."""
        self._log_api_call("/api/tokens/analyze", "POST", request_data)
        
        try:
            self._validate_required_fields(request_data, ["text"])
            
            text = request_data["text"].strip()
            providers = request_data.get("providers", ["openai", "anthropic", "google"])
            
            token_calculator = self.session_container.get_token_calculator()
            analysis = token_calculator.analyze_text(text, providers)
            
            self._log_api_response("/api/tokens/analyze", analysis)
            return analysis
            
        except Exception as e:
            return self._handle_error(e, "/api/tokens/analyze")
    
    def get_models(self, provider: str) -> Dict[str, Any]:
        """Get available models for a specific provider."""
        try:
            token_calculator = self.session_container.get_token_calculator()
            models = token_calculator.get_available_models(provider)
            return {"provider": provider, "models": models}
        except Exception as e:
            return self._handle_error(e, f"/api/tokens/models/{provider}")
    
    def get_model_info(self, provider: str, model: str) -> Dict[str, Any]:
        """Get detailed information about a specific model."""
        try:
            token_calculator = self.session_container.get_token_calculator()
            model_info = token_calculator.get_model_info(provider, model)
            
            if model_info:
                return model_info
            else:
                return {"error": "Model not found"}, 404
                
        except Exception as e:
            return self._handle_error(e, f"/api/tokens/model-info/{provider}/{model}")
    
    def estimate_cost(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate cost for a complete request."""
        try:
            self._validate_required_fields(request_data, ["input_tokens", "output_tokens"])
            
            input_tokens = request_data["input_tokens"]
            output_tokens = request_data["output_tokens"]
            provider = request_data.get("provider", "openai")
            model = request_data.get("model")
            
            token_calculator = self.session_container.get_token_calculator()
            cost = token_calculator.estimate_cost(input_tokens, output_tokens, provider, model)
            
            return {
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "provider": provider,
                "model": model,
                "estimated_cost": cost
            }
            
        except Exception as e:
            return self._handle_error(e, "/api/tokens/estimate-cost")
    
    def get_token_settings(self) -> Dict[str, Any]:
        """Get settings for token calculator."""
        try:
            settings_manager = self.session_container.get_settings_manager()
            settings = settings_manager.get_settings()
            
            token_settings = {
                "providers": {},
                "default_provider": None
            }
            
            for provider_key, provider_config in settings.providers.items():
                if provider_config.enabled:
                    token_settings["providers"][provider_key] = {
                        "name": provider_config.name,
                        "default_model": provider_config.default_model,
                        "enabled": provider_config.enabled
                    }
                    if token_settings["default_provider"] is None:
                        token_settings["default_provider"] = provider_key
            
            self._log_api_call("/api/tokens/settings", "GET", token_settings)
            return token_settings
            
        except Exception as e:
            return self._handle_error(e, "/api/tokens/settings")


class LoggingController(BaseController):
    """Controller for logging operations."""
    
    def get_session_logs(self, session_id: str) -> Dict[str, Any]:
        """Get logs for a specific session."""
        try:
            logging_service = self.session_container.main_container.get_logging_service()
            logs = logging_service.get_session_logs(session_id)
            return {"session_id": session_id, "logs": logs}
        except Exception as e:
            return self._handle_error(e, f"/api/logs/session/{session_id}")
    
    def get_current_session_logs(self) -> Dict[str, Any]:
        """Get logs for the current session."""
        try:
            logging_service = self.session_container.main_container.get_logging_service()
            logs = logging_service.get_session_logs(self.session_container.session_id)
            return {"session_id": self.session_container.session_id, "logs": logs}
        except Exception as e:
            return self._handle_error(e, "/api/logs/current")
    
    def get_recent_logs(self, session_id: str, lines: int = 100) -> Dict[str, Any]:
        """Get recent logs for a specific session."""
        try:
            logging_service = self.session_container.main_container.get_logging_service()
            logs = logging_service.get_recent_logs(session_id, lines)
            return {"session_id": session_id, "logs": logs, "lines": lines}
        except Exception as e:
            return self._handle_error(e, f"/api/logs/recent/{session_id}")
    
    def clear_session_logs(self, session_id: str) -> Dict[str, Any]:
        """Clear logs for a specific session."""
        try:
            logging_service = self.session_container.main_container.get_logging_service()
            logging_service.clear_session_logs(session_id)
            return {"success": True, "session_id": session_id}
        except Exception as e:
            return self._handle_error(e, f"/api/logs/clear/{session_id}")
    
    def get_all_sessions(self) -> Dict[str, Any]:
        """Get all available session IDs."""
        try:
            logging_service = self.session_container.main_container.get_logging_service()
            session_ids = logging_service.get_all_session_ids()
            return {"sessions": session_ids}
        except Exception as e:
            return self._handle_error(e, "/api/logs/sessions")
    
    def get_current_session_id(self) -> Dict[str, Any]:
        """Get the current session ID."""
        return {"session_id": self.session_container.session_id}
