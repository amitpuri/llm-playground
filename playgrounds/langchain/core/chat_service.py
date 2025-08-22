"""
Chat service using LangChain for managing conversations and LLM interactions.
"""
import asyncio
from typing import Dict, Any, Optional, List
from .models import ChatResponse, ChatMessage, MCPGitHubConfig, MCPPostgresConfig, LLMProvider, TokenCount
from .llm_providers import LLMProviderFactory
from .mcp_connectors import MCPConnectorFactory, GitHubMCPConnector, PostgresMCPConnector
from .prompt_optimizer import PromptOptimizer, TextRenderer
from .settings import SettingsManager
from .exceptions import (
    ChatServiceError, ProviderError, MCPError, MCPConnectionError,
    UsageLimitError, ValidationError
)


class ChatSessionManager:
    """Manages chat sessions and conversation history."""
    
    def __init__(self):
        self._sessions: Dict[str, List[ChatMessage]] = {}
    
    def get_session_history(self, session_id: str) -> List[ChatMessage]:
        """Get conversation history for a session."""
        return self._sessions.get(session_id, []).copy()
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to a session."""
        if session_id not in self._sessions:
            self._sessions[session_id] = []
        
        message = ChatMessage(role=role, content=content)
        self._sessions[session_id].append(message)
    
    def clear_session(self, session_id: str) -> None:
        """Clear conversation history for a session."""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
    
    def get_all_sessions(self) -> List[str]:
        """Get all session IDs."""
        return list(self._sessions.keys())


class ChatService:
    """Main chat service that coordinates all chat operations."""
    
    def __init__(self, settings_manager: SettingsManager, session_manager: Optional[ChatSessionManager] = None):
        self.settings_manager = settings_manager
        self.session_manager = session_manager or ChatSessionManager()
    
    def add_message(self, session_id: str, role: str, content: str) -> None:
        """Add a message to the conversation history."""
        self.session_manager.add_message(session_id, role, content)
    
    def get_conversation_history(self, session_id: str) -> List[ChatMessage]:
        """Get the conversation history for a session."""
        return self.session_manager.get_session_history(session_id)
    
    def clear_history(self, session_id: str) -> None:
        """Clear the conversation history for a session."""
        self.session_manager.clear_session(session_id)
    
    async def optimize_prompt(self, user_prompt: str, provider_key: str = None,
                            session_id: str = None, logger=None) -> Dict[str, Any]:
        """Optimize a user prompt using MCP context."""
        try:
            # Validate input
            if not user_prompt or not user_prompt.strip():
                raise ValidationError("User prompt cannot be empty", field="user_prompt")

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
            gh_result = {"issues": [], "debug": None}
            if gh_config.enabled:
                try:
                    if logger:
                        logger.log_mcp_connection("github", gh_config.to_dict())

                    gh_connector = MCPConnectorFactory.create_github_connector(gh_config)
                    
                    # Check if connector is properly enabled
                    if not gh_connector.is_enabled():
                        debug["github"] = {
                            "operation": "fetch_github_issues",
                            "response_time": 0.0,
                            "mcp_calls": [{
                                "disabled": True,
                                "reason": "connector_disabled",
                                "config": {
                                    "enabled": gh_config.enabled,
                                    "url": gh_config.url,
                                    "repo": gh_config.repo,
                                    "has_auth_token": bool(gh_config.auth_token)
                                }
                            }]
                        }
                    else:
                        # Test connection before fetching data
                        try:
                            test_client = await gh_connector.connect()
                            if test_client is None:
                                debug["github_error"] = "Failed to establish MCP connection"
                                debug["github"] = {
                                    "operation": "fetch_github_issues",
                                    "response_time": 0.0,
                                    "mcp_calls": [{
                                        "error_type": "ConnectionFailed",
                                        "details": "Client connection returned None",
                                        "config": {
                                            "url": gh_config.url,
                                            "repo": gh_config.repo,
                                            "has_auth_token": bool(gh_config.auth_token)
                                        }
                                    }]
                                }
                                if logger:
                                    logger.log_mcp_error("github", "Connection failed - client is None")
                            else:
                                # Proceed with data fetching
                                gh_result = await gh_connector.fetch_data(limit_issues=3, limit_comments=5)
                                debug["github"] = gh_result.get("debug")
                                issues_text = TextRenderer.render_issues_text(gh_result.get("issues", []))

                                if logger:
                                    logger.log_mcp_success("github", gh_result)
                        except Exception as conn_error:
                            debug["github_error"] = f"Connection error: {str(conn_error)}"
                            debug["github"] = {
                                "operation": "fetch_github_issues",
                                "response_time": 0.0,
                                "mcp_calls": [{
                                    "error_type": "ConnectionError",
                                    "details": str(conn_error),
                                    "config": {
                                        "url": gh_config.url,
                                        "repo": gh_config.repo,
                                        "has_auth_token": bool(gh_config.auth_token)
                                    }
                                }]
                            }
                            if logger:
                                logger.log_mcp_error("github", f"Connection error: {str(conn_error)}")
                except Exception as e:
                    debug["github_error"] = str(e)
                    debug["github"] = {
                        "operation": "fetch_github_issues",
                        "response_time": 0.0,
                        "mcp_calls": [{
                            "error_type": "GeneralError",
                            "details": str(e),
                            "config": {
                                "enabled": gh_config.enabled,
                                "url": gh_config.url,
                                "repo": gh_config.repo,
                                "has_auth_token": bool(gh_config.auth_token)
                            }
                        }]
                    }
                    if logger:
                        logger.log_mcp_error("github", str(e))
                    # Don't raise here, continue with optimization
            else:
                debug["github"] = {
                    "operation": "fetch_github_issues",
                    "response_time": 0.0,
                    "mcp_calls": [{
                        "disabled": True,
                        "reason": "config_disabled",
                        "config": {
                            "enabled": gh_config.enabled,
                            "url": gh_config.url,
                            "repo": gh_config.repo,
                            "has_auth_token": bool(gh_config.auth_token)
                        }
                    }]
                }

            # Fetch research papers
            papers_text = ""
            pg_result = {"rows": [], "debug": None}
            if pg_config.enabled:
                try:
                    if logger:
                        logger.log_mcp_connection("postgres", pg_config.to_dict())

                    pg_connector = MCPConnectorFactory.create_postgres_connector(pg_config)
                    
                    # Check if connector is properly enabled
                    if not pg_connector.is_enabled():
                        debug["postgres"] = {
                            "operation": "fetch_research_papers",
                            "response_time": 0.0,
                            "mcp_calls": [{
                                "disabled": True,
                                "reason": "connector_disabled",
                                "config": {
                                    "enabled": pg_config.enabled,
                                    "url": pg_config.url,
                                    "has_auth_token": bool(pg_config.auth_token)
                                }
                            }]
                        }
                    else:
                        # Test connection before fetching data
                        try:
                            test_client = await pg_connector.connect()
                            if test_client is None:
                                debug["postgres_error"] = "Failed to establish MCP connection"
                                debug["postgres"] = {
                                    "operation": "fetch_research_papers",
                                    "response_time": 0.0,
                                    "mcp_calls": [{
                                        "error_type": "ConnectionFailed",
                                        "details": "Client connection returned None",
                                        "config": {
                                            "url": pg_config.url,
                                            "has_auth_token": bool(pg_config.auth_token)
                                        }
                                    }]
                                }
                                if logger:
                                    logger.log_mcp_error("postgres", "Connection failed - client is None")
                            else:
                                # Proceed with data fetching
                                pg_result = await pg_connector.fetch_data(limit_rows=8)
                                debug["postgres"] = pg_result.get("debug")
                                papers_text = TextRenderer.render_papers_text(pg_result.get("rows", []))

                                if logger:
                                    logger.log_mcp_success("postgres", pg_result)
                        except Exception as conn_error:
                            debug["postgres_error"] = f"Connection error: {str(conn_error)}"
                            debug["postgres"] = {
                                "operation": "fetch_research_papers",
                                "response_time": 0.0,
                                "mcp_calls": [{
                                    "error_type": "ConnectionError",
                                    "details": str(conn_error),
                                    "config": {
                                        "url": pg_config.url,
                                        "has_auth_token": bool(pg_config.auth_token)
                                    }
                                }]
                            }
                            if logger:
                                logger.log_mcp_error("postgres", f"Connection error: {str(conn_error)}")
                except Exception as e:
                    debug["postgres_error"] = str(e)
                    debug["postgres"] = {
                        "operation": "fetch_research_papers",
                        "response_time": 0.0,
                        "mcp_calls": [{
                            "error_type": "GeneralError",
                            "details": str(e),
                            "config": {
                                "enabled": pg_config.enabled,
                                "url": pg_config.url,
                                "has_auth_token": bool(pg_config.auth_token)
                            }
                        }]
                    }
                    if logger:
                        logger.log_mcp_error("postgres", str(e))
                    # Don't raise here, continue with optimization
            else:
                debug["postgres"] = {
                    "operation": "fetch_research_papers",
                    "response_time": 0.0,
                    "mcp_calls": [{
                        "disabled": True,
                        "reason": "config_disabled",
                        "config": {
                            "enabled": pg_config.enabled,
                            "url": pg_config.url,
                            "has_auth_token": bool(pg_config.auth_token)
                        }
                    }]
                }

            # Get provider configuration
            provider_config = settings.providers.get(provider_key) or settings.providers[settings.default_provider]
            context_window = provider_config.context_window or 128000

            # Create usage tracking callback for real-time updates
            def usage_callback(usage_data: Dict[str, Any]):
                """Callback to track usage in real-time."""
                try:
                    self.settings_manager.update_provider_usage(
                        provider_key=provider_key,
                        user_tokens=usage_data.get("input_tokens", 0),
                        optimized_tokens=usage_data.get("optimized_tokens", 0),
                        response_tokens=usage_data.get("output_tokens", 0),
                        api_calls=1
                    )
                except Exception as e:
                    if logger:
                        logger.log_error(f"Usage tracking error: {e}")

            # Optimize the prompt
            optimizer = PromptOptimizer(settings.optimizer)
            optimization_result = optimizer.optimize_prompt(
                user_prompt=user_prompt,
                github_issues=gh_result.get("issues", []) if "github_error" not in debug and gh_config.enabled else None,
                research_papers=pg_result.get("rows", []) if "postgres_error" not in debug and pg_config.enabled else None
            )

            optimized_prompt = optimization_result["optimized_prompt"]
            debug["optimizer"] = optimization_result["debug"]

            # Create LLM provider
            provider = LLMProviderFactory.create_provider(provider_key, provider_config)

            # Generate response
            try:
                response = await provider.generate(
                    prompt=optimized_prompt,
                    logger=logger
                )

                # Update usage
                if response.tokens:
                    usage_callback(response.tokens)

                # Add messages to session if session_id provided
                if session_id:
                    self.add_message(session_id, "user", user_prompt)
                    self.add_message(session_id, "assistant", response.content)

                return {
                    "optimized_prompt": optimized_prompt,
                    "response": response.content,
                    "debug": debug,
                    "usage": response.tokens
                }

            except Exception as e:
                if logger:
                    logger.log_error(f"LLM generation failed: {str(e)}")

                return {
                    "optimized_prompt": optimized_prompt,
                    "response": f"Error: {str(e)}",
                    "debug": debug,
                    "error": str(e)
                }

        except Exception as e:
            if logger:
                logger.log_error(f"Prompt optimization failed: {str(e)}")

            return {
                "optimized_prompt": user_prompt,
                "response": f"Error during optimization: {str(e)}",
                "debug": {"error": str(e)},
                "error": str(e)
            }
    
    async def send_message(self, user_prompt: str, provider_key: str = None, 
                          model: str = None, session_id: str = None, logger=None) -> ChatResponse:
        """Send a chat message and get a response."""
        settings = self.settings_manager.get_settings()
        
        # Use default provider if none specified
        if provider_key is None:
            provider_key = settings.default_provider
        
        # Get provider configuration
        provider_config = settings.providers.get(provider_key)
        if not provider_config:
            raise ValueError(f"Provider {provider_key} not found or not configured")
        
        # Override model if specified
        if model:
            provider_config = provider_config.__class__(**provider_config.__dict__)
            provider_config.default_model = model
        
        # Create LLM provider
        provider = LLMProviderFactory.create_provider(provider_key, provider_config)
        
        # Get conversation history for context
        conversation_history = []
        if session_id:
            conversation_history = self.get_conversation_history(session_id)
        
        # Build system prompt with conversation context
        system_prompt = None
        if conversation_history:
            # Include recent conversation history in system prompt
            recent_messages = conversation_history[-6:]  # Last 6 messages
            context_parts = ["Previous conversation:"]
            for msg in recent_messages:
                context_parts.append(f"{msg.role}: {msg.content}")
            system_prompt = "\n".join(context_parts)
        
        # Generate response
        try:
            response = await provider.generate(
                prompt=user_prompt,
                system=system_prompt,
                logger=logger
            )
            
            # Update usage
            if response.tokens:
                self.settings_manager.update_provider_usage(
                    provider_key=provider_key,
                    user_tokens=response.tokens.prompt_tokens,
                    response_tokens=response.tokens.completion_tokens,
                    api_calls=1
                )
            
            # Add messages to session if session_id provided
            if session_id:
                self.add_message(session_id, "user", user_prompt)
                self.add_message(session_id, "assistant", response.content)
            
            return response
            
        except Exception as e:
            error_msg = f"Chat failed: {str(e)}"
            if logger:
                logger.log_error(error_msg)
            
            return ChatResponse(
                content=error_msg,
                model="",
                provider="",
                tokens=TokenCount(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                debug_info={"error": str(e)}
            )
