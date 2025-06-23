"""
Voice Assistant Core Module

This module contains the core functionality of the Voice Assistant,
including voice recognition, command processing, and built-in commands.
"""

# Import key components to make them easily accessible
from voice_assistant.core.voice_engine import voice_engine, VoiceCommand, VoiceEngine
from voice_assistant.core.command_processor import command_processor, CommandProcessor

# Import command modules to ensure they're registered
from voice_assistant.core import builtin_commands
from voice_assistant.core import extended_commands
from voice_assistant.core import entertainment_commands
from voice_assistant.core import utility_commands

# Re-export command decorator for easy access
from voice_assistant.core.builtin_commands import command as command_decorator

# Make command modules available
__all__ = [
    'voice_engine',
    'VoiceCommand',
    'VoiceEngine',
    'command_processor',
    'CommandProcessor',
    'command_decorator',
    'builtin_commands',
    'extended_commands',
    'entertainment_commands',
    'utility_commands'
]
from voice_assistant.core.nlu import nlu_engine, Intent, NLUEngine
from voice_assistant.core.events import event_bus, EventBus, Event, VoiceCommandEvent
from voice_assistant.core.builtin_commands import *
from voice_assistant.core.models import Command

# Version information
__version__ = '0.1.0'
__author__ = 'Ankit'
__license__ = 'MIT'

# Define __all__ to explicitly specify the public API
__all__ = [
    'voice_engine', 'VoiceCommand', 'VoiceEngine',
    'command_processor', 'CommandProcessor', 'Command',
    'nlu_engine', 'Intent', 'NLUEngine',
    'event_bus', 'EventBus', 'Event', 'VoiceCommandEvent'
]
