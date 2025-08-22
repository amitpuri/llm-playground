"""
Prompt optimizer module following the Strategy pattern.
Handles summarization and prompt optimization.
"""
import math
import textwrap
from typing import Dict, Any, Tuple, Optional
from .models import OptimizerConfig, OptimizedPromptResult
from .llm_providers import LLMProviderFactory, LLMProvider
import json


class PromptOptimizer:
    """Main prompt optimizer that coordinates summarization and optimization."""
    
    def __init__(self, config: OptimizerConfig, providers: Dict[str, Any], user_provider: str = None, usage_callback=None):
        self.config = config
        self.providers = providers
        self.user_provider = user_provider or config.provider
        self._optimizer_provider = None
        self.usage_callback = usage_callback  # Callback to track usage incrementally
    
    def _get_optimizer_provider(self) -> LLMProvider:
        """Get the LLM provider for optimization tasks."""
        if self._optimizer_provider is None:
            # Use user's selected provider if available, otherwise fall back to optimizer config
            provider_key = self.user_provider if self.user_provider in self.providers else self.config.provider
            provider_config = self.providers.get(provider_key)
            if not provider_config:
                raise RuntimeError(f"Provider '{provider_key}' not configured")
            
            print(f"[OPTIMIZER] Using provider: {provider_key} (user selected: {self.user_provider}, config default: {self.config.provider})")
            
            self._optimizer_provider = LLMProviderFactory.create_provider(
                provider_key, provider_config
            )
        
        return self._optimizer_provider
    
    def estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return max(1, math.ceil(len(text) / 4))
    
    def trim_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trim text to fit within token limit."""
        if self.estimate_tokens(text) <= max_tokens:
            return text
        return text[:max(0, max_tokens * 4)]
    
    def summarize_to_tokens(self, text: str, target_tokens: int, logger=None) -> str:
        """Summarize text to fit within token budget."""
        if not text:
            return text
        
        try:
            provider = self._get_optimizer_provider()
            system_prompt = "You compress content faithfully. Keep concrete facts, IDs, numbers, names. Prefer bullets."
            prompt = f"""Summarize the following to <= {target_tokens} tokens (approx).
Keep key facts, titles, dates, URLs, and short comment insights.

