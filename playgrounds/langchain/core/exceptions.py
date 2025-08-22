"""
Custom exception hierarchy for the LLM playground application.
"""
from typing import Optional, Dict, Any


class LLMPlaygroundException(Exception):
    """Base exception for LLM playground application."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


class ConfigurationError(LLMPlaygroundException):
    """Raised when there's a configuration error."""
    pass


class SettingsError(ConfigurationError):
    """Raised when there's an error with settings management."""
    pass


class ProviderError(LLMPlaygroundException):
    """Base exception for LLM provider errors."""
    
    def __init__(self, message: str, provider: str, model: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.provider = provider
        self.model = model


class ProviderConnectionError(ProviderError):
    """Raised when connection to LLM provider fails."""
    pass


class ProviderAuthenticationError(ProviderError):
    """Raised when authentication with LLM provider fails."""
    pass


class ProviderRateLimitError(ProviderError):
    """Raised when rate limit is exceeded."""
    pass


class ProviderQuotaExceededError(ProviderError):
    """Raised when quota is exceeded."""
    pass


class MCPError(LLMPlaygroundException):
    """Base exception for MCP connector errors."""
    
    def __init__(self, message: str, connector: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.connector = connector


class MCPConnectionError(MCPError):
    """Raised when MCP connection fails."""
    pass


class MCPAuthenticationError(MCPError):
    """Raised when MCP authentication fails."""
    pass


class MCPDataError(MCPError):
    """Raised when there's an error processing MCP data."""
    pass


class ChatServiceError(LLMPlaygroundException):
    """Raised when there's an error in chat service."""
    pass


class SessionError(LLMPlaygroundException):
    """Raised when there's an error with session management."""
    
    def __init__(self, message: str, session_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.session_id = session_id


class TokenCalculationError(LLMPlaygroundException):
    """Raised when there's an error in token calculation."""
    pass


class PromptOptimizationError(LLMPlaygroundException):
    """Raised when there's an error in prompt optimization."""
    pass


class ValidationError(LLMPlaygroundException):
    """Raised when input validation fails."""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.field = field
        self.value = value


class UsageLimitError(LLMPlaygroundException):
    """Raised when usage limits are exceeded."""
    
    def __init__(self, message: str, provider: str, current_usage: int, limit: int, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, details)
        self.provider = provider
        self.current_usage = current_usage
        self.limit = limit
