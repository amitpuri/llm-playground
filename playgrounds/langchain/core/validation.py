"""
Configuration validation module for the LLM playground application.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from .exceptions import ValidationError, ConfigurationError


@dataclass
class ValidationResult:
    """Result of a validation operation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    
    def add_error(self, error: str):
        """Add a validation error."""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a validation warning."""
        self.warnings.append(warning)


class ConfigValidator:
    """Validates configuration settings."""
    
    @staticmethod
    def validate_provider_config(config: Dict[str, Any]) -> ValidationResult:
        """Validate provider configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check required fields
        required_fields = ["name", "default_model"]
        for field in required_fields:
            if not config.get(field):
                result.add_error(f"Missing required field: {field}")
        
        # Validate API key if enabled
        if config.get("enabled", False):
            if not config.get("api_key"):
                result.add_error("API key is required when provider is enabled")
        
        # Validate temperature range
        temperature = config.get("temperature", 0.7)
        if not (0.0 <= temperature <= 2.0):
            result.add_error("Temperature must be between 0.0 and 2.0")
        
        # Validate context window
        context_window = config.get("context_window", 128000)
        if context_window <= 0:
            result.add_error("Context window must be positive")
        
        # Validate max completion tokens
        max_tokens = config.get("max_completion_tokens", 4000)
        if max_tokens <= 0:
            result.add_error("Max completion tokens must be positive")
        
        return result
    
    @staticmethod
    def validate_mcp_config(config: Dict[str, Any]) -> ValidationResult:
        """Validate MCP configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate GitHub config
        github_config = config.get("github", {})
        if github_config.get("enabled", False):
            if not github_config.get("url"):
                result.add_error("GitHub MCP URL is required when enabled")
            if not github_config.get("repo"):
                result.add_error("GitHub repository is required when enabled")
        
        # Validate PostgreSQL config
        postgres_config = config.get("postgres", {})
        if postgres_config.get("enabled", False):
            if not postgres_config.get("url"):
                result.add_error("PostgreSQL MCP URL is required when enabled")
        
        return result
    
    @staticmethod
    def validate_optimizer_config(config: Dict[str, Any]) -> ValidationResult:
        """Validate optimizer configuration."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Validate temperature range
        temperature = config.get("temperature", 0.7)
        if not (0.0 <= temperature <= 2.0):
            result.add_error("Optimizer temperature must be between 0.0 and 2.0")
        
        # Validate max tokens
        max_tokens = config.get("max_tokens", 1000)
        if max_tokens <= 0:
            result.add_error("Optimizer max tokens must be positive")
        
        # Validate context usage percentage
        max_context_usage = config.get("max_context_usage", 0.8)
        if not (0.1 <= max_context_usage <= 1.0):
            result.add_error("Max context usage must be between 0.1 and 1.0")
        
        return result
    
    @staticmethod
    def validate_chat_request(data: Dict[str, Any]) -> ValidationResult:
        """Validate chat request data."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check required fields
        if not data.get("user_prompt"):
            result.add_error("User prompt is required")
        elif not data["user_prompt"].strip():
            result.add_error("User prompt cannot be empty")
        
        # Validate provider if specified
        provider = data.get("provider")
        if provider and not isinstance(provider, str):
            result.add_error("Provider must be a string")
        
        # Validate model if specified
        model = data.get("model")
        if model and not isinstance(model, str):
            result.add_error("Model must be a string")
        
        return result
    
    @staticmethod
    def validate_token_request(data: Dict[str, Any]) -> ValidationResult:
        """Validate token calculation request data."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check required fields
        if not data.get("text"):
            result.add_error("Text is required for token calculation")
        
        # Validate provider if specified
        provider = data.get("provider")
        if provider and not isinstance(provider, str):
            result.add_error("Provider must be a string")
        
        # Validate model if specified
        model = data.get("model")
        if model and not isinstance(model, str):
            result.add_error("Model must be a string")
        
        return result
    
    @staticmethod
    def validate_usage_request(data: Dict[str, Any]) -> ValidationResult:
        """Validate usage tracking request data."""
        result = ValidationResult(is_valid=True, errors=[], warnings=[])
        
        # Check required fields
        if not data.get("provider"):
            result.add_error("Provider is required for usage tracking")
        
        # Validate numeric fields
        numeric_fields = ["user_tokens", "optimized_tokens", "response_tokens", "api_calls"]
        for field in numeric_fields:
            value = data.get(field, 0)
            if not isinstance(value, (int, float)) or value < 0:
                result.add_error(f"{field} must be a non-negative number")
        
        return result


class RequestValidator:
    """Validates incoming API requests."""
    
    def __init__(self):
        self.config_validator = ConfigValidator()
    
    def validate_chat_request(self, data: Dict[str, Any]) -> None:
        """Validate chat request and raise ValidationError if invalid."""
        result = self.config_validator.validate_chat_request(data)
        if not result.is_valid:
            raise ValidationError(
                f"Invalid chat request: {'; '.join(result.errors)}",
                details={"errors": result.errors, "warnings": result.warnings}
            )
    
    def validate_optimize_request(self, data: Dict[str, Any]) -> None:
        """Validate optimize request and raise ValidationError if invalid."""
        result = self.config_validator.validate_chat_request(data)
        if not result.is_valid:
            raise ValidationError(
                f"Invalid optimize request: {'; '.join(result.errors)}",
                details={"errors": result.errors, "warnings": result.warnings}
            )
    
    def validate_token_request(self, data: Dict[str, Any]) -> None:
        """Validate token request and raise ValidationError if invalid."""
        result = self.config_validator.validate_token_request(data)
        if not result.is_valid:
            raise ValidationError(
                f"Invalid token request: {'; '.join(result.errors)}",
                details={"errors": result.errors, "warnings": result.warnings}
            )
    
    def validate_usage_request(self, data: Dict[str, Any]) -> None:
        """Validate usage request and raise ValidationError if invalid."""
        result = self.config_validator.validate_usage_request(data)
        if not result.is_valid:
            raise ValidationError(
                f"Invalid usage request: {'; '.join(result.errors)}",
                details={"errors": result.errors, "warnings": result.warnings}
            )
    
    def validate_settings_update(self, data: Dict[str, Any]) -> None:
        """Validate settings update and raise ValidationError if invalid."""
        errors = []
        
        # Validate providers
        providers = data.get("providers", {})
        for provider_key, provider_config in providers.items():
            result = self.config_validator.validate_provider_config(provider_config)
            if not result.is_valid:
                errors.extend([f"Provider {provider_key}: {error}" for error in result.errors])
        
        # Validate MCP config
        mcp_config = data.get("mcp", {})
        result = self.config_validator.validate_mcp_config(mcp_config)
        if not result.is_valid:
            errors.extend([f"MCP: {error}" for error in result.errors])
        
        # Validate optimizer config
        optimizer_config = data.get("optimizer", {})
        result = self.config_validator.validate_optimizer_config(optimizer_config)
        if not result.is_valid:
            errors.extend([f"Optimizer: {error}" for error in result.errors])
        
        if errors:
            raise ValidationError(
                f"Invalid settings: {'; '.join(errors)}",
                details={"errors": errors}
            )
