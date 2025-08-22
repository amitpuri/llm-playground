"""
Dependency injection container for managing service dependencies.
"""
from typing import Dict, Any, Optional
from .settings import FileSettingsRepository, SettingsManager
from .chat_service import ChatService, ChatSessionManager
from .logging_service import logging_service
from .token_calculator import token_calculator
from .llm_providers import LLMProviderFactory
from .mcp_connectors import MCPConnectorFactory


class ServiceContainer:
    """Dependency injection container for managing all services."""
    
    def __init__(self, session_settings_path: str = "../session-data/settings.json"):
        self._services: Dict[str, Any] = {}
        self._session_settings_path = session_settings_path
        self._configure_services()
    
    def _configure_services(self):
        """Configure all services with proper dependencies."""
        # Core repositories
        self._services['settings_repository'] = FileSettingsRepository(self._session_settings_path)
        
        # Core services
        self._services['settings_manager'] = SettingsManager(self._services['settings_repository'])
        self._services['chat_session_manager'] = ChatSessionManager()
        self._services['logging_service'] = logging_service
        self._services['token_calculator'] = token_calculator
        
        # Factories
        self._services['llm_provider_factory'] = LLMProviderFactory()
        self._services['mcp_connector_factory'] = MCPConnectorFactory()
        
        # Main services
        self._services['chat_service'] = ChatService(
            settings_manager=self._services['settings_manager'],
            session_manager=self._services['chat_session_manager']
        )
    
    def get_service(self, service_name: str) -> Any:
        """Get a service by name."""
        if service_name not in self._services:
            raise KeyError(f"Service '{service_name}' not found in container")
        return self._services[service_name]
    
    def get_settings_manager(self) -> SettingsManager:
        """Get the settings manager."""
        return self._services['settings_manager']
    
    def get_chat_service(self) -> ChatService:
        """Get the chat service."""
        return self._services['chat_service']
    
    def get_logging_service(self):
        """Get the logging service."""
        return self._services['logging_service']
    
    def get_token_calculator(self):
        """Get the token calculator."""
        return self._services['token_calculator']
    
    def create_session_container(self, session_id: str) -> 'SessionServiceContainer':
        """Create a session-specific container."""
        return SessionServiceContainer(self, session_id)


class SessionServiceContainer:
    """Container for session-specific services."""
    
    def __init__(self, main_container: ServiceContainer, session_id: str):
        self.main_container = main_container
        self.session_id = session_id
        self._session_services: Dict[str, Any] = {}
        self._configure_session_services()
    
    def _configure_session_services(self):
        """Configure session-specific services."""
        # Create session-specific settings repository
        session_settings_path = f"../session-data/settings-{self.session_id}.json"
        self._session_services['settings_repository'] = FileSettingsRepository(session_settings_path)
        self._session_services['settings_manager'] = SettingsManager(self._session_services['settings_repository'])
        
        # Get session-specific logger
        self._session_services['logger'] = self.main_container.get_logging_service().get_logger(self.session_id)
    
    def get_settings_manager(self) -> SettingsManager:
        """Get session-specific settings manager."""
        return self._session_services['settings_manager']
    
    def get_logger(self):
        """Get session-specific logger."""
        return self._session_services['logger']
    
    def get_chat_service(self) -> ChatService:
        """Get the main chat service (shared across sessions)."""
        return self.main_container.get_chat_service()
    
    def get_token_calculator(self):
        """Get the token calculator."""
        return self.main_container.get_token_calculator()
