"""Command processor for handling voice commands with NLU support."""
import os
import re
import json
import logging
import random
from dataclasses import dataclass, field
from typing import Dict, List, Callable, Any, Optional, Tuple, Type, TypeVar
from pathlib import Path
import importlib.util
import inspect
import webbrowser
import datetime

from voice_assistant.core.models import Command
from voice_assistant.core.registry import get_command_processor, register_command_processor, get_voice_engine, get_nlu_engine

# Type variable for generic function type
F = TypeVar('F', bound=Callable[..., Any])

from voice_assistant.config import config
from voice_assistant.core.registry import register_command_processor
from voice_assistant.core.voice_engine import VoiceCommand, voice_engine
from voice_assistant.core.nlu import nlu_engine, Intent

# Import all command modules
from voice_assistant.core.builtin_commands import *
from voice_assistant.core.extended_commands import *
from voice_assistant.core.entertainment_commands import *
from voice_assistant.core.utility_commands import *

# Import command decorators
from voice_assistant.core.builtin_commands import command as builtin_command
from voice_assistant.core.extended_commands import command as extended_command
from voice_assistant.core.entertainment_commands import command as entertainment_command
from voice_assistant.core.utility_commands import command as utility_command

# Import ChatGPT handler
from voice_assistant.core.chatgpt_handler import chatgpt_handler, ChatGPTResponse

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename=config.paths.LOGS_DIR / 'command_processor.log'
)
logger = logging.getLogger(__name__)

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
        """Check if the command matches the given text using both patterns and NLU"""
        if not text or not isinstance(text, str):
            return False
            
        text = text.lower()
        
        # First try pattern matching
        for pattern in self.patterns:
            try:
                if not pattern.startswith('^'):
                    pattern = r'\b' + re.escape(pattern.lower()) + r'\b'
                if re.search(pattern, text, re.IGNORECASE):
                    return True
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                continue
        
        # If no pattern match and we have an intent, try NLU
        if self.intent and nlu_engine is not None:
            try:
                intent = nlu_engine.detect_intent(text)
                if intent and hasattr(intent, 'name') and intent.name == self.intent:
                    confidence = getattr(intent, 'confidence', 0)
                    if confidence > 0.7:  # Confidence threshold
                        return True
            except Exception as e:
                logger.warning(f"Error in NLU matching: {e}")
                # Continue to return False if NLU fails
        
        return False