CONTENT:
{text}
"""
            result = provider.complete(prompt, system=system_prompt, temperature=self.config.temperature, logger=logger)
            output = result.strip()
            
            # Track usage for this summarization call
            if self.usage_callback:
                input_tokens = self.estimate_tokens(prompt)
                output_tokens = self.estimate_tokens(output)
                self.usage_callback(input_tokens, output_tokens, 1)
            
            if self.estimate_tokens(output) > target_tokens:
                return self.trim_to_tokens(output, target_tokens)
            
            return output
        except Exception:
            return self.trim_to_tokens(text, target_tokens)
    
    def build_optimized_prompt(self, user_prompt: str, issues_text: str, 
                             papers_text: str, provider_cw_tokens: int, logger=None) -> OptimizedPromptResult:
        """Build an optimized prompt with dual context."""
        # Get the actual provider being used
        actual_provider = self.user_provider if self.user_provider in self.providers else self.config.provider
        provider_config = self.providers.get(actual_provider)
        
        # Handle both ProviderConfig objects and dictionaries
        if hasattr(provider_config, 'default_model'):
            # It's a ProviderConfig object
            default_model = provider_config.default_model or "unknown"
        elif isinstance(provider_config, dict):
            # It's a dictionary
            default_model = provider_config.get("default_model", "unknown")
        else:
            default_model = "unknown"
        
        debug = {
            "provider_context_window": provider_cw_tokens, 
            "optimizer": {
                "provider": actual_provider,
                "model": default_model,
                "temperature": self.config.temperature,
                "max_tokens": getattr(self.config, 'max_tokens', 1000),
                "max_context_usage": getattr(self.config, 'max_context_usage', 0.8)
            }
        }
        
        # Calculate budgets with optimizer limits
        reserve_reply = int(provider_cw_tokens * 0.25)
        reserve_system = 800
        
        # Apply optimizer limits
        max_context_usage = self.config.max_context_usage if hasattr(self.config, 'max_context_usage') else 0.8
        max_tokens = self.config.max_tokens if hasattr(self.config, 'max_tokens') else 1000
        
        # Calculate available budget based on context usage limit
        available_context = int(provider_cw_tokens * max_context_usage)
        prompt_budget = max(1000, available_context - reserve_reply - reserve_system)
        
        # Apply max_tokens limit
        prompt_budget = min(prompt_budget, max_tokens)
        
        # Add applied_budget to debug info after calculation
        debug["optimizer"]["applied_budget"] = prompt_budget
        
        context_budget_total = int(prompt_budget * 0.45)
        issues_budget = max(150, context_budget_total // 2)
        papers_budget = max(150, context_budget_total - issues_budget)
        instruction_budget = max(400, prompt_budget - context_budget_total)
        user_budget = max(200, int(instruction_budget * 0.45))
        
        # Process user prompt
        user_final = (user_prompt if self.estimate_tokens(user_prompt) <= user_budget 
                     else self.trim_to_tokens(user_prompt, user_budget))
        
        # Summarize contexts
        issues_sum = (self.summarize_to_tokens(issues_text, issues_budget, logger) if issues_text else "")
        papers_sum = (self.summarize_to_tokens(papers_text, papers_budget, logger) if papers_text else "")
        
        # Optimize instruction
        try:
            provider = self._get_optimizer_provider()
            system_prompt = "You are a specialized prompt optimizer for AI research paper analysis workflows."
            prompt = f"""Rewrite the user request into a crisp, actionable instruction optimized for research paper analysis and GitHub issue integration.

