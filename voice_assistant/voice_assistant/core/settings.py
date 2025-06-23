"""Settings management for the Voice Assistant.

This module handles loading, saving, and managing application settings.
"""

import os
import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union, List

from voice_assistant.utils import ensure_dir, read_json_file, write_json_file, get_app_data_dir

logger = logging.getLogger(__name__)

class SettingsManager:
    """Manages application settings with persistence.
    
    Settings are stored in a JSON file and can be accessed like a dictionary.
    Changes are automatically saved to disk.
    """
    
    # Default settings
    DEFAULTS = {
        'voice': {
            'enabled': True,
            'voice_id': 1,  # 0 for male, 1 for female (Windows)
            'rate': 170,    # Words per minute
            'volume': 0.9,  # 0.0 to 1.0
            'energy_threshold': 300,  # Minimum audio energy to consider for recording
            'pause_threshold': 0.8,   # Seconds of non-speaking audio before a phrase is complete
            'dynamic_energy_threshold': True,  # Adjust threshold based on ambient noise
            'wake_words': ["hey assistant", "hello buddy", "computer"],
            'activation_method': 'continuous',  # 'continuous' or 'push_to_talk'
            'push_to_talk_key': 'ctrl+space',  # Keyboard shortcut for push-to-talk
        },
        'hotkeys': {
            'push_to_talk': 'ctrl+space',
            'toggle_listening': 'ctrl+shift+space',
            'stop_talking': 'esc',
        },
        'ui': {
            'theme': 'dark',  # 'light' or 'dark'
            'font_family': 'Segoe UI',
            'font_size': 10,
            'show_tray_icon': True,
            'minimize_to_tray': True,
            'start_minimized': False,
            'show_notifications': True,
        },
        'features': {
            'auto_update': True,
            'auto_start': False,
            'check_for_updates': True,
            'save_command_history': True,
            'max_command_history': 1000,
            'enable_analytics': False,
            'enable_crash_reports': True,
        },
        'advanced': {
            'log_level': 'INFO',  # DEBUG, INFO, WARNING, ERROR, CRITICAL
            'max_log_size': 10,  # MB
            'max_log_files': 5,
            'debug_mode': False,
            'enable_profiling': False,
            'enable_remote_debugging': False,
        },
        'paths': {
            'downloads': str(Path.home() / 'Downloads'),
            'documents': str(Path.home() / 'Documents'),
            'music': str(Path.home() / 'Music'),
            'pictures': str(Path.home() / 'Pictures'),
            'videos': str(Path.home() / 'Videos'),
            'desktop': str(Path.home() / 'Desktop'),
        },
        'plugins': {
            'enabled_plugins': [],  # List of enabled plugin names
            'auto_update_plugins': True,
            'allow_external_plugins': False,
            'plugin_directories': [],  # Additional directories to search for plugins
        },
        'api_keys': {
            # API keys will be stored here
        },
    }
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """Initialize the settings manager.
        
        Args:
            config_file: Path to the config file. If None, a default location is used.
        """
        if config_file is None:
            config_dir = get_app_data_dir()
            self.config_file = config_dir / 'config.json'
        else:
            self.config_file = Path(config_file)
        
        # Ensure the config directory exists
        ensure_dir(self.config_file.parent)
        
        # Load settings from file or use defaults
        self._settings = self._load_settings()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from the config file or use defaults."""
        # Start with default settings
        settings = self.DEFAULTS.copy()
        
        # Try to load settings from file
        file_settings = read_json_file(self.config_file, {})
        
        # Merge file settings with defaults (deep merge)
        self._deep_merge(settings, file_settings)
        
        return settings
    
    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]) -> None:
        """Recursively merge two dictionaries."""
        for key, value in update.items():
            if (key in base and 
                isinstance(base[key], dict) and 
                isinstance(value, dict)):
                # Recursively merge dictionaries
                self._deep_merge(base[key], value)
            else:
                # Overwrite with new value
                base[key] = value
    
    def save(self) -> bool:
        """Save the current settings to the config file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            return write_json_file(self.config_file, self._settings)
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value using dot notation.
        
        Args:
            key: The setting key in dot notation (e.g., 'voice.rate')
            default: Default value if the key is not found
            
        Returns:
            The setting value or the default value if not found
        """
        keys = key.split('.')
        value = self._settings
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any, save: bool = True) -> bool:
        """Set a setting value using dot notation.
        
        Args:
            key: The setting key in dot notation (e.g., 'voice.rate')
            value: The value to set
            save: Whether to save the settings to disk after updating
            
        Returns:
            bool: True if successful, False otherwise
        """
        keys = key.split('.')
        current = self._settings
        
        try:
            # Navigate to the parent of the target key
            for k in keys[:-1]:
                if k not in current or not isinstance(current[k], dict):
                    current[k] = {}
                current = current[k]
            
            # Set the value
            current[keys[-1]] = value
            
            # Save to disk if requested
            if save:
                return self.save()
            return True
        except Exception as e:
            logger.error(f"Error setting {key}: {e}")
            return False
    
    def reset_to_defaults(self) -> None:
        """Reset all settings to their default values."""
        self._settings = self.DEFAULTS.copy()
        self.save()
    
    def get_all_settings(self) -> Dict[str, Any]:
        """Get a copy of all settings.
        
        Returns:
            Dict containing all settings
        """
        return self._settings.copy()
    
    def update(self, new_settings: Dict[str, Any], save: bool = True) -> bool:
        """Update multiple settings at once.
        
        Args:
            new_settings: Dictionary of settings to update
            save: Whether to save the settings to disk after updating
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self._deep_merge(self._settings, new_settings)
            if save:
                return self.save()
            return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    def add_api_key(self, service: str, key: str, save: bool = True) -> bool:
        """Add or update an API key.
        
        Args:
            service: The service name (e.g., 'openai', 'google')
            key: The API key
            save: Whether to save the settings to disk after updating
            
        Returns:
            bool: True if successful, False otherwise
        """
        if 'api_keys' not in self._settings:
            self._settings['api_keys'] = {}
        
        self._settings['api_keys'][service] = key
        
        if save:
            return self.save()
        return True
    
    def get_api_key(self, service: str, default: str = '') -> str:
        """Get an API key.
        
        Args:
            service: The service name
            default: Default value if the key is not found
            
        Returns:
            The API key or the default value if not found
        """
        return self._settings.get('api_keys', {}).get(service, default)
    
    def remove_api_key(self, service: str, save: bool = True) -> bool:
        """Remove an API key.
        
        Args:
            service: The service name
            save: Whether to save the settings to disk after updating
            
        Returns:
            bool: True if the key was removed, False otherwise
        """
        if 'api_keys' in self._settings and service in self._settings['api_keys']:
            del self._settings['api_keys'][service]
            if save:
                return self.save()
            return True
        return False


# Singleton instance
settings = SettingsManager()

# For backward compatibility
def get_setting(key: str, default: Any = None) -> Any:
    """Get a setting value using dot notation."""
    return settings.get(key, default)

def set_setting(key: str, value: Any, save: bool = True) -> bool:
    """Set a setting value using dot notation."""
    return settings.set(key, value, save)
