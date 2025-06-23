"""Data models for the voice assistant."""
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional


@dataclass
class Command:
    """Represents a command that can be executed"""
    name: str
    description: str
    patterns: List[str] = field(default_factory=list)
    func: Callable = None
    intent: str = None
    requires_wake_word: bool = True
    admin_only: bool = False
    
    def matches(self, text: str) -> bool:
        """Check if the command matches the given text"""
        if not text:
            return False
            
        # Check if any pattern matches
        for pattern in self.patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
                
        return False
