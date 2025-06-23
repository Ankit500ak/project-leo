import os
import sys
import winreg
import webbrowser
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

# Common applications and their executable names
COMMON_APPS = {
    'chrome': 'chrome.exe',
    'google chrome': 'chrome.exe',
    'firefox': 'firefox.exe',
    'edge': 'msedge.exe',
    'vscode': 'code.exe',
    'visual studio code': 'code.exe',
    'pycharm': 'pycharm64.exe',
    'intellij': 'idea64.exe',
    'spotify': 'spotify.exe',
    'discord': 'discord.exe',
    'whatsapp': 'whatsapp.exe',
    'telegram': 'telegram.exe',
    'notepad': 'notepad.exe',
    'word': 'winword.exe',
    'excel': 'excel.exe',
    'powerpoint': 'powerpnt.exe',
    'outlook': 'outlook.exe',
    'photoshop': 'photoshop.exe',
    'premiere': 'adobe premiere pro.exe',
}

# Common websites and their URLs
COMMON_WEBSITES = {
    'youtube': 'https://youtube.com',
    'yt': 'https://youtube.com',
    'github': 'https://github.com',
    'git': 'https://github.com',
    'gmail': 'https://mail.google.com',
    'google': 'https://google.com',
    'maps': 'https://maps.google.com',
    'drive': 'https://drive.google.com',
    'docs': 'https://docs.google.com',
    'sheets': 'https://sheets.google.com',
    'slides': 'https://slides.google.com',
    'facebook': 'https://facebook.com',
    'twitter': 'https://twitter.com',
    'instagram': 'https://instagram.com',
    'linkedin': 'https://linkedin.com',
    'reddit': 'https://reddit.com',
    'wikipedia': 'https://wikipedia.org',
    'amazon': 'https://amazon.com',
    'leetcode': 'https://leetcode.com',
    'stackoverflow': 'https://stackoverflow.com',
    'stack overflow': 'https://stackoverflow.com',
}

def get_installed_apps() -> Dict[str, str]:
    """Get a dictionary of installed applications and their executable paths"""
    installed_apps = {}
    
    # Check common install locations
    common_paths = [
        os.path.join(os.environ.get('PROGRAMFILES', ''), '*'),
        os.path.join(os.environ.get('PROGRAMFILES(X86)', ''), '*'),
        os.path.join(os.environ.get('LOCALAPPDATA', ''), 'Programs', '*'),
        os.path.join(os.environ.get('APPDATA', ''), '..', 'Local', 'Programs', '*'),
    ]
    
    import glob
    for path in common_paths:
        try:
            for app_path in glob.glob(path):
                app_name = os.path.basename(app_path).lower()
                # Look for exe files in the directory
                for exe in glob.glob(os.path.join(app_path, '*.exe')):
                    exe_name = os.path.basename(exe).lower()
                    installed_apps[app_name] = exe
                    installed_apps[exe_name] = exe
        except Exception as e:
            logger.debug(f"Error scanning {path}: {e}")
    
    return installed_apps

def find_app_executable(app_name: str) -> Optional[str]:
    """Find the executable path for the given app name"""
    app_name = app_name.lower().strip()
    
    # First check if it's a known app with a standard name
    if app_name in COMMON_APPS:
        standard_exe = COMMON_APPS[app_name]
        # Check if it's in PATH
        for path in os.environ['PATH'].split(os.pathsep):
            exe_path = os.path.join(path, standard_exe)
            if os.path.isfile(exe_path):
                return exe_path
    
    # Search in installed apps
    installed_apps = get_installed_apps()
    
    # Exact match
    if app_name in installed_apps:
        return installed_apps[app_name]
    
    # Partial match
    for name, path in installed_apps.items():
        if app_name in name or any(word in name for word in app_name.split()):
            return path
    
    return None

def open_app_or_website(target: str) -> bool:
    """
    Try to open an application, fall back to website if not found
    Returns True if successful, False otherwise
    """
    target = target.lower().strip()
    
    # Check if it's a known website
    website_url = COMMON_WEBSITES.get(target)
    if website_url:
        webbrowser.open(website_url)
        return True
    
    # Try to find and open the application
    app_path = find_app_executable(target)
    if app_path:
        try:
            os.startfile(app_path)
            return True
        except Exception as e:
            logger.error(f"Failed to open application {target}: {e}")
    
    # If not found as app, try as website
    try:
        # Try common TLDs if it looks like a website name
        for tld in ['com', 'org', 'net', 'io', 'dev']:
            try:
                webbrowser.open(f"https://{target}.{tld}")
                return True
            except:
                continue
                
        # Try direct search as last resort
        webbrowser.open(f"https://www.google.com/search?q={target}")
        return True
    except Exception as e:
        logger.error(f"Failed to open website {target}: {e}")
        return False
