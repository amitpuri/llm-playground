"""
Prompt optimizer using LangChain for context-aware prompt enhancement.
"""
import math
from typing import Dict, Any, List, Optional
from .models import GitHubIssue, ResearchPaper, OptimizerConfig


class TextRenderer:
    """Utility class for rendering MCP data as text."""
    
    @staticmethod
    def render_issues_text(issues: List[Dict[str, Any]]) -> str:
        """Render GitHub issues as text."""
        if not issues:
            return ""
        
        text_parts = ["## Recent GitHub Issues\n"]
        
        for issue in issues:
            text_parts.append(f"### Issue #{issue['number']}: {issue['title']}")
            text_parts.append(f"**State:** {issue['state']}")
            text_parts.append(f"**Created:** {issue['created_at']}")
            text_parts.append(f"**Updated:** {issue['updated_at']}")
            
            if issue['body']:
                # Truncate body if too long
                body = issue['body'][:500] + "..." if len(issue['body']) > 500 else issue['body']
                text_parts.append(f"**Description:** {body}")
            
            if issue['comments']:
                text_parts.append("**Recent Comments:**")
                for comment in issue['comments'][:3]:  # Limit to 3 comments
                    comment_text = comment['body'][:200] + "..." if len(comment['body']) > 200 else comment['body']
                    text_parts.append(f"- **{comment['user']}:** {comment_text}")
            
            text_parts.append("")  # Empty line between issues
        
        return "\n".join(text_parts)
    
    @staticmethod
    def render_papers_text(papers: List[Dict[str, Any]]) -> str:
        """Render research papers as text."""
        if not papers:
            return ""
        
        text_parts = ["## Recent Research Papers\n"]
        
        for paper in papers:
            text_parts.append(f"### {paper['title']}")
            text_parts.append(f"**Authors:** {paper['authors']}")
            
            if paper.get('year'):
                text_parts.append(f"**Year:** {paper['year']}")
            
            if paper.get('doi'):
                text_parts.append(f"**DOI:** {paper['doi']}")
            
            if paper['abstract']:
                # Truncate abstract if too long
                abstract = paper['abstract'][:300] + "..." if len(paper['abstract']) > 300 else paper['abstract']
                text_parts.append(f"**Abstract:** {abstract}")
            
            text_parts.append("")  # Empty line between papers
        
        return "\n".join(text_parts)


class PromptOptimizer:
    """Optimizes prompts using MCP context."""
    
    def __init__(self, config: OptimizerConfig):
        self.config = config
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count for text."""
        return max(1, math.ceil(len(text) / 4))
    
    def _trim_to_tokens(self, text: str, max_tokens: int) -> str:
        """Trim text to fit within token limit."""
        if self._estimate_tokens(text) <= max_tokens:
            return text
        return text[:max(0, max_tokens * 4)]
    
    def optimize_prompt(self, user_prompt: str, github_issues: List[Dict[str, Any]] = None, 
                       research_papers: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Optimize a user prompt with MCP context."""
        if not self.config.enabled:
            return {
                "optimized_prompt": user_prompt,
                "debug": {"optimizer_enabled": False}
            }
        
        context_parts = []
        debug_info = {
            "optimizer_enabled": True,
            "github_issues_count": 0,
            "research_papers_count": 0,
            "context_tokens": 0
        }
        
        # Add GitHub issues context
        if self.config.include_github_issues and github_issues:
            issues_text = TextRenderer.render_issues_text(github_issues[:self.config.max_issues])
            if issues_text:
                context_parts.append(issues_text)
                debug_info["github_issues_count"] = len(github_issues[:self.config.max_issues])
        
        # Add research papers context
        if self.config.include_research_papers and research_papers:
            papers_text = TextRenderer.render_papers_text(research_papers[:self.config.max_papers])
            if papers_text:
                context_parts.append(papers_text)
                debug_info["research_papers_count"] = len(research_papers[:self.config.max_papers])
        
        # Combine context
        if context_parts:
            context = "\n\n".join(context_parts)
            context_tokens = self._estimate_tokens(context)
            debug_info["context_tokens"] = context_tokens
            
            # Check if context fits within limits
            if context_tokens > self.config.max_context_tokens:
                context = self._trim_to_tokens(context, self.config.max_context_tokens)
                debug_info["context_trimmed"] = True
            
            # Create optimized prompt
            optimized_prompt = f"""You have access to the following context information:

{context}

Based on this context and your knowledge, please respond to the following user query:

{user_prompt}

Please provide a comprehensive and well-informed response that takes into account the context provided above."""
        else:
            optimized_prompt = user_prompt
            debug_info["no_context_available"] = True
            debug_info["user_prompt_length"] = len(user_prompt) if user_prompt else 0
        
        return {
            "optimized_prompt": optimized_prompt,
            "debug": debug_info
        }
