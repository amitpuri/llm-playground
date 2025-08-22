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
    
    def load_settings(self) -> AppSettings:
        """Backward compatibility method."""
        return self.load()
    
    def save_settings(self, settings: AppSettings) -> bool:
        """Backward compatibility method."""
        try:
            self.save(settings)
            return True
        except Exception as e:
            print(f"Error saving settings: {e}")
            return False
    
    def _create_default_settings(self) -> AppSettings:
        """Get default application settings."""
        providers = {
            "anthropic": ProviderConfig(
                enabled=True,
                name="Anthropic",
                base_url="https://api.anthropic.com",
                api_key="",
                organization="",
                default_model="claude-3-7-sonnet-latest",
                temperature=0.2,
                max_completion_tokens=8192,
                context_window=200000,
                usage_cap_tokens=1000000
            ),
            "openai": ProviderConfig(
                enabled=False,
                name="OpenAI",
                base_url="https://api.openai.com/v1",
                api_key="",
                organization="",
                default_model="gpt-5",
                temperature=0.2,
                max_completion_tokens=8192,
                context_window=128000,
                usage_cap_tokens=1000000
            ),
            "ollama": ProviderConfig(
                enabled=True,
                name="Ollama",
                base_url="http://localhost:11434",
                api_key="",
                organization="",
                default_model="gemma3:270m",
                temperature=0.2,
                max_completion_tokens=4096,
                context_window=8000,
                usage_cap_tokens=1000000
            ),
            "google": ProviderConfig(
                enabled=True,
                name="Google",
                base_url="https://generativelanguage.googleapis.com",
                api_key="",
                organization="",
                default_model="gemini-2.5-pro",
                temperature=0.2,
                max_completion_tokens=8192,
                context_window=128000,
                usage_cap_tokens=1000000
            )
        }
        
        mcp = {
            "github": {
                "enabled": False,
                "url": "http://localhost:3000",
                "auth_token": "",
                "repo": "microsoft/vscode",
                "owner": "microsoft"
            },
            "postgres": {
                "enabled": False,
                "url": "http://localhost:3001",
                "auth_token": "",
                "sample_sql": "SELECT title, authors, abstract FROM papers LIMIT 10"
            }
        }
        
        optimizer = OptimizerConfig(
            enabled=True,
            provider="openai",
            model="gpt-5",
            temperature=0.2,
            max_tokens=1000,
            max_context_usage=0.8,
            max_context_tokens=80000,
            include_github_issues=True,
            include_research_papers=True,
            max_issues=3,
            max_papers=8
        )
        
        return AppSettings(
            providers=providers,
            mcp=mcp,
            optimizer=optimizer,
            default_provider="openai"
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
    
    def reset_provider_usage(self, provider_key: str) -> bool:
        """Reset usage for a specific provider."""
        current_settings = self.get_settings()
        
        if provider_key not in current_settings.providers:
            return False
        
        provider = current_settings.providers[provider_key]
        provider.usage_tracking.reset_usage()
        
        self.save_settings(current_settings)
        return True
