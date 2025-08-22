"""
LLM providers module following the Strategy pattern.
Each provider implements the LLMProvider interface.
"""
import requests
import math
from typing import Optional, Dict, Any
from abc import ABC, abstractmethod
from .models import LLMProvider, ProviderConfig
import json


class BaseLLMProvider(LLMProvider):
    """Base class for LLM providers with common functionality."""
    
    def __init__(self, config: ProviderConfig):
        self.config = config
    
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


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider implementation."""
    
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None, logger=None) -> str:
        """Generate completion using OpenAI API."""
        if not self.config.api_key:
            print(f"[LLM-OpenAI] Error: API key missing")
            raise RuntimeError("OpenAI API key missing")
        
        url = self._get_endpoint("chat/completions")
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        
        # Calculate dynamic max_completion_tokens based on context window and prompt length
        context_window = self.get_context_window()
        prompt_tokens = self._estimate_tokens(prompt)
        system_tokens = self._estimate_tokens(system) if system else 0
        total_input_tokens = prompt_tokens + system_tokens
        
        # Reserve some tokens for the response (25% of context window, but at least 1000)
        reserved_for_response = max(1000, int(context_window * 0.25))
        
        # Calculate available tokens for completion
        available_tokens = context_window - total_input_tokens - reserved_for_response
        
        # Ensure we have reasonable limits and respect provider-specific cap
        provider_cap = self.config.max_completion_tokens
        max_completion_tokens = max(100, min(available_tokens, provider_cap))
        
        # Log the request
        self._log_request(logger, "openai", self.config.default_model, prompt, system, 
                         temperature or self.config.temperature, max_completion_tokens)
        
        payload = {
            "model": self.config.default_model,
            "messages": messages,
            "max_completion_tokens": max_completion_tokens
        }
        
        # For newer OpenAI models (like GPT-4o, GPT-5), don't include temperature parameter
        # as they only support the default value (1.0) and reject custom values
        # This avoids the "Unsupported value: 'temperature' does not support 0.2" error
        # requested_temp = temperature or self.config.temperature
        # payload["temperature"] = requested_temp  # Commented out to avoid API errors
        
        print(f"[LLM-OpenAI] API call to: {url}")
        print(f"[LLM-OpenAI] Model: {self.config.default_model}")
        print(f"[LLM-OpenAI] Temperature: {temperature or self.config.temperature}")
        print(f"[LLM-OpenAI] Context window: {context_window:,} tokens")
        print(f"[LLM-OpenAI] Prompt tokens: {prompt_tokens:,}")
        print(f"[LLM-OpenAI] System tokens: {system_tokens:,}")
        print(f"[LLM-OpenAI] Total input tokens: {total_input_tokens:,}")
        print(f"[LLM-OpenAI] Reserved for response: {reserved_for_response:,}")
        print(f"[LLM-OpenAI] Available for completion: {available_tokens:,}")
        print(f"[LLM-OpenAI] Provider cap: {provider_cap:,}")
        print(f"[LLM-OpenAI] Max completion tokens: {max_completion_tokens:,}")
        print(f"[LLM-OpenAI] Prompt length: {len(prompt)} chars")
        print(f"[LLM-OpenAI] System prompt: {system[:100] if system else 'None'}...")
        print(f"[LLM-OpenAI] Payload: {json.dumps(payload, indent=2)}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            body = ""
            try:
                body = response.text[:2000]
                print(f"[LLM-OpenAI] Full error response: {body}")
            except Exception:
                pass
            print(f"[LLM-OpenAI] API error: {e} :: {body}")
            self._log_error(logger, "openai", f"{e} :: {body}")
            raise requests.HTTPError(f"{e} :: {body}") from None
        
        data = response.json()
        print(f"[LLM-OpenAI] Full API response: {json.dumps(data, indent=2)}")
        
        # Check if we have choices
        if not data.get("choices"):
            print(f"[LLM-OpenAI] Error: No choices in response")
            return ""
        
        # Check if the first choice has a message
        first_choice = data["choices"][0]
        if not first_choice.get("message"):
            print(f"[LLM-OpenAI] Error: No message in first choice")
            return ""
        
        # Check if the message has content
        message = first_choice["message"]
        if not message.get("content"):
            print(f"[LLM-OpenAI] Error: No content in message")
            # Check if it's due to length limit
            if first_choice.get("finish_reason") == "length":
                print(f"[LLM-OpenAI] Warning: Response truncated due to length limit")
                return "Response was truncated due to length limit. Please try with a shorter prompt or increase token limits."
            return ""
        
        result = message["content"].strip()
        
        # If result is empty but we have a finish reason, provide context
        if not result and first_choice.get("finish_reason"):
            print(f"[LLM-OpenAI] Warning: Empty content with finish_reason: {first_choice['finish_reason']}")
            if first_choice["finish_reason"] == "length":
                error_msg = "Response was truncated due to length limit. Please try with a shorter prompt."
                self._log_error(logger, "openai", error_msg)
                return error_msg
            elif first_choice["finish_reason"] == "stop":
                error_msg = "Response completed but was empty. Please try rephrasing your request."
                self._log_error(logger, "openai", error_msg)
                return error_msg
            else:
                error_msg = f"Response completed with finish reason: {first_choice['finish_reason']}. Please try again."
                self._log_error(logger, "openai", error_msg)
                return error_msg
        
        print(f"[LLM-OpenAI] Response length: {len(result)} chars")
        print(f"[LLM-OpenAI] Response preview: {result[:200]}...")
        
        # Log the response
        self._log_response(logger, "openai", result)
        
        return result
    
    def _get_endpoint(self, resource: str = "chat/completions") -> str:
        """Get the correct endpoint URL."""
        base = (self.config.base_url or "https://api.openai.com").rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/{resource.lstrip('/')}"
        return f"{base}/v1/{resource.lstrip('/')}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic API provider implementation."""
    
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None, logger=None) -> str:
        """Generate completion using Anthropic API."""
        if not self.config.api_key:
            print(f"[LLM-Anthropic] Error: API key missing")
            raise RuntimeError("Anthropic API key missing")
        
        url = self._get_endpoint("messages")
        headers = {
            "x-api-key": self.config.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        
        # Calculate dynamic max_tokens based on context window and prompt length
        context_window = self.get_context_window()
        prompt_tokens = self._estimate_tokens(prompt)
        system_tokens = self._estimate_tokens(system) if system else 0
        total_input_tokens = prompt_tokens + system_tokens
        
        # Reserve some tokens for the response (25% of context window, but at least 1000)
        reserved_for_response = max(1000, int(context_window * 0.25))
        
        # Calculate available tokens for completion
        available_tokens = context_window - total_input_tokens - reserved_for_response
        
        # Ensure we have reasonable limits and respect provider-specific cap
        provider_cap = self.config.max_completion_tokens
        max_tokens = max(100, min(available_tokens, provider_cap))
        
        # Log the request
        self._log_request(logger, "anthropic", self.config.default_model, prompt, system, 
                         temperature or self.config.temperature, max_tokens)
        
        payload = {
            "model": self.config.default_model,
            "max_tokens": max_tokens,
            "temperature": temperature or self.config.temperature,
            "system": system or "You are a helpful assistant.",
            "messages": [{"role": "user", "content": prompt}],
        }
        
        print(f"[LLM-Anthropic] API call to: {url}")
        print(f"[LLM-Anthropic] Model: {self.config.default_model}")
        print(f"[LLM-Anthropic] Temperature: {temperature or self.config.temperature}")
        print(f"[LLM-Anthropic] Context window: {context_window:,} tokens")
        print(f"[LLM-Anthropic] Prompt tokens: {prompt_tokens:,}")
        print(f"[LLM-Anthropic] System tokens: {system_tokens:,}")
        print(f"[LLM-Anthropic] Total input tokens: {total_input_tokens:,}")
        print(f"[LLM-Anthropic] Reserved for response: {reserved_for_response:,}")
        print(f"[LLM-Anthropic] Available for completion: {available_tokens:,}")
        print(f"[LLM-Anthropic] Provider cap: {provider_cap:,}")
        print(f"[LLM-Anthropic] Max tokens: {max_tokens:,}")
        print(f"[LLM-Anthropic] Prompt length: {len(prompt)} chars")
        print(f"[LLM-Anthropic] System prompt: {system[:100] if system else 'None'}...")
        
        response = requests.post(url, headers=headers, json=payload, timeout=180)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            body = ""
            try:
                body = response.text[:2000]
            except Exception:
                pass
            print(f"[LLM-Anthropic] API error: {e} :: {body}")
            raise requests.HTTPError(f"{e} :: {body}") from None
        
        data = response.json()
        output = ""
        for content in data.get("content", []):
            if isinstance(content, dict) and content.get("type") == "text":
                output += content.get("text", "")
        
        result = output.strip()
        print(f"[LLM-Anthropic] Response length: {len(result)} chars")
        print(f"[LLM-Anthropic] Response preview: {result[:200]}...")
        
        # Log the response
        self._log_response(logger, "anthropic", result)
        
        return result
    
    def _get_endpoint(self, resource: str = "messages") -> str:
        """Get the correct endpoint URL."""
        base = (self.config.base_url or "").rstrip("/")
        if base.endswith("/v1"):
            return f"{base}/{resource.lstrip('/')}"
        return f"{base}/v1/{resource.lstrip('/')}"


class OllamaProvider(BaseLLMProvider):
    """Ollama local provider implementation."""
    
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None, logger=None) -> str:
        """Generate completion using Ollama API."""
        url = f"{self.config.base_url.rstrip('/')}/api/generate"
        
        full_prompt = prompt
        if system:
            full_prompt = f"{system}\n\n{prompt}".strip()
        
        # Calculate dynamic max_tokens based on context window and prompt length
        context_window = self.get_context_window()
        prompt_tokens = self._estimate_tokens(full_prompt)
        
        # Reserve some tokens for the response (25% of context window, but at least 1000)
        reserved_for_response = max(1000, int(context_window * 0.25))
        
        # Calculate available tokens for completion
        available_tokens = context_window - prompt_tokens - reserved_for_response
        
        # Ensure we have reasonable limits and respect provider-specific cap
        provider_cap = self.config.max_completion_tokens
        max_tokens = max(100, min(available_tokens, provider_cap))
        
        # Log the request
        self._log_request(logger, "ollama", self.config.default_model, prompt, system, 
                         temperature or self.config.temperature, max_tokens)
        
        payload = {
            "model": self.config.default_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": temperature or self.config.temperature,
                "num_predict": max_tokens
            }
        }
        
        print(f"[LLM-Ollama] API call to: {url}")
        print(f"[LLM-Ollama] Model: {self.config.default_model}")
        print(f"[LLM-Ollama] Context window: {context_window:,} tokens")
        print(f"[LLM-Ollama] Prompt tokens: {prompt_tokens:,}")
        print(f"[LLM-Ollama] Max completion tokens: {max_tokens:,}")
        
        response = requests.post(url, json=payload, timeout=180)
        response.raise_for_status()
        
        result = response.json().get("response", "").strip()
        print(f"[LLM-Ollama] Response length: {len(result)} chars")
        print(f"[LLM-Ollama] Response preview: {result[:200]}...")
        
        # Log the response
        self._log_response(logger, "ollama", result)
        
        return result


