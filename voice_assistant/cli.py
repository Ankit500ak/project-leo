"""Command-line interface for the Voice Assistant.

This module provides a command-line interface for interacting with the
voice assistant, including starting the assistant in different modes,
managing plugins, and configuring settings.
"""

import argparse
import asyncio
import json
import logging
import os
import signal
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import colorama
from colorama import Fore, Style

from . import __version__
from .core.command_processor import CommandProcessor
from .core.events import event_bus, ErrorEvent
from .core.plugin_manager import PluginManager, load_plugins
from .core.settings import settings, SettingsManager
from .core.voice_engine import VoiceEngine
from .gui.app import VoiceAssistantApp
from .utils import ensure_dir, get_app_data_dir

# Initialize colorama for cross-platform colored output
colorama.init()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(get_app_data_dir() / 'voice_assistant.log')
    ]
)
logger = logging.getLogger(__name__)

class VoiceAssistantCLI:
    """Command-line interface for the Voice Assistant."""
    
    def __init__(self, args: argparse.Namespace):
        """Initialize the CLI.
        
        Args:
            args: Parsed command-line arguments
        """
        self.args = args
        self.running = False
        self.voice_engine = None
        self.command_processor = None
        self.plugin_manager = None
        self.gui_app = None
    
    def run(self) -> int:
        """Run the CLI.
        
        Returns:
            int: Exit code
        """
        try:
            # Handle version flag
            if self.args.version:
                print(f"Voice Assistant v{__version__}")
                return 0
            
            # Handle config command
            if self.args.command == 'config':
                return self.handle_config()
            
            # Handle plugin commands
            if self.args.command == 'plugin':
                return self.handle_plugin_command()
            
            # Handle main application commands
            if self.args.command == 'start':
                return self.start()
            
            # If no command was provided, show help
            self.parser.print_help()
            return 1
            
        except KeyboardInterrupt:
            logger.info("Shutting down...")
            self.shutdown()
            return 0
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
            return 1
    
    def start(self) -> int:
        """Start the voice assistant.
        
        Returns:
            int: Exit code
        """
        # Initialize components
        self.initialize_components()
        
        # Start in the appropriate mode
        if self.args.gui:
            return self.start_gui()
        else:
            return self.start_console()
    
    def initialize_components(self) -> None:
        """Initialize the voice assistant components."""
        logger.info("Initializing components...")
        
        # Initialize settings
        if self.args.config:
            settings.update_from_file(self.args.config)
        
        # Initialize voice engine
        self.voice_engine = VoiceEngine(
            energy_threshold=settings.get('voice.energy_threshold', 300),
            pause_threshold=settings.get('voice.pause_threshold', 0.8),
            dynamic_energy_threshold=settings.get('voice.dynamic_energy_threshold', True),
            wake_words=settings.get('voice.wake_words', ["hey assistant"]),
            activation_method=settings.get('voice.activation_method', 'continuous'),
            push_to_talk_key=settings.get('voice.push_to_talk_key', 'ctrl+space'),
        )
        
        # Initialize command processor
        self.command_processor = CommandProcessor(
            voice_engine=self.voice_engine,
            require_wake_word=settings.get('voice.require_wake_word', True),
        )
        
        # Initialize plugin manager
        self.plugin_manager = PluginManager(
            plugin_dirs=settings.get('plugins.plugin_directories', [])
        )
        
        # Load plugins
        self.plugin_manager.load_plugins()
        
        # Register plugin commands
        self.plugin_manager.register_plugin_commands(self.command_processor)
        
        # Set up signal handlers
        self.setup_signal_handlers()
    
    def start_console(self) -> int:
        """Start the voice assistant in console mode.
        
        Returns:
            int: Exit code
        """
        logger.info("Starting in console mode...")
        print(f"{Fore.GREEN}Voice Assistant v{__version__} - Console Mode{Style.RESET_ALL}")
        print("Type 'exit' or press Ctrl+C to quit\n")
        
        try:
            # Start the voice engine
            self.voice_engine.start()
            self.running = True
            
            # Main loop
            while self.running:
                try:
                    # Get user input
                    try:
                        text = input(">> ").strip()
                    except EOFError:
                        break
                    
                    # Handle exit command
                    if text.lower() in ('exit', 'quit', 'q'):
                        break
                    
                    # Process the command
                    if text:
                        self.command_processor.process_text(text)
                    
                except KeyboardInterrupt:
                    print("\nType 'exit' or press Ctrl+C again to quit")
                except Exception as e:
                    logger.error(f"Error: {e}", exc_info=True)
            
            return 0
            
        except Exception as e:
            logger.error(f"Error in console mode: {e}", exc_info=True)
            return 1
            
        finally:
            self.shutdown()
    
    def start_gui(self) -> int:
        """Start the voice assistant with a GUI.
        
        Returns:
            int: Exit code
        """
        logger.info("Starting GUI...")
        
        try:
            # Import GUI components here to avoid tkinter import in console mode
            self.gui_app = VoiceAssistantApp(
                voice_engine=self.voice_engine,
                command_processor=self.command_processor,
                plugin_manager=self.plugin_manager,
                settings=settings
            )
            
            # Start the voice engine
            self.voice_engine.start()
            self.running = True
            
            # Run the GUI main loop
            self.gui_app.mainloop()
            
            return 0
            
        except Exception as e:
            logger.error(f"Error in GUI: {e}", exc_info=True)
            return 1
            
        finally:
            self.shutdown()
    
    def handle_config(self) -> int:
        """Handle config command.
        
        Returns:
            int: Exit code
        """
        if self.args.action == 'get':
            # Get a config value
            if self.args.key:
                value = settings.get(self.args.key)
                if value is not None:
                    print(json.dumps(value, indent=2))
                    return 0
                else:
                    print(f"No such config key: {self.args.key}", file=sys.stderr)
                    return 1
            else:
                # Show all config
                print(json.dumps(settings.get_all_settings(), indent=2))
                return 0
                
        elif self.args.action == 'set':
            # Set a config value
            if not self.args.key or not self.args.value:
                print("Error: key and value are required for 'set' action", file=sys.stderr)
                return 1
                
            try:
                # Try to parse the value as JSON
                value = json.loads(self.args.value)
            except json.JSONDecodeError:
                # If not valid JSON, treat as string
                value = self.args.value
                
            settings.set(self.args.key, value)
            print(f"Set {self.args.key} = {json.dumps(value)}")
            return 0
            
        elif self.args.action == 'reset':
            # Reset config to defaults
            if self.args.key:
                settings.reset(self.args.key)
                print(f"Reset {self.args.key} to default")
            else:
                settings.reset_all()
                print("Reset all settings to defaults")
            return 0
            
        else:
            print(f"Unknown action: {self.args.action}", file=sys.stderr)
            return 1
    
    def handle_plugin_command(self) -> int:
        """Handle plugin commands.
        
        Returns:
            int: Exit code
        """
        if not self.plugin_manager:
            self.plugin_manager = PluginManager()
        
        if self.args.plugin_action == 'list':
            # List all plugins
            plugins = self.plugin_manager.get_plugins()
            if not plugins:
                print("No plugins found")
                return 0
                
            print(f"\n{Fore.CYAN}Available Plugins:{Style.RESET_ALL}")
            for name, plugin in plugins.items():
                status = f"{Fore.GREEN}enabled{Style.RESET_ALL}" if plugin.enabled else f"{Fore.RED}disabled{Style.RESET_ALL}"
                print(f"- {name} ({status})")
                print(f"  {plugin.description}")
                print(f"  Version: {plugin.version}, Author: {plugin.author}")
                print()
            
            return 0
            
        elif self.args.plugin_action == 'enable':
            # Enable a plugin
            if not self.args.plugin_name:
                print("Error: plugin name is required", file=sys.stderr)
                return 1
                
            if self.plugin_manager.enable_plugin(self.args.plugin_name):
                print(f"Enabled plugin: {self.args.plugin_name}")
                return 0
            else:
                print(f"Failed to enable plugin: {self.args.plugin_name}", file=sys.stderr)
                return 1
                
        elif self.args.plugin_action == 'disable':
            # Disable a plugin
            if not self.args.plugin_name:
                print("Error: plugin name is required", file=sys.stderr)
                return 1
                
            if self.plugin_manager.disable_plugin(self.args.plugin_name):
                print(f"Disabled plugin: {self.args.plugin_name}")
                return 0
            else:
                print(f"Failed to disable plugin: {self.args.plugin_name}", file=sys.stderr)
                return 1
                
        elif self.args.plugin_action == 'info':
            # Show plugin info
            if not self.args.plugin_name:
                print("Error: plugin name is required", file=sys.stderr)
                return 1
                
            plugin = self.plugin_manager.get_plugin(self.args.plugin_name)
            if not plugin:
                print(f"Plugin not found: {self.args.plugin_name}", file=sys.stderr)
                return 1
                
            print(f"\n{Fore.CYAN}Plugin: {plugin.name}{Style.RESET_ALL}")
            print(f"Status: {'Enabled' if plugin.enabled else 'Disabled'}")
            print(f"Version: {plugin.version}")
            print(f"Author: {plugin.author}")
            print(f"Path: {plugin.path}")
            print(f"\n{plugin.description}")
            
            # Show commands provided by this plugin
            if plugin.commands:
                print(f"\n{Fore.CYAN}Commands:{Style.RESET_ALL}")
                for cmd in plugin.commands:
                    cmd_info = getattr(cmd, '_command_info', {})
                    print(f"- {cmd_info.get('name', cmd.__name__)}")
                    if cmd_info.get('description'):
                        print(f"  {cmd_info['description']}")
            
            return 0
            
        else:
            print(f"Unknown plugin action: {self.args.plugin_action}", file=sys.stderr)
            return 1
    
    def setup_signal_handlers(self) -> None:
        """Set up signal handlers for graceful shutdown."""
        def handle_signal(signum, frame):
            logger.info(f"Received signal {signum}, shutting down...")
            self.shutdown()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handle_signal)
        signal.signal(signal.SIGTERM, handle_signal)
    
    def shutdown(self) -> None:
        """Shut down the voice assistant."""
        if not self.running:
            return
            
        logger.info("Shutting down...")
        self.running = False
        
        # Stop the voice engine
        if self.voice_engine:
            self.voice_engine.stop()
        
        # Save settings
        settings.save()
        
        logger.info("Shutdown complete")


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="A voice-controlled assistant with plugin support"
    )
    
    # Global arguments
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='show version and exit'
    )
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest='command', help='command to run')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='start the voice assistant')
    start_parser.add_argument(
        '--gui',
        action='store_true',
        help='start with the graphical user interface'
    )
    start_parser.add_argument(
        '-c', '--config',
        type=str,
        help='path to config file'
    )
    
    # Config command
    config_parser = subparsers.add_parser('config', help='manage configuration')
    config_subparsers = config_parser.add_subparsers(dest='action', help='action to perform')
    
    # Config get
    get_parser = config_subparsers.add_parser('get', help='get a config value')
    get_parser.add_argument('key', nargs='?', help='config key to get')
    
    # Config set
    set_parser = config_subparsers.add_parser('set', help='set a config value')
    set_parser.add_argument('key', help='config key to set')
    set_parser.add_argument('value', help='value to set')
    
    # Config reset
    reset_parser = config_subparsers.add_parser('reset', help='reset config to defaults')
    reset_parser.add_argument('key', nargs='?', help='config key to reset (or all if not specified)')
    
    # Plugin command
    plugin_parser = subparsers.add_parser('plugin', help='manage plugins')
    plugin_subparsers = plugin_parser.add_subparsers(dest='plugin_action', help='action to perform')
    
    # Plugin list
    list_parser = plugin_subparsers.add_parser('list', help='list all plugins')
    
    # Plugin enable
    enable_parser = plugin_subparsers.add_parser('enable', help='enable a plugin')
    enable_parser.add_argument('plugin_name', help='name of the plugin to enable')
    
    # Plugin disable
    disable_parser = plugin_subparsers.add_parser('disable', help='disable a plugin')
    disable_parser.add_argument('plugin_name', help='name of the plugin to disable')
    
    # Plugin info
    info_parser = plugin_subparsers.add_parser('info', help='show plugin information')
    info_parser.add_argument('plugin_name', help='name of the plugin')
    
    # Store the parser for help in the CLI class
    parser._positionals.title = 'Commands'
    parser._optionals.title = 'Global Options'
    VoiceAssistantCLI.parser = parser
    
    return parser.parse_args()


def main() -> int:
    """Main entry point for the CLI.
    
    Returns:
        int: Exit code
    """
    args = parse_args()
    cli = VoiceAssistantCLI(args)
    return cli.run()


if __name__ == '__main__':
    sys.exit(main())
