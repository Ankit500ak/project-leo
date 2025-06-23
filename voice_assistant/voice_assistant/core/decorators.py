"""Decorators for the Voice Assistant.

This module provides decorators for registering commands, event handlers,
and other functionality with the voice assistant.
"""

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, TypeVar, cast

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

def command(
    name: Optional[str] = None,
    description: str = "",
    patterns: Optional[List[str]] = None,
    requires_wake_word: bool = True,
    admin_only: bool = False,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator to register a function as a voice command.
    
    Args:
        name: Command name (defaults to function name)
        description: Short description of the command
        patterns: List of patterns that trigger this command
        requires_wake_word: Whether the wake word is required
        admin_only: Whether only admin users can use this command
        enabled: Whether the command is enabled by default
        
    Returns:
        The decorated function with command metadata
    """
    def decorator(func: F) -> F:
        # Use function name if name not provided
        cmd_name = name or func.__name__
        
        # Store command metadata
        cmd_info = {
            'name': cmd_name,
            'description': description or (func.__doc__ or "").split('\n')[0],
            'patterns': patterns or [],
            'requires_wake_word': requires_wake_word,
            'admin_only': admin_only,
            'enabled': enabled,
            'function': func,
            'module': func.__module__,
        }
        
        # Attach command info to the function
        func._command_info = cmd_info  # type: ignore
        
        # Preserve the original function's metadata
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
            
        # Copy the command info to the wrapper
        wrapper._command_info = cmd_info  # type: ignore
        
        return cast(F, wrapper)
    return decorator

def event(event_name: Optional[str] = None, priority: int = 0) -> Callable[[F], F]:
    """Decorator to register a function as an event handler.
    
    Args:
        event_name: Name of the event to handle (defaults to function name)
        priority: Handler priority (higher numbers are called first)
        
    Returns:
        The decorated function with event handler metadata
    """
    def decorator(func: F) -> F:
        # Use function name if event_name not provided
        evt_name = event_name or func.__name__
        
        # Store event handler metadata
        handler_info = {
            'name': evt_name,
            'priority': priority,
            'function': func,
            'module': func.__module__,
        }
        
        # Attach handler info to the function
        func._event_handler_info = handler_info  # type: ignore
        
        # Preserve the original function's metadata
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
            
        # Copy the handler info to the wrapper
        wrapper._event_handler_info = handler_info  # type: ignore
        
        return cast(F, wrapper)
    return decorator

def background_task(
    name: Optional[str] = None, 
    daemon: bool = True,
    autostart: bool = True
) -> Callable[[F], F]:
    """Decorator to register a function as a background task.
    
    Args:
        name: Task name (defaults to function name)
        daemon: Whether the task should run as a daemon thread
        autostart: Whether to start the task automatically
        
    Returns:
        The decorated function with task metadata
    """
    def decorator(func: F) -> F:
        # Use function name if name not provided
        task_name = name or func.__name__
        
        # Store task metadata
        task_info = {
            'name': task_name,
            'daemon': daemon,
            'autostart': autostart,
            'function': func,
            'module': func.__module__,
        }
        
        # Attach task info to the function
        func._task_info = task_info  # type: ignore
        
        # Preserve the original function's metadata
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return func(*args, **kwargs)
            
        # Copy the task info to the wrapper
        wrapper._task_info = task_info  # type: ignore
        
        return cast(F, wrapper)
    return decorator

def plugin_command(
    name: Optional[str] = None,
    description: str = "",
    patterns: Optional[List[str]] = None,
    requires_wake_word: bool = True,
    admin_only: bool = False,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator to register a plugin command.
    
    This is an alias for the command decorator for better semantics in plugins.
    """
    return command(
        name=name,
        description=description,
        patterns=patterns,
        requires_wake_word=requires_wake_word,
        admin_only=admin_only,
        enabled=enabled,
    )

def admin_command(
    name: Optional[str] = None,
    description: str = "",
    patterns: Optional[List[str]] = None,
    requires_wake_word: bool = True,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator to register an admin-only command.
    
    This is a convenience wrapper around the command decorator with admin_only=True.
    """
    return command(
        name=name,
        description=description,
        patterns=patterns,
        requires_wake_word=requires_wake_word,
        admin_only=True,
        enabled=enabled,
    )

def async_command(
    name: Optional[str] = None,
    description: str = "",
    patterns: Optional[List[str]] = None,
    requires_wake_word: bool = True,
    admin_only: bool = False,
    enabled: bool = True,
) -> Callable[[F], F]:
    """Decorator to register an async command.
    
    This is a convenience wrapper around the command decorator for async functions.
    """
    def decorator(func: F) -> F:
        # Apply the standard command decorator
        cmd_func = command(
            name=name,
            description=description,
            patterns=patterns,
            requires_wake_word=requires_wake_word,
            admin_only=admin_only,
            enabled=enabled,
        )(func)
        
        # Mark the function as async
        cmd_func._is_async = True  # type: ignore
        
        return cmd_func
    return decorator

# Export the most commonly used decorators
__all__ = [
    'command',
    'event',
    'background_task',
    'plugin_command',
    'admin_command',
    'async_command',
]
