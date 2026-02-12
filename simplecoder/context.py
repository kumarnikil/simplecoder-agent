"""
Context management for keeping conversations within token limits.

Simple approach: Track tokens, keep recent messages, discard old ones when limit reached.
"""

from typing import List, Dict, Any
from rich.console import Console

console = Console()


class ContextManager:
    """
    Simple context manager that keeps conversations within token limits.
    """
    
    def __init__(self, max_tokens: int = 100000, keep_last_n: int = 10, verbose: bool = False):
        """
        Args:
            max_tokens: Maximum tokens allowed (default: 100k)
            keep_last_n: Number of recent messages to keep (default: 10)
            verbose: Print detailed logging
        """
        self.max_tokens = max_tokens
        self.keep_last_n = keep_last_n
        self.verbose = verbose
        
        if self.verbose:
            console.print(f"[dim]Context manager initialized: max={max_tokens:,} tokens, keep_last={keep_last_n}[/dim]")
    
    def estimate_tokens(self, messages: List[Dict[str, Any]]) -> int:
        """
        Rough token estimate: ~4 chars = 1 token
        """
        total_chars = sum(len(str(msg.get("content", ""))) for msg in messages)
        tokens = total_chars // 4
        
        if self.verbose:
            console.print(f"[dim]Token estimate: ~{tokens:,} tokens from {len(messages)} messages[/dim]")
        
        return tokens
    
    def should_compact(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Return True if over 80% of max tokens
        """
        tokens = self.estimate_tokens(messages)
        threshold = int(self.max_tokens * 0.8)
        
        if tokens > threshold:
            if self.verbose:
                console.print(f"[yellow]⚠️  Context over threshold: {tokens:,}/{self.max_tokens:,} tokens ({int(tokens/self.max_tokens*100)}%)[/yellow]")
            return True
        
        if self.verbose:
            console.print(f"[dim]Context OK: {tokens:,}/{self.max_tokens:,} tokens ({int(tokens/self.max_tokens*100)}%)[/dim]")
        
        return False
    
    def compact_messages(self, messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if len(messages) <= self.keep_last_n + 1:
            if self.verbose:
                console.print(f"[dim]No compaction needed (only {len(messages)} messages)[/dim]")
            return messages
        
        # Separate system message and find first user message
        system_msg = messages[0] if messages[0].get("role") == "system" else None
        
        # Find first user message (Gemini requires user after system)
        first_user_msg = None
        for msg in messages[1:]:
            if msg.get("role") == "user":
                first_user_msg = msg
                break
        
        # Keep last N messages
        recent = messages[-self.keep_last_n:]
        
        # Build compacted list: system + first_user + recent
        compacted = []
        if system_msg:
            compacted.append(system_msg)
        if first_user_msg and first_user_msg not in recent:
            compacted.append(first_user_msg)  # Ensure user after system
        compacted.extend(recent)
        
        if self.verbose:
            console.print(f"[green]✓ Compacted: {len(messages)} → {len(compacted)} messages[/green]")
        
        return compacted