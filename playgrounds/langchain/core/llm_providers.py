"""
LangChain-based LLM providers module.
"""
import asyncio
import math
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod

from langchain_core.language_models import BaseLLM
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.outputs import LLMResult
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from .models import LLMProvider, ProviderConfig, ChatResponse, TokenCount


class BaseLangChainProvider(LLMProvider):
    """Base class for LangChain-based LLM providers."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
        self._llm: Optional[BaseLLM] = None
    
    def get_context_window(self) -> int:
        """Get the context window size in tokens."""
        return self.config.context_window
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return max(1, math.ceil(len(text) / 4))
    
    def _trim_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trim text to fit within token limit."""
        if self._estimate_tokens(text) <= max_tokens:
            return text
        return text[:max(0, max_tokens * 4)]
    
    def _log_request(self, logger, provider: str, model: str, prompt: str, system: str = None, 
                    temperature: float = None, max_tokens: int = None):
        """Log LLM request if logger is provided."""
        if logger:
            logger.log_llm_request(provider, model, prompt, system, temperature, max_tokens)
    
    def _log_response(self, logger, provider: str, response: str, tokens_used: int = None):
        """Log LLM response if logger is provided."""
        if logger:
            logger.log_llm_response(provider, response, tokens_used)
    
    def _log_error(self, logger, provider: str, error: str):
        """Log LLM error if logger is provided."""
        if logger:
            logger.log_llm_error(provider, error)
    
    @abstractmethod
    def _create_llm(self) -> BaseLLM:
        """Create the LangChain LLM instance."""
        pass
    
    def _get_llm(self) -> BaseLLM:
        """Get or create the LLM instance."""
        if self._llm is None:
            self._llm = self._create_llm()
        return self._llm
    
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None) -> str:
        """Generate text completion (synchronous wrapper for async generate)."""
        # This is a synchronous wrapper for the async generate method
        # In a real implementation, you might want to use asyncio.run() or similar
        # For now, we'll raise an error to indicate this should be used asynchronously
        raise NotImplementedError("Use generate() method for async completion")
    
    async def generate(self, prompt: str, system: Optional[str] = None, 
                      temperature: Optional[float] = None, logger=None) -> ChatResponse:
        """Generate a response from the LLM."""
        try:
            llm = self._get_llm()
            
            # Prepare messages
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            # Calculate max tokens
            context_window = self.get_context_window()
            prompt_tokens = self._estimate_tokens(prompt)
            system_tokens = self._estimate_tokens(system) if system else 0
            total_input_tokens = prompt_tokens + system_tokens
            
            # Reserve some tokens for the response (25% of context window, but at least 1000)
            reserved_for_response = max(1000, int(context_window * 0.25))
            available_tokens = context_window - total_input_tokens - reserved_for_response
            provider_cap = self.config.max_completion_tokens
            max_tokens = max(100, min(available_tokens, provider_cap))
            
            # Log the request
            self._log_request(logger, self.config.name.lower(), self.config.default_model, 
                            prompt, system, temperature or self.config.temperature, max_tokens)
            
            # Generate response
            response = await llm.ainvoke(messages)
            
            # Extract response text
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Log the response
            self._log_response(logger, self.config.name.lower(), response_text)
            
            return ChatResponse(
                content=response_text,
                model=self.config.default_model,
                provider=self.config.name,
                tokens=TokenCount(
                    prompt_tokens=total_input_tokens,
                    completion_tokens=self._estimate_tokens(response_text),
                    total_tokens=total_input_tokens + self._estimate_tokens(response_text)
                ),
                debug_info={"provider": self.config.name, "model": self.config.default_model}
            )
            
        except Exception as e:
            error_msg = f"LLM generation failed: {str(e)}"
            self._log_error(logger, self.config.name.lower(), error_msg)
            raise RuntimeError(error_msg)


class AnthropicProvider(BaseLangChainProvider):
    """Anthropic Claude provider using LangChain."""
    
    def _create_llm(self) -> BaseLLM:
        """Create Anthropic LLM instance."""
        return ChatAnthropic(
            model=self.config.default_model,
            anthropic_api_key=self.config.api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_completion_tokens
        )


class OpenAIProvider(BaseLangChainProvider):
    """OpenAI provider using LangChain."""
    
    def _create_llm(self) -> BaseLLM:
        """Create OpenAI LLM instance."""
        return ChatOpenAI(
            model=self.config.default_model,
            openai_api_key=self.config.api_key,
            temperature=self.config.temperature,
            max_tokens=self.config.max_completion_tokens,
            base_url=self.config.base_url if self.config.base_url else None,
            organization=self.config.organization if self.config.organization else None
        )


class GoogleProvider(BaseLangChainProvider):
    """Google Gemini provider using LangChain."""
    
    def _create_llm(self) -> BaseLLM:
        """Create Google LLM instance."""
        return ChatGoogleGenerativeAI(
            model=self.config.default_model,
            google_api_key=self.config.api_key,
            temperature=self.config.temperature,
            max_output_tokens=self.config.max_completion_tokens
        )


class LLMProviderFactory:
    """Factory for creating LLM providers."""
    
    _providers = {
        "anthropic": AnthropicProvider,
        "openai": OpenAIProvider,
        "google": GoogleProvider
    }
    
    @classmethod
    def create_provider(cls, provider_key: str, config: ProviderConfig) -> LLMProvider:
        """Create an LLM provider instance."""
        if provider_key not in cls._providers:
            raise ValueError(f"Unknown provider: {provider_key}")
        
        provider_class = cls._providers[provider_key]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider keys."""
        return list(cls._providers.keys())
