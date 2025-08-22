"""
Token calculator for various LLM providers using LangChain tokenizers.
"""
import math
from typing import Dict, Any, List, Optional
import tiktoken

from .models import TokenCount


class TokenCalculator:
    """Token calculator for different LLM providers."""
    
    def __init__(self):
        self._encoders: Dict[str, Any] = {}
        self._model_info: Dict[str, Dict[str, Any]] = {
            "openai": {
                "models": {
                    "gpt-5": {"context_window": 128000, "input_cost_per_1k": 0.005, "output_cost_per_1k": 0.015},
                    "gpt-4o": {"context_window": 128000, "input_cost_per_1k": 0.005, "output_cost_per_1k": 0.015},
                    "gpt-4o-mini": {"context_window": 128000, "input_cost_per_1k": 0.00015, "output_cost_per_1k": 0.0006},
                    "gpt-4-turbo": {"context_window": 128000, "input_cost_per_1k": 0.01, "output_cost_per_1k": 0.03},
                    "gpt-3.5-turbo": {"context_window": 16385, "input_cost_per_1k": 0.0015, "output_cost_per_1k": 0.002}
                },
                "default_model": "gpt-5"
            },
            "anthropic": {
                "models": {
                    "claude-opus-4-0": {"context_window": 200000, "input_cost_per_1k": 0.015, "output_cost_per_1k": 0.075},
                    "claude-sonnet-4-0": {"context_window": 200000, "input_cost_per_1k": 0.003, "output_cost_per_1k": 0.015},
                    "claude-haiku-3-0": {"context_window": 200000, "input_cost_per_1k": 0.00025, "output_cost_per_1k": 0.00125}
                },
                "default_model": "claude-opus-4-0"
            },
            "ollama": {
                "models": {
                    "llama3.2": {"context_window": 8000, "input_cost_per_1k": 0.0, "output_cost_per_1k": 0.0},
                    "llama3.1": {"context_window": 8000, "input_cost_per_1k": 0.0, "output_cost_per_1k": 0.0},
                    "mistral": {"context_window": 8000, "input_cost_per_1k": 0.0, "output_cost_per_1k": 0.0},
                    "codellama": {"context_window": 8000, "input_cost_per_1k": 0.0, "output_cost_per_1k": 0.0}
                },
                "default_model": "llama3.2"
            },
            "google": {
                "models": {
                    "gemini-pro": {"context_window": 32768, "input_cost_per_1k": 0.0005, "output_cost_per_1k": 0.0015},
                    "gemini-flash": {"context_window": 1000000, "input_cost_per_1k": 0.000075, "output_cost_per_1k": 0.0003},
                    "gemini-nano": {"context_window": 32768, "input_cost_per_1k": 0.00025, "output_cost_per_1k": 0.00075}
                },
                "default_model": "gemini-pro"
            }
        }
    
    def _get_encoder(self, provider: str) -> Any:
        """Get or create tokenizer encoder for a provider."""
        if provider not in self._encoders:
            if provider == "openai":
                self._encoders[provider] = tiktoken.get_encoding("cl100k_base")
            elif provider == "anthropic":
                self._encoders[provider] = tiktoken.get_encoding("cl100k_base")
            elif provider == "google":
                # Google uses a different tokenizer, but we'll approximate with GPT-4 tokenizer
                self._encoders[provider] = tiktoken.get_encoding("cl100k_base")
            else:
                # Default to GPT-4 tokenizer for unknown providers
                self._encoders[provider] = tiktoken.get_encoding("cl100k_base")
        
        return self._encoders[provider]
    
    def count_tokens(self, text: str, provider: str = "openai", model: str = None) -> TokenCount:
        """Count tokens for a given text and provider."""
        if not text:
            return TokenCount(
                input_tokens=0,
                output_tokens=0,
                total_tokens=0,
                characters=0,
                words=0,
                estimated_cost=0.0,
                model=model or self._model_info[provider]["default_model"],
                provider=provider
            )
        
        # Get encoder
        encoder = self._get_encoder(provider)
        
        # Count tokens
        tokens = encoder.encode(text)
        token_count = len(tokens)
        
        # Count characters and words
        characters = len(text)
        words = len(text.split())
        
        # Get model info
        model = model or self._model_info[provider]["default_model"]
        model_info = self._model_info[provider]["models"].get(model, {})
        
        # Calculate estimated cost
        input_cost_per_1k = model_info.get("input_cost_per_1k", 0.001)
        estimated_cost = (token_count / 1000) * input_cost_per_1k
        
        return TokenCount(
            input_tokens=token_count,
            output_tokens=0,
            total_tokens=token_count,
            characters=characters,
            words=words,
            estimated_cost=estimated_cost,
            model=model,
            provider=provider
        )
    
    def analyze_text(self, text: str, providers: List[str] = None) -> Dict[str, Any]:
        """Comprehensive text analysis with token counts for specified providers."""
        if providers is None:
            providers = ["openai", "anthropic", "google"]
        
        analysis = {
            "text_length": len(text),
            "characters": len(text),
            "words": len(text.split()),
            "providers": {}
        }
        
        for provider in providers:
            if provider in self._model_info:
                token_count = self.count_tokens(text, provider)
                analysis["providers"][provider] = {
                    "input_tokens": token_count.input_tokens,
                    "output_tokens": token_count.output_tokens,
                    "total_tokens": token_count.total_tokens,
                    "estimated_cost": token_count.estimated_cost,
                    "model": token_count.model,
                    "context_window": self._model_info[provider]["models"].get(token_count.model, {}).get("context_window", 0)
                }
        
        return analysis
    
    def get_available_models(self, provider: str) -> List[str]:
        """Get available models for a specific provider."""
        if provider in self._model_info:
            return list(self._model_info[provider]["models"].keys())
        return []
    
    def get_model_info(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific model."""
        if provider in self._model_info and model in self._model_info[provider]["models"]:
            return self._model_info[provider]["models"][model]
        return None
    
    def estimate_cost(self, input_tokens: int, output_tokens: int, provider: str = "openai", model: str = None) -> float:
        """Estimate cost for a complete request."""
        if provider not in self._model_info:
            return 0.0
        
        model = model or self._model_info[provider]["default_model"]
        model_info = self._model_info[provider]["models"].get(model, {})
        
        input_cost_per_1k = model_info.get("input_cost_per_1k", 0.001)
        output_cost_per_1k = model_info.get("output_cost_per_1k", 0.002)
        
        input_cost = (input_tokens / 1000) * input_cost_per_1k
        output_cost = (output_tokens / 1000) * output_cost_per_1k
        
        return input_cost + output_cost
    
    def get_context_window(self, provider: str, model: str = None) -> int:
        """Get context window size for a provider/model combination."""
        if provider not in self._model_info:
            return 128000  # Default fallback
        
        model = model or self._model_info[provider]["default_model"]
        model_info = self._model_info[provider]["models"].get(model, {})
        
        return model_info.get("context_window", 128000)


# Global token calculator instance
token_calculator = TokenCalculator()
