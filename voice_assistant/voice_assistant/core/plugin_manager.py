"""Plugin management system for the Voice Assistant.

This module handles the discovery, loading, and management of plugins
that extend the functionality of the Voice Assistant.
"""

import importlib
import importlib.util
import inspect
import logging
import pkgutil
import sys
from pathlib import Path
from typing import Dict, List, Optional, Type, Any, Set, Callable

from voice_assistant.utils import ensure_dir
from voice_assistant.core.settings import settings

logger = logging.getLogger(__name__)

class Plugin:
    """Represents a loaded plugin."""
    
    def __init__(
        self,
        name: str,
        path: Path,
        module: Any,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Initialize a plugin.
        
        Args:
            name: Plugin name (should be unique)
            path: Path to the plugin file or directory
            module: The loaded module object
            enabled: Whether the plugin is enabled
            metadata: Additional metadata about the plugin
        """
        self.name = name
        self.path = path
        self.module = module
        self.enabled = enabled
        self.metadata = metadata or {}
        self._commands: List[Callable] = []
    
    def __repr__(self) -> str:
        return f"<Plugin {self.name} {'(enabled)' if self.enabled else '(disabled)'}>"
    
    @property
    def description(self) -> str:
        """Get the plugin description from its docstring or metadata."""
        if 'description' in self.metadata:
            return self.metadata['description']
        return inspect.getdoc(self.module) or "No description available"
    
    @property
    def version(self) -> str:
        """Get the plugin version from its metadata or module."""
        if 'version' in self.metadata:
            return self.metadata['version']
        return getattr(self.module, '__version__', '0.1.0')
    
    @property
    def author(self) -> str:
        """Get the plugin author from its metadata or module."""
        if 'author' in self.metadata:
            return self.metadata['author']
        return getattr(self.module, '__author__', 'Unknown')
    
    @property
    def commands(self) -> List[Callable]:
        """Get a list of command functions registered by this plugin."""
        return self._commands
    
    def register_command(self, command_func: Callable) -> None:
        """Register a command function with this plugin."""
        self._commands.append(command_func)
    
    def enable(self) -> None:
        """Enable the plugin."""
        self.enabled = True
        # Initialize the plugin if it has an initialize function
        if hasattr(self.module, 'initialize'):
            try:
                self.module.initialize()
                logger.info(f"Initialized plugin: {self.name}")
            except Exception as e:
                logger.error(f"Error initializing plugin {self.name}: {e}", exc_info=True)
    
    def disable(self) -> None:
        """Disable the plugin."""
        self.enabled = False
        # Clean up the plugin if it has a cleanup function
        if hasattr(self.module, 'cleanup'):
            try:
                self.module.cleanup()
                logger.info(f"Cleaned up plugin: {self.name}")
            except Exception as e:
                logger.error(f"Error cleaning up plugin {self.name}: {e}", exc_info=True)


class PluginManager:
    """Manages the loading and unloading of plugins."""
    
    def __init__(self, plugin_dirs: Optional[List[Union[str, Path]]] = None):
        """Initialize the plugin manager.
        
        Args:
            plugin_dirs: List of directories to search for plugins
        """
        # Convert string paths to Path objects and ensure they exist
        self.plugin_dirs = [
            ensure_dir(Path(d)) 
            for d in (plugin_dirs or [])
            if Path(d).exists()
        ]
        
        # Add the default plugins directory if it exists
        default_plugin_dir = Path(__file__).parent.parent / 'plugins'
        if default_plugin_dir.exists() and default_plugin_dir not in self.plugin_dirs:
            self.plugin_dirs.append(default_plugin_dir)
        
        # Store loaded plugins
        self._plugins: Dict[str, Plugin] = {}
        self._loaded = False
    
    def discover_plugins(self) -> List[Path]:
        """Discover available plugins in the plugin directories.
        
        Returns:
            List of paths to potential plugin modules
        """
        plugin_paths = []
        
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            # Look for Python files and directories with __init__.py
            for item in plugin_dir.iterdir():
                # Skip hidden files and __pycache__
                if item.name.startswith('_') or item.name == '__pycache__':
                    continue
                    
                # Check for Python files
                if item.is_file() and item.suffix == '.py':
                    plugin_paths.append(item)
                # Check for package directories
                elif item.is_dir() and (item / '__init__.py').exists():
                    plugin_paths.append(item)
        
        return plugin_paths
    
    def load_plugins(self) -> Dict[str, Plugin]:
        """Load all discovered plugins.
        
        Returns:
            Dictionary of loaded plugins (name -> Plugin)
        """
        if self._loaded:
            return self._plugins
            
        plugin_paths = self.discover_plugins()
        
        for plugin_path in plugin_paths:
            try:
                plugin = self._load_plugin(plugin_path)
                if plugin:
                    self._plugins[plugin.name] = plugin
                    logger.info(f"Loaded plugin: {plugin.name}")
            except Exception as e:
                logger.error(f"Error loading plugin {plugin_path}: {e}", exc_info=True)
        
        # Initialize enabled plugins
        for plugin in self._plugins.values():
            if plugin.enabled:
                plugin.enable()
        
        self._loaded = True
        return self._plugins
    
    def _load_plugin(self, plugin_path: Path) -> Optional[Plugin]:
        """Load a single plugin from a file or directory.
        
        Args:
            plugin_path: Path to the plugin file or directory
            
        Returns:
            Loaded Plugin object, or None if loading failed
        """
        # Determine the module name
        if plugin_path.is_file():
            module_name = f"plugins.{plugin_path.stem}"
        else:
            module_name = f"plugins.{plugin_path.name}"
        
        # Check if the module is already loaded
        if module_name in sys.modules:
            module = sys.modules[module_name]
        else:
            # Load the module
            try:
                if plugin_path.is_file():
                    spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                else:
                    spec = importlib.util.spec_from_file_location(
                        module_name, 
                        plugin_path / "__init__.py"
                    )
                
                if spec is None or spec.loader is None:
                    logger.error(f"Could not load spec for {plugin_path}")
                    return None
                
                module = importlib.util.module_from_spec(spec)
                sys.modules[module_name] = module
                spec.loader.exec_module(module)
            except Exception as e:
                logger.error(f"Error loading module {module_name}: {e}")
                return None
        
        # Get plugin metadata
        metadata = {
            'name': getattr(module, '__name__', module_name),
            'version': getattr(module, '__version__', '0.1.0'),
            'author': getattr(module, '__author__', 'Unknown'),
            'description': inspect.getdoc(module) or "",
        }
        
        # Create the plugin instance
        plugin_name = metadata['name']
        plugin = Plugin(
            name=plugin_name,
            path=plugin_path,
            module=module,
            enabled=plugin_name not in settings.get('plugins.disabled_plugins', []),
            metadata=metadata
        )
        
        return plugin
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name.
        
        Args:
            name: Name of the plugin
            
        Returns:
            The Plugin object, or None if not found
        """
        if not self._loaded:
            self.load_plugins()
        return self._plugins.get(name)
    
    def get_plugins(self) -> Dict[str, Plugin]:
        """Get all loaded plugins.
        
        Returns:
            Dictionary of name -> Plugin
        """
        if not self._loaded:
            self.load_plugins()
        return self._plugins.copy()
    
    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin.
        
        Args:
            name: Name of the plugin to enable
            
        Returns:
            bool: True if the plugin was enabled, False otherwise
        """
        plugin = self.get_plugin(name)
        if plugin and not plugin.enabled:
            plugin.enable()
            
            # Update disabled plugins list in settings
            disabled = set(settings.get('plugins.disabled_plugins', []))
            disabled.discard(name)
            settings.set('plugins.disabled_plugins', list(disabled))
            
            return True
        return False
    
    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin.
        
        Args:
            name: Name of the plugin to disable
            
        Returns:
            bool: True if the plugin was disabled, False otherwise
        """
        plugin = self.get_plugin(name)
        if plugin and plugin.enabled:
            plugin.disable()
            
            # Update disabled plugins list in settings
            disabled = set(settings.get('plugins.disabled_plugins', []))
            disabled.add(name)
            settings.set('plugins.disabled_plugins', list(disabled))
            
            return True
        return False
    
    def reload_plugins(self) -> Dict[str, Plugin]:
        """Reload all plugins.
        
        Returns:
            Dictionary of reloaded plugins (name -> Plugin)
        """
        # Disable all plugins first
        for plugin in self._plugins.values():
            if plugin.enabled:
                plugin.disable()
        
        # Clear the plugins cache
        self._plugins.clear()
        self._loaded = False
        
        # Reload all plugins
        return self.load_plugins()
    
    def register_plugin_commands(self, command_processor: Any) -> None:
        """Register commands from all enabled plugins.
        
        Args:
            command_processor: The command processor instance to register with
        """
        if not self._loaded:
            self.load_plugins()
            
        for plugin in self._plugins.values():
            if not plugin.enabled:
                continue
                
            # Look for commands in the plugin module
            for name, obj in inspect.getmembers(plugin.module):
                if (
                    inspect.isfunction(obj) and 
                    hasattr(obj, '_command_info') and 
                    hasattr(command_processor, 'register_command')
                ):
                    # Register the command with the command processor
                    command_processor.register_command(obj)
                    plugin.register_command(obj)
                    logger.debug(f"Registered command {name} from plugin {plugin.name}")


# Singleton instance
plugin_manager = PluginManager()

# For backward compatibility
def load_plugins() -> Dict[str, Plugin]:
    """Load all plugins."""
    return plugin_manager.load_plugins()

def get_plugin(name: str) -> Optional[Plugin]:
    """Get a plugin by name."""
    return plugin_manager.get_plugin(name)

def get_plugins() -> Dict[str, Plugin]:
    """Get all loaded plugins."""
    return plugin_manager.get_plugins()

def enable_plugin(name: str) -> bool:
    """Enable a plugin."""
    return plugin_manager.enable_plugin(name)

def disable_plugin(name: str) -> bool:
    """Disable a plugin."""
    return plugin_manager.disable_plugin(name)

def reload_plugins() -> Dict[str, Plugin]:
    """Reload all plugins."""
    return plugin_manager.reload_plugins()