class GoogleProvider(BaseLLMProvider):
    """Google Gemini API provider implementation."""
    
    def complete(self, prompt: str, system: Optional[str] = None, 
                temperature: Optional[float] = None, logger=None) -> str:
        """Generate completion using Google Gemini API."""
        endpoint = f"{self.config.base_url.rstrip('/')}/v1beta/models/{self.config.default_model}:generateContent"
        params = {"key": self.config.api_key} if self.config.api_key else {}
        
        text = f"{system}\n\n{prompt}".strip() if system else prompt
        
        # Log the request
        self._log_request(logger, "google", self.config.default_model, prompt, system, 
                         temperature or self.config.temperature)
        
        payload = {
            "contents": [{"role": "user", "parts": [{"text": text}]}],
            "generationConfig": {"temperature": temperature or self.config.temperature}
        }
        
        response = requests.post(endpoint, params=params, json=payload, timeout=180)
        response.raise_for_status()
        
        data = response.json()
        try:
            parts = data["candidates"][0]["content"]["parts"]
            combined = "".join(part.get("text", "") for part in parts)
            result = combined.strip()
            
            # Log the response
            self._log_response(logger, "google", result)
            
            return result
        except Exception as e:
            error_msg = f"Failed to parse Google response: {e}"
            self._log_error(logger, "google", error_msg)
            return str(data)[:2000]


class LLMProviderFactory:
    """Factory for creating LLM provider instances."""
    
    _providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "google": GoogleProvider,
    }
    
    @classmethod
    def create_provider(cls, provider_type: str, config: ProviderConfig) -> LLMProvider:
        """Create a provider instance based on type."""
        if provider_type not in cls._providers:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        provider_class = cls._providers[provider_type]
        return provider_class(config)
    
    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Get list of available provider types."""
        return list(cls._providers.keys())
