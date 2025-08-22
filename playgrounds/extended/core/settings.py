"""
Settings management module following the Repository pattern.
"""
import os
import json
from typing import Dict, Any, Optional
from .models import AppSettings, ProviderConfig, OptimizerConfig, SettingsRepository


class FileSettingsRepository(SettingsRepository):
    """File-based settings repository implementation."""
    
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def load(self) -> AppSettings:
        """Load settings from JSON file with fallback to sample.settings.json."""
        # Try to load from the specified file path first
        if os.path.exists(self.file_path):
            print(f"Loading settings from: {self.file_path}")
            with open(self.file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            return AppSettings.from_dict(raw_data)
        
        # If the specified file doesn't exist, try to use session-data/settings.json as template
        session_data_settings_path = "../session-data/settings.json"
        if os.path.exists(session_data_settings_path):
            print(f"Using session-data/settings.json as template for new session")
            with open(session_data_settings_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            settings = AppSettings.from_dict(raw_data)
            # Save to the session file to create it
            self.save(settings)
            return settings
        
        # If session-data/settings.json doesn't exist, try settings.json as template
        settings_path = "../session-data/settings.json"
        if os.path.exists(settings_path):
            print(f"Using settings.json as template for new session")
            with open(settings_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            settings = AppSettings.from_dict(raw_data)
            # Save to the session file to create it
            self.save(settings)
            return settings
        
        # If settings.json doesn't exist, try sample.settings.json
        sample_path = "../sample.settings.json"
        if os.path.exists(sample_path):
            print(f"settings.json not found, loading from: {sample_path}")
            with open(sample_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            settings = AppSettings.from_dict(raw_data)
            # Save to the session file to create it
            self.save(settings)
            return settings
        
        # If neither file exists, create default settings
        print("No settings files found, creating default settings")
        settings = self._create_default_settings()
        self.save(settings)
        return settings
    
    def save(self, settings: AppSettings) -> None:
        """Save settings to JSON file."""
        data = settings.to_dict()
        
        # Create directory if it doesn't exist
        directory = os.path.dirname(self.file_path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Settings saved to: {self.file_path}")
    
    def _create_default_settings(self) -> AppSettings:
        """Create default settings with environment variable fallbacks."""
        return AppSettings(
            providers={
                "openai": ProviderConfig(
                    enabled=False,
                    name="OpenAI",
                    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                    api_key=os.getenv("OPENAI_API_KEY", ""),
                    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
                    default_model=os.getenv("OPENAI_DEFAULT_MODEL", "gpt-4o"),
                    context_window=int(os.getenv("OPENAI_CONTEXT_WINDOW", "128000")),
                ),
                "anthropic": ProviderConfig(
                    enabled=True,
                    name="Anthropic",
                    base_url=os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
                    api_key=os.getenv("ANTHROPIC_API_KEY", ""),
                    temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.2")),
                    default_model=os.getenv("ANTHROPIC_DEFAULT_MODEL", "claude-3-7-sonnet-latest"),
                    context_window=int(os.getenv("ANTHROPIC_CONTEXT_WINDOW", "200000")),
                ),
                "ollama": ProviderConfig(
                    enabled=True,
                    name="Ollama",
                    base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                    api_key="",
                    temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.2")),
                    default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "gemma3:270m"),
                    context_window=int(os.getenv("OLLAMA_CONTEXT_WINDOW", "8000")),
                ),
                "google": ProviderConfig(
                    enabled=False,
                    name="Google",
                    base_url=os.getenv("GOOGLE_BASE_URL", "https://generativelanguage.googleapis.com"),
                    api_key=os.getenv("GOOGLE_API_KEY", ""),
                    temperature=float(os.getenv("GOOGLE_TEMPERATURE", "0.2")),
                    default_model=os.getenv("GOOGLE_DEFAULT_MODEL", "gemini-2.5-pro"),
                    context_window=int(os.getenv("GOOGLE_CONTEXT_WINDOW", "128000")),
                ),
            },
            mcp={
                "github": {
                    "enabled": True,
                    "url": os.getenv("MCP_SERVER_URL", "https://api.githubcopilot.com/mcp/"),
                    "auth_token": os.getenv("GITHUB_TOKEN", ""),
                    "repo": os.getenv("GITHUB_REPO", "owner/repo"),
                },
                "postgres": {
                    "enabled": True,
                    "url": os.getenv("MCP_SSE_SERVER_URL", "http://localhost:8000/sse"),
                    "auth_token": os.getenv("MCP_AUTH_TOKEN", ""),
                    "sample_sql": os.getenv("PG_SAMPLE_SQL",
                        "SELECT url, title, date, abstract, category "
                        "FROM research_papers.ai_research_papers "
                        "ORDER BY date DESC LIMIT 5;"
                    ),
                },
            },
            optimizer=OptimizerConfig(
                provider=os.getenv("OPT_PROVIDER", "anthropic"),
                model=os.getenv("OPT_MODEL", "claude-3-7-sonnet-latest"),
                temperature=float(os.getenv("OPT_TEMPERATURE", "0.2")),
                max_tokens=int(os.getenv("OPT_MAX_TOKENS", "1000")),
                max_context_usage=float(os.getenv("OPT_MAX_CONTEXT_USAGE", "0.8")),
            ),
        )


class SettingsManager:
    """High-level settings manager that coordinates with the repository."""
    
    def __init__(self, repository: SettingsRepository):
        self.repository = repository
        self._cache: Optional[AppSettings] = None
    
    def get_settings(self) -> AppSettings:
        """Get current settings, using cache if available."""
        if self._cache is None:
            self._cache = self.repository.load()
        return self._cache
    
    def save_settings(self, settings: AppSettings) -> None:
        """Save settings and update cache."""
        self.repository.save(settings)
        self._cache = settings
    
    def update_settings(self, updates: Dict[str, Any]) -> AppSettings:
        """Update settings with partial data."""
        current = self.get_settings()
        
        # Update providers
        if "providers" in updates:
            for key, provider_data in updates["providers"].items():
                if key in current.providers:
                    current.providers[key] = ProviderConfig.from_dict({
                        **current.providers[key].to_dict(),
                        **provider_data
                    })
                else:
                    current.providers[key] = ProviderConfig.from_dict(provider_data)
        
        # Update MCP settings
        if "mcp" in updates:
            current.mcp.update(updates["mcp"])
        
        # Update optimizer
        if "optimizer" in updates:
            current.optimizer = OptimizerConfig.from_dict({
                **current.optimizer.to_dict(),
                **updates["optimizer"]
            })
        
        # Update default provider
        if "default_provider" in updates:
            current.default_provider = updates["default_provider"]
        
        self.save_settings(current)
        return current
    
    def clear_cache(self) -> None:
        """Clear the settings cache."""
        self._cache = None
    
    def update_provider_usage(self, provider_key: str, user_tokens: int = 0, optimized_tokens: int = 0, 
                            response_tokens: int = 0, api_calls: int = 1) -> bool:
        """Update usage for a specific provider and save settings."""
        current_settings = self.get_settings()
        
        if provider_key not in current_settings.providers:
            return False
        
        provider = current_settings.providers[provider_key]
        
        # Check if usage cap would be exceeded
        new_total = provider.usage_tracking.total_tokens_used + user_tokens + optimized_tokens + response_tokens
        if new_total > provider.usage_cap_tokens:
            return False  # Usage cap would be exceeded
        
        # Update usage
        provider.usage_tracking.update_usage(user_tokens, optimized_tokens, response_tokens, api_calls)
        
        # Save updated settings
        self.save_settings(current_settings)
        return True
    
    def get_provider_usage(self, provider_key: str) -> Optional[Dict[str, Any]]:
        """Get usage information for a specific provider."""
        current_settings = self.get_settings()
        
        if provider_key not in current_settings.providers:
            return None
        
        provider = current_settings.providers[provider_key]
        usage = provider.usage_tracking
        
        return {
            'total_tokens_used': usage.total_tokens_used,
            'user_tokens': usage.user_tokens,
            'optimized_tokens': usage.optimized_tokens,
            'response_tokens': usage.response_tokens,
            'api_calls': usage.api_calls,
            'last_updated': usage.last_updated,
            'usage_cap_tokens': provider.usage_cap_tokens,
            'usage_percentage': provider.get_usage_percentage(),
            'remaining_tokens': provider.get_remaining_tokens(),
            'is_cap_exceeded': provider.is_usage_cap_exceeded()
        }
    
    def reset_provider_usage(self, provider_key: str) -> bool:
        """Reset usage for a specific provider."""
        current_settings = self.get_settings()
        
        if provider_key not in current_settings.providers:
            return False
        
        provider = current_settings.providers[provider_key]
        provider.usage_tracking.reset_usage()
        
        self.save_settings(current_settings)
        return True