class CommandProcessor:
    """Processes voice commands using NLU and executes the appropriate actions"""
    
    def __init__(self):
        self.commands: Dict[str, Command] = {}
        self.context = {}
        self.nlu = get_nlu_engine()
        self.command_history = []  # Track command history
        self.max_history = 10  # Maximum number of commands to remember
        # Register this instance with the registry first
        register_command_processor(self)
        # Then register commands
        self._register_commands()
        # Initialize built-in commands
        self._initialize_builtin_commands()
        
    def _initialize_builtin_commands(self):
        """Initialize all built-in commands."""
        from voice_assistant.core.builtin_commands import CommandDecorator
        CommandDecorator.register_all()
        
    def _register_commands(self):
        """Register all available commands from all modules."""
        # Import all command modules to ensure their decorators run
        import importlib
        import inspect
        from voice_assistant.core import builtin_commands, extended_commands, entertainment_commands, utility_commands
        
        # List of modules to import commands from
        command_modules = [
            builtin_commands,
            extended_commands,
            entertainment_commands,
            utility_commands
        ]
        
        # Track registered command names to avoid duplicates
        registered_commands = set()
        
        # Register all commands from each module
        for module in command_modules:
            # Get all functions with the command decorator
            for name, obj in inspect.getmembers(module):
                if hasattr(obj, '_command_info'):
                    # Extract command info from the decorator
                    cmd_info = getattr(obj, '_command_info')
                    cmd_name = cmd_info.get('name', name)
                    
                    # Skip if already registered
                    if cmd_name in registered_commands:
                        logger.debug(f"Skipping duplicate command: {cmd_name}")
                        continue
                        
                    # Register the command
                    self.register_command(
                        name=cmd_name,
                        description=cmd_info.get('description', ''),
                        func=obj,
                        patterns=cmd_info.get('patterns', []),
                        requires_wake_word=cmd_info.get('requires_wake_word', True),
                        admin_only=cmd_info.get('admin_only', False)
                    )
                    
                    registered_commands.add(cmd_name)
                    logger.info(f"Registered command: {cmd_name}")
                    
        
        # System commands
        self.register_command(
            name="email",
            description="Send emails",
            intent="email",
            func=handle_email
        )
        
        self.register_command(
            name="alarm",
            description="Set alarms",
            intent="alarm",
            func=handle_alarm
        )
        
        # Information commands
        self.register_command(
            name="weather",
            description="Get weather information",
            intent="weather",
            func=handle_weather
        )
        
        self.register_command(
            name="news",
            description="Get latest news",
            intent="news",
            func=handle_news
        )
        
        # Communication commands
        self.register_command(
            name="whatsapp",
            description="Send WhatsApp messages",
            intent="whatsapp",
            func=handle_whatsapp
        )
        
        self.register_command(
            name="video_call",
            description="Make video calls",
            intent="video_call",
            func=handle_video_call
        )
        
        # Location services
        self.register_command(
            name="location",
            description="Get location information",
            intent="location",
            func=handle_location
        )
        
        # System information
        self.register_command(
            name="speedtest",
            description="Run internet speed test",
            intent="speedtest",
            func=handle_speedtest
        )
        
        # Calculator
        self.register_command(
            name="calculate",
            description="Perform calculations",
            intent="calculate",
            func=handle_calculation
        )
        
        # Temperature conversion
        self.register_command(
            name="temperature",
            description="Convert temperatures",
            intent="temperature",
            func=handle_temperature
        )
        self.load_plugins()
        
        # Register command processor with voice engine
        voice_engine.register_callback(self.process_voice_command)
    
    def register_command(self, name: str, description: str, patterns: List[str] = None, 
                       func: Callable = None, requires_wake_word: bool = True, 
                       admin_only: bool = False, intent: str = None) -> Callable:
        """Register a new command with the processor.
        
        Can be used as a decorator or a regular method.
        
        Args:
            name: Unique name for the command
            description: Short description of what the command does
            patterns: List of regex patterns to match this command
            func: Function to call when command is executed
            requires_wake_word: Whether the wake word is required
            admin_only: Whether only admin users can run this command
            intent: The intent name this command handles (optional)
            
        Returns:
            The decorated function or the command instance if used as a decorator
        """
        def decorator(f: Callable) -> Callable:
            """Decorator to register a command"""
            command = Command(
                name=name,
                description=description,
                patterns=patterns or [],
                func=f,
                requires_wake_word=requires_wake_word,
                admin_only=admin_only,
                intent=intent
            )
            self.commands[name.lower()] = command
            return f
            
        # If used as a decorator without arguments
        if func is not None and callable(func):
            return decorator(func)
            
        return decorator
    
    def load_builtin_commands(self):
        """Load built-in commands"""
        import voice_assistant.core.builtin_commands  # This will be created next
        
    def load_plugins(self):
        """Load commands from plugin modules"""
        plugins_dir = Path(__file__).parent.parent / 'plugins'
        if not plugins_dir.exists():
            plugins_dir.mkdir(parents=True, exist_ok=True)
            return
            
        for plugin_file in plugins_dir.glob('*.py'):
            if plugin_file.name.startswith('_'):
                continue
                
            plugin_name = plugin_file.stem
            spec = importlib.util.spec_from_file_location(
                f'plugins.{plugin_name}', 
                plugin_file
            )
            if spec and spec.loader:
                try:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    logger.info(f"Loaded plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Error loading plugin {plugin_name}: {e}")
    
    def process_command(self, text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Process a text command and return the response.
        
        Args:
            text: The text command to process
            context: Optional context dictionary
                
        Returns:
            Response dictionary with 'text' and 'success' keys
        """
        if not text or not isinstance(text, str):
            return {'text': "I didn't catch that. Could you please repeat?", 'success': False}
            
        if context is None:
            context = {}
            
        # Clean and normalize the input text
        text = text.lower().strip()
        logger.info(f"Processing command: {text}")
        
        # Add to command history
        self.command_history.append(text)
        if len(self.command_history) > self.max_history:
            self.command_history.pop(0)
        
        # Check for wake word if required
        wake_word_detected = context.get('wake_word_detected', False)
        if not wake_word_detected:
            wake_word_detected = any(
                re.search(rf'\b{re.escape(wake_word)}\b', text, re.IGNORECASE)
                for wake_word in config.voice.WAKE_WORDS
            )
            if not wake_word_detected:
                logger.debug("No wake word detected in command")
                return {'success': False}
        
        # Try multiple approaches to handle the command
        
        # 1. Try exact command matching first
        for command in self.commands.values():
            if text == command.name.lower():
                return self._execute_command(command, text, context)
        
        # 2. Try pattern matching
        best_match = None
        best_confidence = 0.0
        
        for command in self.commands.values():
            # Try pattern matching
            pattern_match = False
            for pattern in command.patterns:
                try:
                    if not pattern.startswith('^'):
                        pattern = r'\b' + re.escape(pattern.lower()) + r'\b'
                    if re.search(pattern, text, re.IGNORECASE):
                        pattern_match = True
                        confidence = 0.8  # High confidence for pattern match
                        break
                except re.error as e:
                    logger.warning(f"Invalid regex pattern '{pattern}': {e}")
                    continue
            
            # If no pattern match and we have an intent, try NLU
            if not pattern_match and command.intent and self.nlu is not None:
                try:
                    intent = self.nlu.detect_intent(text)
                    if intent and intent.name == command.intent:
                        confidence = intent.confidence
                        pattern_match = True
                except Exception as e:
                    logger.warning(f"Error in NLU matching: {e}")
                    continue
            
            # Update best match if this command has higher confidence
            if pattern_match and confidence > best_confidence:
                best_match = command
                best_confidence = confidence
        
        # 3. If we found a good match, execute it
        if best_match and best_confidence > 0.6:
            return self._execute_command(best_match, text, context)
        
        # 4. Try to find similar commands from history
        similar_commands = self._find_similar_commands(text)
        if similar_commands:
            # If we found similar commands, ask for confirmation
            suggestions = ", ".join(f"'{cmd}'" for cmd in similar_commands[:3])
            return {
                'text': f"I'm not sure if I understood correctly. Did you mean one of these: {suggestions}?",
                'success': False,
                'requires_confirmation': True,
                'suggestions': similar_commands
            }
        
        # 5. If no match found, try ChatGPT
        chatgpt_response = chatgpt_handler.process_command(text, context)
        if chatgpt_response.success:
            # If ChatGPT suggests a command, try to execute it
            if chatgpt_response.action:
                suggested_command = chatgpt_response.action.lower()
                for command in self.commands.values():
                    if suggested_command in command.name.lower():
                        return self._execute_command(command, text, context)
            
            # Otherwise, return ChatGPT's response
            return {
                'text': chatgpt_response.text,
                'success': True,
                'action': chatgpt_response.action,
                'metadata': chatgpt_response.metadata
            }
        
        # 6. If all else fails, get a suggestion from ChatGPT
        suggestion = chatgpt_handler.get_command_suggestion(text)
        return {
            'text': suggestion.text,
            'success': False,
            'suggestion': suggestion.metadata.get('suggested_command'),
            'requires_input': True
        }
    
    def _execute_command(self, command: Command, text: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a command and handle its response"""
        try:
            # Extract command parameters
            params = self._extract_command_params(text, command)
            
            # Execute the command
            result = command.func(text, context, **params)
            
            if isinstance(result, dict):
                if result.get('success', True):
                    logger.info(f"Command {command.name} executed successfully")
                else:
                    logger.warning(f"Command {command.name} failed: {result.get('message', 'Unknown error')}")
                return result
                
            return {'text': str(result), 'success': True}
            
        except Exception as e:
            logger.error(f"Error executing command {command.name}: {e}", exc_info=True)
            return {
                'text': "I had trouble with that request. Could you try again?",
                'success': False,
                'error': str(e)
            }
    
    def _find_similar_commands(self, text: str) -> List[str]:
        """Find similar commands from history using fuzzy matching"""
        from difflib import get_close_matches
        
        # Get all command names and patterns
        command_texts = []
        for cmd in self.commands.values():
            command_texts.append(cmd.name)
            command_texts.extend(cmd.patterns)
        
        # Add recent command history
        command_texts.extend(self.command_history)
        
        # Find similar matches
        matches = get_close_matches(text, command_texts, n=3, cutoff=0.6)
        return matches
    
    def _extract_command_params(self, text: str, command: Command) -> Dict[str, Any]:
        """Extract command parameters from the input text"""
        params = {}
        
        # Common parameter extraction patterns
        param_patterns = {
            'open': r'(?:open|launch|start|run|go to|navigate to)\s+(?:the\s+)?(?:app\s+|application\s+|program\s+|website\s+|site\s+|browser\s+)?(.+)$',
            'play': r'(?:play|start playing)\s+(?:the\s+)?(?:song\s+|music\s+|video\s+|audio\s+)?(.+)$',
            'search': r'(?:search|look up|find|google)\s+(?:for\s+|about\s+)?(.+)$',
            'whatsapp': r'(?:send|whatsapp|message)\s+(?:a\s+)?(?:whatsapp\s+|message\s+)?(?:to\s+)?(.+?)(?:\s+saying\s+|\s+with\s+|\s+that\s+)?(.+)?$',
            'email': r'(?:send|write|compose)\s+(?:an\s+)?(?:email|message)\s+(?:to\s+)?(.+?)(?:\s+about\s+|\s+saying\s+|\s+with\s+|\s+that\s+)?(.+)?$',
            'weather': r'(?:weather|forecast)\s+(?:for\s+|in\s+)?(.+)$',
            'time': r'(?:time|what time)\s+(?:in\s+)?(.+)?$',
            'date': r'(?:date|what day|what\'s today)\s+(?:is\s+)?(.+)?$',
            'calculate': r'(?:calculate|compute|what is|what\'s)\s+(.+)$',
            'convert': r'(?:convert|change|transform)\s+(.+?)\s+(?:to|into)\s+(.+)$'
        }
        
        # Try to extract parameters based on command type
        if command.name in param_patterns:
            pattern = param_patterns[command.name]
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if command.name in ['whatsapp', 'email']:
                    params['contact'] = match.group(1).strip()
                    if len(match.groups()) > 1 and match.group(2):
                        params['message'] = match.group(2).strip()
                elif command.name == 'convert':
                    params['value'] = match.group(1).strip()
                    params['target_unit'] = match.group(2).strip()
                else:
                    params['target'] = match.group(1).strip()
        
        # Add context from previous commands if available
        if self.command_history:
            last_command = self.command_history[-1]
            if 'awaiting' in context:
                # If we were waiting for input, use the current command as the input
                param_name = context['awaiting'].replace('awaiting_', '')
                params[param_name] = text
        
        return params
    
    def process_voice_command(self, command):
        """Process a voice command from the voice engine"""
        if not command or not command.text:
            return
            
        # Create context with wake word detection
        context = {
            'wake_word_detected': getattr(command, 'is_wake_word', False),
            'confidence': getattr(command, 'confidence', 1.0),
            'intent': command.intent.name if hasattr(command, 'intent') and command.intent else None,
            'raw_intent': getattr(command, 'intent', None)
        }
        
        # Process the command
        response = self.process_command(command.text, context)
        
        # Speak the response if available
        if response and response.get('text'):
            voice_engine = get_voice_engine()
            if voice_engine:
                voice_engine.speak(response['text'])
        
        return response
        
    def set_context(self, key: str, value: Any):
        """Set a context value"""
        self.context[key] = value
    
    def get_context(self, key: str, default=None) -> Any:
        """Get a context value"""
        return self.context.get(key, default)
    
    def list_commands(self) -> List[Dict[str, Any]]:
        """List all available commands"""
        return [
            {
                'name': cmd.name,
                'description': cmd.description,
                'patterns': cmd.patterns,
                'requires_wake_word': cmd.requires_wake_word,
                'admin_only': cmd.admin_only
            }
            for cmd in self.commands.values()
        ]


# Create a singleton instance when this module is imported
command_processor = CommandProcessor()

# Example usage
if __name__ == "__main__":
    # Example of registering a command
    @command_processor.register_command(
        name="greet",
        description="Responds with a greeting",
        patterns=["hello", "hi", "hey"],
        requires_wake_word=False
    )
    def greet():
        voice_engine.speak("Hello! How can I help you today?")
    
    # Start listening
    voice_engine.start_continuous_listening()
    print("Listening for commands...")
    
    try:
        while True:
            # Process commands in the main thread
            commands = voice_engine.process_command_queue()
            for cmd in commands:
                command_processor.process_voice_command(cmd)
            time.sleep(0.1)
    except KeyboardInterrupt:
        voice_engine.stop_continuous_listening()
        print("\nStopped listening")
