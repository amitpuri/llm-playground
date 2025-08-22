"""
Data models for the LangChain playground application.
Following SOLID principles with clear separation of concerns.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    def get_context_window(self) -> int:
        """Get the context window size in tokens."""
        pass


@dataclass
class TokenCount:
    """Token count information."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TokenCount':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: str = ""
    tokens: Optional[TokenCount] = None
    
    def __post_init__(self):
        if self.timestamp == "":
            self.timestamp = datetime.now().isoformat()
        if self.tokens is None:
            self.tokens = TokenCount()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['tokens'] = self.tokens.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        """Create from dictionary."""
        tokens_data = data.get('tokens', {})
        if isinstance(tokens_data, dict):
            data['tokens'] = TokenCount.from_dict(tokens_data)
        return cls(**data)


@dataclass
class ChatResponse:
    """Response from LLM chat completion."""
    content: str
    model: str
    provider: str
    tokens: TokenCount
    finish_reason: str = "stop"
    debug_info: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['tokens'] = self.tokens.to_dict()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatResponse':
        """Create from dictionary."""
        tokens_data = data.get('tokens', {})
        if isinstance(tokens_data, dict):
            data['tokens'] = TokenCount.from_dict(tokens_data)
        return cls(**data)


@dataclass
class UsageTracking:
    """Usage tracking for a provider."""
    total_tokens_used: int = 0
    user_tokens: int = 0
    optimized_tokens: int = 0
    response_tokens: int = 0
    api_calls: int = 0
    last_updated: str = ""
    
    def update_usage(self, user_tokens: int = 0, optimized_tokens: int = 0, response_tokens: int = 0, api_calls: int = 1):
        """Update usage statistics."""
        self.user_tokens += user_tokens
        self.optimized_tokens += optimized_tokens
        self.response_tokens += response_tokens
        self.api_calls += api_calls
        self.total_tokens_used = self.user_tokens + self.optimized_tokens + self.response_tokens
        self.last_updated = datetime.now().isoformat()
    
    def reset_usage(self):
        """Reset usage statistics."""
        self.total_tokens_used = 0
        self.user_tokens = 0
        self.optimized_tokens = 0
        self.response_tokens = 0
        self.api_calls = 0
        self.last_updated = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UsageTracking':
        """Create from dictionary with field name compatibility."""
        # Handle both old and new field names for backward compatibility
        field_mapping = {
            'user_prompt_tokens': 'user_tokens',
            'optimized_prompt_tokens': 'optimized_tokens'
        }
        
        # Create a copy of data and map old field names to new ones
        mapped_data = {}
        for key, value in data.items():
            if key in field_mapping:
                mapped_data[field_mapping[key]] = value
            else:
                mapped_data[key] = value
        
        return cls(**mapped_data)


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    enabled: bool = False
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    organization: str = ""
    temperature: float = 0.7
    default_model: str = ""
    context_window: int = 128000
    max_completion_tokens: int = 4000
    usage_cap_tokens: int = 1000000  # Monthly usage cap in tokens
    usage_tracking: UsageTracking = None

    def __post_init__(self):
        if self.usage_tracking is None:
            self.usage_tracking = UsageTracking()

    def to_dict(self) -> Dict[str, Any]:
        """Convert provider config to dictionary."""
        data = asdict(self)
        data['usage_tracking'] = self.usage_tracking.to_dict()
        return data

    def is_usage_cap_exceeded(self) -> bool:
        """Check if usage cap is exceeded."""
        return self.usage_tracking.total_tokens_used >= self.usage_cap_tokens
    
    def get_usage_percentage(self) -> float:
        """Get usage as percentage of cap."""
        if self.usage_cap_tokens == 0:
            return 0.0
        return (self.usage_tracking.total_tokens_used / self.usage_cap_tokens) * 100
    
    def get_remaining_tokens(self) -> int:
        """Get remaining tokens within cap."""
        return max(0, self.usage_cap_tokens - self.usage_tracking.total_tokens_used)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProviderConfig':
        """Create from dictionary."""
        # Handle usage_tracking - it might be a dict or already a UsageTracking object
        usage_data = data.get('usage_tracking', {})
        if isinstance(usage_data, dict):
            usage_tracking = UsageTracking.from_dict(usage_data)
            data['usage_tracking'] = usage_tracking
        elif usage_data is None:
            data['usage_tracking'] = UsageTracking()
        
        # Remove models from data as it's not part of ProviderConfig
        data_clean = {k: v for k, v in data.items() if k != 'models'}
        
        return cls(**data_clean)


