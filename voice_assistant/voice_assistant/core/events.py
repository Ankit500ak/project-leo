"""Event system for the Voice Assistant.

This module provides an event system that allows different components
of the application to communicate with each other in a decoupled way.
"""

import asyncio
import inspect
import logging
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import (
    Any, Callable, Coroutine, Dict, List, Optional, Set, Type, TypeVar, Union, cast
)

from voice_assistant.core.decorators import event

logger = logging.getLogger(__name__)

# Type variables
T = TypeVar('T')
EventHandler = Callable[..., Optional[Union[None, Coroutine[Any, Any, None]]]]

class EventPriority(Enum):
    """Priority levels for event handlers."""
    LOWEST = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    HIGHEST = 4
    MONITOR = 5  # For monitoring only, should not modify the event

@dataclass
class Event:
    """Base class for all events.
    
    Events can be created by subclassing this class and adding any
    necessary attributes. Events can be fired using the EventBus.
    """
    # Whether the event has been cancelled
    cancelled: bool = field(default=False, init=False)
    
    # Whether the event should be processed asynchronously
    async_event: bool = field(default=False, init=False)
    
    def cancel(self) -> None:
        """Cancel the event."""
        self.cancelled = True

@dataclass
class CommandEvent(Event):
    """Event fired when a command is executed."""
    command: str
    args: Dict[str, Any]
    result: Any = None
    success: bool = True
    error: Optional[Exception] = None

@dataclass
class VoiceCommandEvent(Event):
    """Event fired when a voice command is recognized."""
    text: str
    confidence: float
    is_wake_word: bool = False
    processed: bool = False

@dataclass
class SpeechRecognizedEvent(Event):
    """Event fired when speech is recognized."""
    text: str
    confidence: float
    is_final: bool = True

@dataclass
class SpeechSynthesisEvent(Event):
    """Event fired when text is about to be spoken."""
    text: str
    voice_id: Optional[str] = None
    rate: Optional[int] = None
    volume: Optional[float] = None

@dataclass
class PluginLoadedEvent(Event):
    """Event fired when a plugin is loaded."""
    plugin_name: str
    plugin_path: str
    success: bool
    error: Optional[Exception] = None

@dataclass
class ErrorEvent(Event):
    """Event fired when an error occurs."""
    error: Exception
    context: Optional[Dict[str, Any]] = None
    handled: bool = False

