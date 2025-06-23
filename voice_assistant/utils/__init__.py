""
Utility functions and helpers for the Voice Assistant.

This module provides various utility functions that are used throughout
the application for common tasks such as file operations, text processing,
and system interactions.
"""

import os
import sys
import json
import logging
import platform
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, Callable

# Configure logging
logger = logging.getLogger(__name__)

def ensure_dir(directory: Union[str, Path]) -> Path:
    """Ensure that a directory exists, create it if it doesn't.
    
    Args:
        directory: Path to the directory
        
    Returns:
        Path: The path to the directory
    """
    path = Path(directory).expanduser().resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path

def read_json_file(file_path: Union[str, Path], default: Any = None) -> Any:
    """Read data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        The parsed JSON data or the default value
    """
    path = Path(file_path)
    if not path.exists():
        return default
        
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error reading JSON file {path}: {e}")
        return default

def write_json_file(file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
    """Write data to a JSON file.
    
    Args:
        file_path: Path to the JSON file
        data: Data to write (must be JSON serializable)
        indent: Indentation level for the JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except (TypeError, IOError) as e:
        logger.error(f"Error writing JSON file {path}: {e}")
        return False

def get_platform() -> str:
    """Get the current operating system platform.
    
    Returns:
        str: One of 'windows', 'linux', 'darwin', or 'unknown'
    """
    system = platform.system().lower()
    if system == 'windows':
        return 'windows'
    elif system == 'linux':
        return 'linux'
    elif system == 'darwin':
        return 'darwin'
    return 'unknown'

def run_command(cmd: Union[str, List[str]], cwd: Optional[Union[str, Path]] = None) -> str:
    """Run a shell command and return its output.
    
    Args:
        cmd: The command to run (as a string or list of args)
        cwd: Working directory for the command
        
    Returns:
        str: The command output
    """
    if isinstance(cmd, str):
        # Split the command string into a list of arguments
        import shlex
        cmd = shlex.split(cmd)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(cwd) if cwd else None,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        return e.stderr.strip()
    except Exception as e:
        logger.error(f"Error running command: {e}")
        return str(e)

def format_bytes(size: int) -> str:
    """Format a size in bytes to a human-readable string.
    
    Args:
        size: Size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"

def safe_get(dictionary: Dict, *keys, default=None) -> Any:
    """Safely get a value from a nested dictionary.
    
    Args:
        dictionary: The dictionary to search
        *keys: Keys to traverse (can be multiple levels deep)
        default: Default value if any key is not found
        
    Returns:
        The value at the specified path or the default value
    """
    current = dictionary
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def is_running_as_admin() -> bool:
    """Check if the script is running with administrator/root privileges.
    
    Returns:
        bool: True if running as admin/root, False otherwise
    """
    if get_platform() == 'windows':
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    else:
        return os.geteuid() == 0

def get_app_data_dir(app_name: str = "voice_assistant") -> Path:
    """Get the application data directory for the current platform.
    
    Args:
        app_name: Name of the application (used in the path)
        
    Returns:
        Path: Path to the application data directory
    """
    platform = get_platform()
    
    if platform == 'windows':
        base = os.environ.get('APPDATA', os.path.expanduser('~'))
        return Path(base) / app_name
    elif platform == 'darwin':  # macOS
        return Path(f"~/Library/Application Support/{app_name}").expanduser()
    else:  # Linux and others
        return Path(os.environ.get('XDG_DATA_HOME', '~/.local/share')).expanduser() / app_name

def retry(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """Decorator for retrying a function call.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt} failed: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        import time
                        time.sleep(delay)
            # If we get here, all attempts failed
            raise last_exception
        return wrapper
    return decorator

def async_retry(max_attempts: int = 3, delay: float = 1.0, exceptions=(Exception,)):
    """Decorator for retrying an async function call.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Delay between attempts in seconds
        exceptions: Tuple of exceptions to catch and retry on
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        logger.warning(
                            f"Attempt {attempt} failed: {e}. "
                            f"Retrying in {delay} seconds..."
                        )
                        import asyncio
                        await asyncio.sleep(delay)
            # If we get here, all attempts failed
            raise last_exception
        return wrapper
    return decorator

def get_resource_path(relative_path: str) -> Path:
    """Get the absolute path to a resource file.
    
    This works both in development and in PyInstaller bundles.
    
    Args:
        relative_path: Path relative to the project root
        
    Returns:
        Path: Absolute path to the resource
    """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = Path(sys._MEIPASS)  # type: ignore
    except AttributeError:
        # Not running in a PyInstaller bundle
        base_path = Path(__file__).parent.parent
    
    return base_path / relative_path

def format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-readable string.
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        str: Formatted duration (e.g., "2h 30m 15s")
    """
    seconds = int(round(seconds))
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0 or days > 0:
        parts.append(f"{hours}h")
    if minutes > 0 or hours > 0 or days > 0:
        parts.append(f"{minutes}m")
    parts.append(f"{seconds}s")
    
    return " ".join(parts)