@dataclass
class MCPGitHubConfig:
    """Configuration for GitHub MCP connector."""
    enabled: bool = False
    url: str = ""
    auth_token: str = ""
    repo: str = ""
    owner: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPGitHubConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class MCPPostgresConfig:
    """Configuration for PostgreSQL MCP connector."""
    enabled: bool = False
    url: str = ""
    auth_token: str = ""
    sample_sql: str = "SELECT NOW() AS server_time;"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPPostgresConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class OptimizerConfig:
    """Configuration for the prompt optimizer."""
    enabled: bool = True
    provider: str = "anthropic"
    model: str = "claude-3-5-sonnet-20241022"
    temperature: float = 0.7
    max_tokens: int = 1000  # Maximum tokens for optimized prompt
    max_context_usage: float = 0.8  # Maximum context window usage (80% by default)
    max_context_tokens: int = 80000
    include_github_issues: bool = True
    include_research_papers: bool = True
    max_issues: int = 3
    max_papers: int = 8

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'OptimizerConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class AppSettings:
    """Main application settings container."""
    providers: Dict[str, ProviderConfig]
    mcp: Dict[str, Any]
    optimizer: OptimizerConfig
    default_provider: str = "anthropic"  # Default provider to use as fallback

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "providers": {k: v.to_dict() for k, v in self.providers.items()},
            "mcp": self.mcp,
            "optimizer": self.optimizer.to_dict(),
            "default_provider": self.default_provider,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppSettings':
        """Create from dictionary."""
        providers = {k: ProviderConfig.from_dict(v) for k, v in data.get("providers", {}).items()}
        optimizer = OptimizerConfig.from_dict(data.get("optimizer", {}))
        default_provider = data.get("default_provider", "anthropic")
        return cls(providers=providers, mcp=data.get("mcp", {}), optimizer=optimizer, default_provider=default_provider)


@dataclass
class GitHubIssue:
    """Represents a GitHub issue."""
    number: Optional[int] = None
    title: str = ""
    body: str = ""
    state: str = ""
    created_at: str = ""
    updated_at: str = ""
    url: str = ""
    user: str = ""
    labels: List[str] = None
    assignees: List[str] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.assignees is None:
            self.assignees = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GitHubIssue':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class ResearchPaper:
    """Represents a research paper."""
    title: str = ""
    authors: str = ""
    abstract: str = ""
    url: str = ""
    date: str = ""
    category: str = ""
    citations: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchPaper':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class DebugInfo:
    """Debug information for troubleshooting."""
    timestamp: str = ""
    operation: str = ""
    provider: str = ""
    model: str = ""
    tokens_used: int = 0
    response_time: float = 0.0
    error: Optional[str] = None
    mcp_calls: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.mcp_calls is None:
            self.mcp_calls = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DebugInfo':
        """Create from dictionary."""
        return cls(**data)


class SettingsRepository(ABC):
    """Abstract interface for settings storage."""
    
    @abstractmethod
    def load(self) -> AppSettings:
        """Load settings from storage."""
        pass
    
    @abstractmethod
    def save(self, settings: AppSettings) -> None:
        """Save settings to storage."""
        pass


class MCPConnector(ABC):
    """Abstract base class for MCP connectors."""
    
    @abstractmethod
    async def fetch_data(self, query: str) -> str:
        """Fetch data from the MCP server."""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if the connector is enabled."""
        pass


class LoggingService:
    """Service for managing multiple session loggers."""
    
    def __init__(self):
        self.session_loggers: Dict[str, Any] = {}
    
    def get_logger(self, session_id: str = None) -> Any:
        """Get or create a logger for the given session."""
        if session_id not in self.session_loggers:
            # This will be implemented in logging_service.py
            pass
        return self.session_loggers.get(session_id)
    
    def get_session_logs(self, session_id: str) -> str:
        """Get logs for a specific session."""
        if session_id not in self.session_loggers:
            return f"No logger found for session {session_id}"
        return self.session_loggers[session_id].get_session_logs()
    
    def get_recent_logs(self, session_id: str, lines: int = 100) -> str:
        """Get recent logs for a specific session."""
        if session_id not in self.session_loggers:
            return f"No logger found for session {session_id}"
        return self.session_loggers[session_id].get_recent_logs(lines)
    
    def clear_session_logs(self, session_id: str):
        """Clear logs for a specific session."""
        if session_id in self.session_loggers:
            self.session_loggers[session_id].clear_logs()
    
    def get_all_session_ids(self) -> list:
        """Get all active session IDs."""
        return list(self.session_loggers.keys())
    
    def get_log_file_path(self, session_id: str) -> str:
        """Get the log file path for a specific session."""
        if session_id in self.session_loggers:
            return self.session_loggers[session_id].get_log_file_path()
        return ""
    
    def cleanup_old_sessions(self, max_sessions: int = 10):
        """Clean up old sessions, keeping only the most recent ones."""
        if len(self.session_loggers) <= max_sessions:
            return
        
        # Sort sessions by creation time (this would need to be tracked)
        # For now, just keep the most recent ones based on session ID
        session_ids = sorted(self.session_loggers.keys())
        sessions_to_remove = session_ids[:-max_sessions]
        
        for session_id in sessions_to_remove:
            del self.session_loggers[session_id]
