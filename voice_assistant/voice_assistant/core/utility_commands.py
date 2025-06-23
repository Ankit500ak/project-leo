"""Utility commands for the voice assistant."""
import os
import subprocess
import webbrowser
import pyperclip
from typing import Dict, Any, List, Optional
from pathlib import Path

from voice_assistant.core.registry import get_voice_engine
from voice_assistant.core.builtin_commands import command

voice_engine = get_voice_engine()

@command(
    name="open_application",
    description="Open an application on the computer",
    patterns=["open *", "launch *", "start *"]
)
def open_application(app_name: str) -> Dict[str, Any]:
    """
    Open an application by name.
    
    Args:
        app_name: Name of the application to open
        
    Returns:
        Dict with status and details about the opened application
    """
    # Common applications and their executable names
    app_mapping = {
        "chrome": "chrome",
        "google chrome": "chrome",
        "firefox": "firefox",
        "edge": "msedge",
        "safari": "safari",
        "spotify": "spotify",
        "discord": "discord",
        "slack": "slack",
        "vscode": "code",
        "visual studio code": "code",
        "pycharm": "pycharm",
        "intellij": "idea",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "outlook": "outlook",
        "notepad": "notepad",
        "calculator": "calc",
        "paint": "mspaint",
        "photoshop": "photoshop",
        "premiere": "premiere pro",
        "zoom": "zoom",
        "teams": "teams",
        "whatsapp": "whatsapp",
        "telegram": "telegram",
        "spotify": "spotify",
        "itunes": "itunes",
        "vlc": "vlc",
        "steam": "steam",
        "epic games": "epicgameslauncher",
    }
    
    # Common application paths on Windows
    app_paths = {
        "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "vscode": r"C:\Users\{username}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
        "spotify": r"C:\Users\{username}\AppData\Roaming\Spotify\Spotify.exe",
        "discord": r"C:\Users\{username}\AppData\Local\Discord\app-*\Discord.exe",
    }
    
    try:
        app_name = app_name.lower()
        
        # Check if it's a web URL
        if any(prefix in app_name for prefix in ['http://', 'https://', 'www.']):
            webbrowser.open(app_name)
            return {"status": "success", "action": "opened_url", "url": app_name}
        
        # Check if it's a mapped application
        if app_name in app_mapping:
            try:
                # Try to open using the mapped name
                subprocess.Popen([app_mapping[app_name]])
                voice_engine.speak(f"Opening {app_name}")
                return {"status": "success", "app": app_name, "method": "direct_launch"}
            except Exception as e:
                # If direct launch fails, try to open using the full path
                if app_name in app_paths:
                    path = app_paths[app_name].format(username=os.getlogin())
                    subprocess.Popen([path])
                    voice_engine.speak(f"Opening {app_name}")
                    return {"status": "success", "app": app_name, "method": "path_launch"}
        
        # Try to open as a file or folder
        if os.path.exists(app_name):
            os.startfile(app_name)
            voice_engine.speak(f"Opening {os.path.basename(app_name)}")
            return {"status": "success", "path": app_name, "method": "file_open"}
        
        # Try to search for the application in the start menu
        try:
            subprocess.Popen(f'start {app_name}', shell=True)
            voice_engine.speak(f"Opening {app_name}")
            return {"status": "success", "app": app_name, "method": "start_menu_search"}
        except:
            pass
        
        # If we get here, we couldn't open the application
        voice_engine.speak(f"I couldn't find an application named {app_name}")
        return {"status": "error", "error": "Application not found", "app": app_name}
        
    except Exception as e:
        error_msg = f"Error opening {app_name}: {str(e)}"
        voice_engine.speak("I encountered an error while trying to open that application.")
        return {"status": "error", "error": error_msg}

