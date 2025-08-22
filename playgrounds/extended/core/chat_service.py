"""
Chat service module following the Service pattern.
Handles chat interactions and response processing.
"""
import json
import asyncio
from typing import Dict, Any, Optional
from .models import ChatResponse, ChatMessage, MCPGitHubConfig, MCPPostgresConfig
from .llm_providers import LLMProviderFactory, LLMProvider
from .mcp_connectors import MCPConnectorFactory, GitHubMCPConnector, PostgresMCPConnector
from .prompt_optimizer import PromptOptimizer, TextRenderer
from .settings import SettingsManager


class ChatService:
    """Main chat service that coordinates all chat operations."""
    
    def __init__(self, settings_manager: SettingsManager):
        self.settings_manager = settings_manager
        self._conversation_history: list[ChatMessage] = []
    
    def add_message(self, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        message = ChatMessage(role=role, content=content)
        self._conversation_history.append(message)
    
    def get_conversation_history(self) -> list[ChatMessage]:
        """Get the conversation history."""
        return self._conversation_history.copy()
    
    def clear_history(self) -> None:
        """Clear the conversation history."""
        self._conversation_history.clear()
    
    async def optimize_prompt(self, user_prompt: str, provider_key: str = None, logger=None) -> Dict[str, Any]:
        """Optimize a user prompt using MCP context."""
        settings = self.settings_manager.get_settings()
        
        # Use default provider if none specified
        if provider_key is None:
            provider_key = settings.default_provider
        
        # Get MCP configurations
        gh_config_dict = settings.mcp.get("github", {})
        pg_config_dict = settings.mcp.get("postgres", {})
        
        # Convert to dataclass instances
        gh_config = MCPGitHubConfig.from_dict(gh_config_dict)
        pg_config = MCPPostgresConfig.from_dict(pg_config_dict)
        
        debug = {"github": None, "postgres": None, "optimizer": None}
        
        # Fetch GitHub issues
        issues_text = ""
        try:
            if logger:
                logger.log_mcp_connection("github", gh_config.to_dict())
            print(f"[MCP] Connecting to GitHub: {gh_config.url}")
            gh_connector = MCPConnectorFactory.create_github_connector(gh_config)
            print(f"[MCP] Fetching GitHub issues from repo: {gh_config.repo}")
            gh_result = await gh_connector.fetch_issues_and_comments(limit_issues=3, limit_comments=5)
            debug["github"] = gh_result.get("debug")
            issues_text = TextRenderer.render_issues_text(gh_result.get("issues", []))
            print(f"[MCP] GitHub result: {len(gh_result.get('issues', []))} issues, debug: {debug['github']}")
            if logger:
                logger.log_mcp_success("github", gh_result)
        except Exception as e:
            debug["github_error"] = str(e)
            print(f"[MCP] GitHub error: {e}")
            if logger:
                logger.log_mcp_error("github", str(e))
        
        # Fetch research papers
        papers_text = ""
        try:
            if logger:
                logger.log_mcp_connection("postgres", pg_config.to_dict())
            print(f"[MCP] Connecting to PostgreSQL: {pg_config.url}")
            pg_connector = MCPConnectorFactory.create_postgres_connector(pg_config)
            print(f"[MCP] Fetching research papers with SQL: {pg_config.sample_sql}")
            pg_result = await pg_connector.fetch_research_papers(limit_rows=8)
            debug["postgres"] = pg_result.get("debug")
            papers_text = TextRenderer.render_papers_text(pg_result.get("rows", []))
            print(f"[MCP] PostgreSQL result: {len(pg_result.get('rows', []))} rows, debug: {debug['postgres']}")
            if logger:
                logger.log_mcp_success("postgres", pg_result)
        except Exception as e:
            debug["postgres_error"] = str(e)
            print(f"[MCP] PostgreSQL error: {e}")
            if logger:
                logger.log_mcp_error("postgres", str(e))
        
        # Get provider configuration
        provider_config = settings.providers.get(provider_key) or settings.providers[settings.default_provider]
        context_window = provider_config.context_window or 128000
        
        print(f"[LLM] Using provider: {provider_key}, model: {provider_config.default_model}")
        print(f"[LLM] Context window: {context_window}")
        
        # Create usage tracking callback for real-time updates
        def usage_callback(input_tokens, output_tokens, api_calls=1):
            """Callback to track usage incrementally during optimization."""
            try:
                # Update usage in real-time
                self.settings_manager.update_provider_usage(
                    provider_key=provider_key,
                    user_tokens=input_tokens,
                    optimized_tokens=0,  # These are optimization calls, not user calls
                    response_tokens=output_tokens,
                    api_calls=api_calls
                )
                print(f"[USAGE] Updated usage for {provider_key}: input={input_tokens}, output={output_tokens}, calls={api_calls}")
            except Exception as e:
                print(f"[USAGE] Error updating usage: {e}")
        
        # Build optimized prompt with usage tracking
        optimizer = PromptOptimizer(settings.optimizer, settings.providers, user_provider=provider_key, usage_callback=usage_callback)
        result = optimizer.build_optimized_prompt(
            user_prompt=user_prompt,
            issues_text=issues_text,
            papers_text=papers_text,
            provider_cw_tokens=context_window,
            logger=logger
        )
        
        debug["optimizer"] = result.debug
        print(f"[LLM] Optimized prompt length: {len(result.optimized_prompt)} chars")
        print(f"[LLM] Optimizer debug: {result.debug}")
        
        return {
            "optimized_prompt": result.optimized_prompt,
            "debug": debug
        }
    
    async def send_message(self, user_prompt: str, provider_key: str = None, 
                          model: Optional[str] = None) -> ChatResponse:
        """Send a message and get a response."""
        settings = self.settings_manager.get_settings()
        
        # Use default provider if none specified
        if provider_key is None:
            provider_key = settings.default_provider
        
        # Get provider configuration
        provider_config = settings.providers.get(provider_key) or settings.providers[settings.default_provider]
        model = model or provider_config.default_model
        
        # Add user message to history
        self.add_message("user", user_prompt)
        
        # Get MCP contexts
        gh_config_dict = settings.mcp.get("github", {})
        pg_config_dict = settings.mcp.get("postgres", {})
        
        # Convert to dataclass instances
        gh_config = MCPGitHubConfig.from_dict(gh_config_dict)
        pg_config = MCPPostgresConfig.from_dict(pg_config_dict)
        
        # Fetch fresh data
        issues_text = ""
        papers_text = ""
        debug = {"mcp": {"github": None, "postgres": None}, "optimizer": None, "provider": None}
        
        try:
            gh_connector = MCPConnectorFactory.create_github_connector(gh_config)
            gh_result = await gh_connector.fetch_issues_and_comments(limit_issues=3, limit_comments=5)
            debug["mcp"]["github"] = gh_result.get("debug")
            issues_text = TextRenderer.render_issues_text(gh_result.get("issues", []))
        except Exception as e:
            debug["mcp"]["github_error"] = str(e)
        
        try:
            pg_connector = MCPConnectorFactory.create_postgres_connector(pg_config)
            pg_result = await pg_connector.fetch_research_papers(limit_rows=8)
            debug["mcp"]["postgres"] = pg_result.get("debug")
            papers_text = TextRenderer.render_papers_text(pg_result.get("rows", []))
        except Exception as e:
            debug["mcp"]["postgres_error"] = str(e)
        
        # Build optimized prompt
        context_window = provider_config.context_window or 128000
        optimizer = PromptOptimizer(settings.optimizer, settings.providers, user_provider=provider_key)
        opt_result = optimizer.build_optimized_prompt(
            user_prompt=user_prompt,
            issues_text=issues_text,
            papers_text=papers_text,
            provider_cw_tokens=context_window
        )
        
        debug["optimizer"] = opt_result.debug
        
        # Generate response
        try:
            provider = LLMProviderFactory.create_provider(provider_key, provider_config)
            
            system_prompt = self._get_system_prompt()
            final_prompt = opt_result.optimized_prompt
            
            raw_response = provider.complete(
                prompt=final_prompt,
                system=system_prompt,
                temperature=provider_config.temperature
            )
            
            # Parse response
            try:
                structured_response = json.loads(raw_response)
            except Exception:
                structured_response = {"answer": raw_response, "used_connectors": [], "citations": []}
            
            # Add assistant message to history
            self.add_message("assistant", structured_response.get("answer", raw_response))
            
            # Build debug info
            provider_debug = {
                "name": provider_config.name or provider_key,
                "model": model,
                "endpoint": provider_config.base_url,
                "request": {
                    "system_preview": system_prompt[:800],
                    "prompt_preview": final_prompt[:800],
                    "temperature": provider_config.temperature,
                },
                "response": {
                    "raw_preview": raw_response[:1400]
                },
                "parsed": {
                    "structured_preview": str(structured_response)[:1400]
                }
            }
            
            debug["provider"] = provider_debug
            debug["final_prompt_tokens_est"] = optimizer.estimate_tokens(final_prompt)
            
            return ChatResponse(
                text=raw_response,
                structured=json.dumps(structured_response, ensure_ascii=False, indent=2),
                debug=debug
            )
            
        except Exception as e:
            error_response = json.dumps({
                "answer": f"Provider error: {e}",
                "used_connectors": [],
                "citations": []
            })
            
            debug["provider"] = {
                "name": provider_config.name or provider_key,
                "model": model,
                "endpoint": provider_config.base_url,
                "error": str(e)
            }
            
            return ChatResponse(
                text=error_response,
                structured=error_response,
                debug=debug
            )
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the chat."""
        return """You are an AI Research Paper Analysis Assistant that helps developers and researchers by:

1. **Analyzing GitHub Issues**: Extract project requirements, technical specifications, and implementation needs from GitHub issues and comments
2. **Research Paper Discovery**: Find and analyze relevant AI research papers that match project requirements
3. **Recommendation Generation**: Provide actionable recommendations combining project requirements with research insights

**Your Capabilities:**
- Parse GitHub issues to understand project scope and technical requirements
- Match requirements with relevant research papers from the database
- Provide implementation guidance based on research findings
- Suggest relevant papers for literature reviews and gap analysis
- Identify research gaps and collaboration opportunities

**Response Format:** Reply ONLY with the JSON schema specified below.

Return ONLY valid JSON with keys:
{
  "answer": string,
  "used_connectors": string[],
  "citations": string[]
}"""


class ChatSessionManager:
    """Manages multiple chat sessions."""
    
    def __init__(self):
        self._sessions: Dict[str, ChatService] = {}
    
    def get_session(self, session_id: str, settings_manager: SettingsManager) -> ChatService:
        """Get or create a chat session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = ChatService(settings_manager)
        return self._sessions[session_id]
    
    def remove_session(self, session_id: str) -> None:
        """Remove a chat session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
    
    def clear_all_sessions(self) -> None:
        """Clear all chat sessions."""
        self._sessions.clear()
