"""
Data models for the MCP Playground application.
Following SOLID principles with clear separation of concerns.
"""
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime


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
    """Configuration for an AI provider."""
    enabled: bool = False
    name: str = ""
    base_url: str = ""
    api_key: str = ""
    temperature: float = 0.2
    default_model: str = ""
    context_window: int = 128000
    max_completion_tokens: int = 8192  # Cap for max completion tokens to prevent attacks
    usage_cap_tokens: int = 1000000  # Monthly usage cap in tokens
    usage_tracking: UsageTracking = None

    def __post_init__(self):
        if self.usage_tracking is None:
            self.usage_tracking = UsageTracking()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
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
        
        return cls(**data)


@dataclass
class MCPGitHubConfig:
    """Configuration for GitHub MCP connector."""
    enabled: bool = False
    url: str = ""
    auth_token: str = ""
    repo: str = ""

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
    provider: str = "anthropic"
    model: str = "claude-3-7-sonnet-latest"
    temperature: float = 0.2
    max_tokens: int = 1000  # Maximum tokens for optimized prompt
    max_context_usage: float = 0.8  # Maximum context window usage (80% by default)

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
    state: str = ""
    url: str = ""
    updated_at: str = ""
    labels: List[str] = None
    body: str = ""
    comments: List[Dict[str, Any]] = None

    def __post_init__(self):
        if self.labels is None:
            self.labels = []
        if self.comments is None:
            self.comments = []


@dataclass
class ResearchPaper:
    """Represents a research paper from the database."""
    url: str = ""
    title: str = ""
    date: str = ""
    abstract: str = ""
    category: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResearchPaper':
        """Create from dictionary with flexible field mapping."""
        # Handle different field names that might be present
        field_mapping = {
            'url': ['url', 'link', 'paper_url'],
            'title': ['title', 'name', 'paper_title'],
            'date': ['date', 'published_date', 'publication_date'],
            'abstract': ['abstract', 'summary', 'description'],
            'category': ['category', 'type', 'field']
        }
        
        result = {}
        for field, possible_names in field_mapping.items():
            for name in possible_names:
                if name in data:
                    result[field] = data[name]
                    break
            if field not in result:
                result[field] = ""
        
        return cls(**result)


@dataclass
class ChatMessage:
    """Represents a chat message."""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class DebugInfo:
    """Debug information for API calls."""
    tools: List[str] = None
    calls: List[Dict[str, Any]] = None
    flow: List[Dict[str, Any]] = None
    error: Optional[str] = None
    sql: Optional[str] = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.calls is None:
            self.calls = []
        if self.flow is None:
            self.flow = []


@dataclass
class OptimizedPromptResult:
    """Result of prompt optimization."""
    optimized_prompt: str
    debug: Dict[str, Any]
    budgets: Dict[str, Any]
    final_tokens_est: int


@dataclass
class ChatResponse:
    """Response from chat API."""
    text: str
    structured: str
    debug: Dict[str, Any]


# Abstract base classes following Interface Segregation Principle
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
    """Abstract interface for MCP connectors."""
    
    @abstractmethod
    async def connect(self) -> Any:
        """Connect to the MCP server."""
        pass
    
    @abstractmethod
    def _mcp_connect(self):
        """Create MCP client connection."""
        pass


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