class EventBus:
    """Event bus for publishing and subscribing to events.
    
    This class provides a simple publish-subscribe system for events.
    Components can subscribe to event types and be notified when events
    of those types are published.
    """
    
    def __init__(self):
        """Initialize the event bus."""
        self._handlers: Dict[Type[Event], Dict[EventHandler, EventPriority]] = defaultdict(dict)
        self._async_handlers: Dict[Type[Event], Dict[EventHandler, EventPriority]] = defaultdict(dict)
        self._event_loop = asyncio.get_event_loop()
    
    def subscribe(
        self, 
        event_type: Type[T], 
        handler: EventHandler,
        priority: EventPriority = EventPriority.NORMAL,
        is_async: bool = False
    ) -> None:
        """Subscribe to an event type.
        
        Args:
            event_type: The type of event to subscribe to
            handler: The handler function to call when the event is published
            priority: The priority of the handler (higher numbers are called first)
            is_async: Whether the handler is an async function
        """
        if not issubclass(event_type, Event):
            raise TypeError(f"{event_type} is not a subclass of Event")
        
        if is_async or inspect.iscoroutinefunction(handler):
            self._async_handlers[event_type][handler] = priority
        else:
            self._handlers[event_type][handler] = priority
    
    def unsubscribe(self, event_type: Type[Event], handler: EventHandler) -> None:
        """Unsubscribe a handler from an event type.
        
        Args:
            event_type: The type of event to unsubscribe from
            handler: The handler function to remove
        """
        if handler in self._handlers[event_type]:
            del self._handlers[event_type][handler]
        if handler in self._async_handlers[event_type]:
            del self._async_handlers[event_type][handler]
    
    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.
        
        Args:
            event: The event to publish
            
        Returns:
            The event, possibly modified by handlers
        """
        if not isinstance(event, Event):
            raise TypeError(f"Expected Event, got {type(event).__name__}")
        
        # Get all handlers for this event type and its superclasses
        event_type = type(event)
        event_types = [t for t in self._handlers.keys() if issubclass(event_type, t)]
        
        # Sort handlers by priority (highest first)
        handlers = []
        for t in event_types:
            for handler, priority in self._handlers[t].items():
                handlers.append((handler, priority))
        
        handlers.sort(key=lambda x: x[1].value, reverse=True)
        
        # Call synchronous handlers
        for handler, _ in handlers:
            if event.cancelled:
                break
                
            try:
                result = handler(event)
                if result is not None:
                    logger.warning(
                        f"Synchronous event handler {handler.__name__} "
                        "returned a value which will be ignored"
                    )
            except Exception as e:
                logger.error(f"Error in event handler {handler.__name__}: {e}", exc_info=True)
        
        # Schedule async handlers
        if not event.cancelled:
            self._schedule_async_handlers(event)
        
        return event
    
    def _schedule_async_handlers(self, event: Event) -> None:
        """Schedule async handlers to be called.
        
        Args:
            event: The event to handle
        """
        event_type = type(event)
        event_types = [t for t in self._async_handlers.keys() if issubclass(event_type, t)]
        
        # Sort handlers by priority (highest first)
        handlers = []
        for t in event_types:
            for handler, priority in self._async_handlers[t].items():
                handlers.append((handler, priority))
        
        handlers.sort(key=lambda x: x[1].value, reverse=True)
        
        # Create a task to run all async handlers
        async def run_handlers():
            for handler, _ in handlers:
                if event.cancelled:
                    break
                    
                try:
                    result = handler(event)
                    if inspect.iscoroutine(result):
                        await result
                except Exception as e:
                    logger.error(f"Error in async event handler {handler.__name__}: {e}", exc_info=True)
        
        # Schedule the task
        asyncio.create_task(run_handlers())
    
    def register_handler(
        self, 
        event_type: Type[T], 
        priority: EventPriority = EventPriority.NORMAL,
        is_async: bool = False
    ) -> Callable[[EventHandler], EventHandler]:
        """Decorator to register an event handler.
        
        Args:
            event_type: The type of event to handle
            priority: The priority of the handler
            is_async: Whether the handler is an async function
            
        Returns:
            A decorator that registers the function as an event handler
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_type, handler, priority, is_async)
            return handler
        return decorator

# Singleton instance
event_bus = EventBus()

# Convenience functions
def subscribe(
    event_type: Type[T], 
    priority: EventPriority = EventPriority.NORMAL,
    is_async: bool = False
) -> Callable[[EventHandler], EventHandler]:
    """Decorator to subscribe to an event type.
    
    Args:
        event_type: The type of event to subscribe to
        priority: The priority of the handler
        is_async: Whether the handler is an async function
        
    Returns:
        A decorator that registers the function as an event handler
    """
    return event_bus.register_handler(event_type, priority, is_async)

def publish(event: Event) -> Event:
    """Publish an event to all subscribers.
    
    Args:
        event: The event to publish
        
    Returns:
        The event, possibly modified by handlers
    """
    return event_bus.publish(event)

# Example event handlers for common events
@subscribe(ErrorEvent, priority=EventPriority.HIGH)
def log_errors(event: ErrorEvent) -> None:
    """Log all erro1rs to the console."""
    if not event.handled:
        logger.error(f"Unhandled error: {event.error}", exc_info=event.error)
        event.handled = True

@subscribe(PluginLoadedEvent)
def log_plugin_loaded(event: PluginLoadedEvent) -> None:
    """Log when plugins are loaded."""
    if event.success:
        logger.info(f"Plugin loaded: {event.plugin_name}")
    else:
        logger.error(
            f"Failed to load plugin {event.plugin_name}: {event.error}",
            exc_info=event.error
        )

# Export commonly used events and types
__all__ = [
    'Event',
    'CommandEvent',
    'VoiceCommandEvent',
    'SpeechRecognizedEvent',
    'SpeechSynthesisEvent',
    'PluginLoadedEvent',
    'ErrorEvent',
    'EventPriority',
    'EventBus',
    'event_bus',
    'subscribe',
    'publish',
]