**Optimization Guidelines:**
- Keep the instruction <= {instruction_budget} tokens (approx)
- Be specific and structured for research paper matching
- Include concrete references (issue #, URLs, table/column names) when present
- Focus on extracting requirements from GitHub issues and matching with research papers
- Emphasize implementation guidance and literature review aspects
- Do NOT include any 'Context:' sections—return only the instruction text

**Research Paper Workflow Focus:**
- Extract technical requirements from GitHub issues
- Match requirements with relevant AI research papers
- Provide implementation recommendations based on research findings
- Suggest papers for literature reviews and gap analysis

User request:
{user_final}

Context A (GitHub Issues, summarized):
{issues_sum}

Context B (Research Papers, summarized):
{papers_sum}
"""
            optimized_instruction = provider.complete(
                prompt, system=system_prompt, temperature=self.config.temperature, logger=logger
            ).strip() or user_final
            
            # Track usage for this optimization call
            if self.usage_callback:
                input_tokens = self.estimate_tokens(prompt)
                output_tokens = self.estimate_tokens(optimized_instruction)
                self.usage_callback(input_tokens, output_tokens, 1)
            
            if self.estimate_tokens(optimized_instruction) > instruction_budget:
                optimized_instruction = self.summarize_to_tokens(optimized_instruction, instruction_budget, logger)
        except Exception as e:
            debug["optimizer_error"] = str(e)
            optimized_instruction = f"""Analyze the user request by combining GitHub issues/comments with research paper insights to provide comprehensive recommendations.

**Analysis Approach:**
- Extract project requirements and technical specifications from GitHub issues
- Match requirements with relevant AI research papers from the database
- Provide implementation guidance based on research findings
- Suggest relevant papers for literature review and gap analysis

User request:
{user_final}"""
        
        # Final budget adjustment if needed
        total_now = (self.estimate_tokens(optimized_instruction) + 
                    self.estimate_tokens(issues_sum) + 
                    self.estimate_tokens(papers_sum))
        
        if total_now > prompt_budget:
            overflow = total_now - prompt_budget
            cur_i = self.estimate_tokens(issues_sum) or 1
            cur_p = self.estimate_tokens(papers_sum) or 1
            total_c = cur_i + cur_p
            reduce_i = int(overflow * (cur_i / total_c))
            reduce_p = overflow - reduce_i
            new_i_budget = max(100, cur_i - reduce_i)
            new_p_budget = max(100, cur_p - reduce_p)
            issues_sum = self.summarize_to_tokens(issues_sum, new_i_budget, logger)
            papers_sum = self.summarize_to_tokens(papers_sum, new_p_budget, logger)
        
        # Build final prompt
        final_prompt = f"""{optimized_instruction}

**GitHub Issues Context** (Project Requirements & Specifications):
{issues_sum or '(none)'} 

**Research Papers Context** (AI Research Database):
{papers_sum or '(none)'}"""
        
        # Final check and trim if needed
        if self.estimate_tokens(final_prompt) > prompt_budget:
            rem = prompt_budget - self.estimate_tokens(optimized_instruction)
            half = max(80, rem // 2)
            issues_sum = self.summarize_to_tokens(issues_sum, half, logger)
            papers_sum = self.summarize_to_tokens(papers_sum, rem - half, logger)
            final_prompt = f"""{optimized_instruction}

**GitHub Issues Context** (Project Requirements & Specifications):
{issues_sum or '(none)'} 

**Research Papers Context** (AI Research Database):
{papers_sum or '(none)'}"""
        
        budgets = {
            "reserve_reply": reserve_reply,
            "reserve_system": reserve_system,
            "prompt_budget_total": prompt_budget,
            "instruction_budget": instruction_budget,
            "context_budget_total": context_budget_total,
            "issues_budget": issues_budget,
            "papers_budget": papers_budget,
            "user_budget": user_budget,
        }
        
        return OptimizedPromptResult(
            optimized_prompt=final_prompt,
            debug=debug,
            budgets=budgets,
            final_tokens_est=self.estimate_tokens(final_prompt)
        )


class TextRenderer:
    """Utility class for rendering data as text."""
    
    @staticmethod
    def render_issues_text(issues: list) -> str:
        """Render GitHub issues as text."""
        parts = []
        for issue in issues:
            num = issue.get("number")
            title = issue.get("title") or ""
            url = issue.get("url") or ""
            state = issue.get("state") or ""
            updated = issue.get("updated_at") or ""
            labels = ", ".join([l for l in (issue.get("labels") or []) if l]) or "(none)"
            body = (issue.get("body") or "").strip()
            
            parts.append(
                f"Issue #{num}: {title}\n"
                f"URL: {url}\n"
                f"State: {state} | Updated: {updated}\n"
                f"Labels: {labels}\n"
                f"Body:\n{body}"
            )
            
            comments = issue.get("comments") or []
            if comments:
                parts.append("Comments:")
                for comment in comments:
                    user = comment.get("user", "")
                    comment_body = (comment.get("body") or "").strip()
                    parts.append(f"- @{user}: {comment_body}")
            parts.append("")
        
        return "\n".join(parts).strip()
    
    @staticmethod
    def render_papers_text(rows: list) -> str:
        """Render research papers as text."""
        lines = []
        for row in rows:
            if isinstance(row, str):
                lines.append(row)
                continue
            
            if isinstance(row, dict) and "raw" in row:
                lines.append(str(row["raw"]))
                continue
            
            if isinstance(row, dict):
                # Handle different field names
                kl = {str(k).lower(): v for k, v in row.items()}
                url = kl.get("url", "")
                title = kl.get("title", "")
                date = kl.get("date", "")
                abstract = kl.get("abstract", "")
                category = kl.get("category", "")
                
                if any([url, title, date, abstract, category]):
                    lines.append(f"- {date} | {title} | {url}\n  abstract: {abstract}\n  category: {category}")
                    continue
            
            lines.append(f"- {json.dumps(row, ensure_ascii=False)}")
        
        return "\n".join(lines).strip()