@command(
    name="close_application",
    description="Close an application",
    patterns=["close *", "exit *", "quit *"]
)
def close_application(app_name: str) -> Dict[str, Any]:
    """
    Close an application by name.
    
    Args:
        app_name: Name of the application to close
        
    Returns:
        Dict with status and details about the closed application
    """
    try:
        app_name = app_name.lower()
        
        # Special cases for common applications
        if "chrome" in app_name or "browser" in app_name:
            os.system("taskkill /f /im chrome.exe")
        elif "firefox" in app_name:
            os.system("taskkill /f /im firefox.exe")
        elif "edge" in app_name:
            os.system("taskkill /f /im msedge.exe")
        elif "word" in app_name:
            os.system("taskkill /f /im WINWORD.EXE")
        elif "excel" in app_name:
            os.system("taskkill /f /im EXCEL.EXE")
        elif "powerpoint" in app_name or "power point" in app_name:
            os.system("taskkill /f /im POWERPNT.EXE")
        elif "outlook" in app_name:
            os.system("taskkill /f /im OUTLOOK.EXE")
        else:
            # Try to kill by process name
            os.system(f"taskkill /f /im {app_name}.exe")
        
        voice_engine.speak(f"Closing {app_name}")
        return {"status": "success", "app": app_name}
        
    except Exception as e:
        error_msg = f"Error closing {app_name}: {str(e)}"
        voice_engine.speak("I couldn't close that application.")
        return {"status": "error", "error": error_msg}

@command(
    name="copy_to_clipboard",
    description="Copy text to clipboard",
    patterns=["copy * to clipboard", "copy *"]
)
def copy_to_clipboard(text: str) -> Dict[str, Any]:
    """
    Copy the given text to the clipboard.
    
    Args:
        text: Text to copy to clipboard
        
    Returns:
        Dict with status and the copied text
    """
    try:
        pyperclip.copy(text)
        voice_engine.speak(f"Copied to clipboard: {text[:50]}{'...' if len(text) > 50 else ''}")
        return {"status": "success", "copied_text": text}
    except Exception as e:
        error_msg = f"Error copying to clipboard: {str(e)}"
        voice_engine.speak("I couldn't copy that to the clipboard.")
        return {"status": "error", "error": error_msg}

@command(
    name="read_clipboard",
    description="Read the contents of the clipboard",
    patterns=["read clipboard", "what's on the clipboard", "paste clipboard"]
)
def read_clipboard() -> Dict[str, Any]:
    """
    Read and speak the contents of the clipboard.
    
    Returns:
        Dict with status and the clipboard contents
    """
    try:
        text = pyperclip.paste()
        if not text.strip():
            voice_engine.speak("The clipboard is empty.")
            return {"status": "success", "is_empty": True}
        
        voice_engine.speak("Here's what's on the clipboard: " + text[:100])
        if len(text) > 100:
            voice_engine.speak("... and more")
        
        return {
            "status": "success",
            "content": text,
            "length": len(text)
        }
    except Exception as e:
        error_msg = f"Error reading clipboard: {str(e)}"
        voice_engine.speak("I couldn't read the clipboard.")
        return {"status": "error", "error": error_msg}

@command(
    name="create_shortcut",
    description="Create a desktop shortcut",
    patterns=["create shortcut for *", "make a shortcut to *"]
)
def create_shortcut(target: str, name: Optional[str] = None) -> Dict[str, Any]:
    """
    Create a desktop shortcut to a file, folder, or application.
    
    Args:
        target: Path to the target file/folder/application
        name: Optional name for the shortcut
        
    Returns:
        Dict with status and details about the created shortcut
    """
    try:
        import winshell
        from win32com.client import Dispatch
        
        desktop = winshell.desktop()
        
        if not name:
            name = os.path.basename(target)
            if '.' in name:
                name = name.split('.')[0]
            name += " Shortcut"
        
        path = os.path.join(desktop, f"{name}.lnk")
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(path)
        shortcut.TargetPath = target
        shortcut.WorkingDirectory = os.path.dirname(target)
        shortcut.save()
        
        voice_engine.speak(f"Created shortcut: {name}")
        return {
            "status": "success",
            "shortcut_path": path,
            "target": target,
            "name": name
        }
    except Exception as e:
        error_msg = f"Error creating shortcut: {str(e)}"
        voice_engine.speak("I couldn't create that shortcut.")
        return {"status": "error", "error": error_msg}
