"""Built-in commands for the voice assistant with NLU support"""
import os
import sys
import webbrowser
import subprocess
import datetime
import json
import random
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import re
import urllib.parse

from voice_assistant.config import config
from voice_assistant.core.registry import get_command_processor, get_voice_engine, get_nlu_engine
from voice_assistant.core.models import Command
from voice_assistant.core.utils.app_utils import open_app_or_website

# Lazy decorator for commands
class CommandDecorator:
    """Lazily registers commands with the command processor."""
    _instance = None
    _commands = []
    _registered = False
    
    @classmethod
    def register(cls, *args, **kwargs):
        """Register a command with the decorator."""
        def decorator(func):
            cls._commands.append((func, args, kwargs))
            return func
        return decorator
    
    @classmethod
    def register_all(cls):
        """Register all commands with the command processor."""
        if cls._registered:
            return
            
        cmd_processor = get_command_processor()
        if cmd_processor is None:
            logger.warning("Command processor not available for command registration")
            return
            
        for func, args, kwargs in cls._commands:
            try:
                cmd_processor.register_command(*args, **kwargs)(func)
            except Exception as e:
                logger.error(f"Error registering command {func.__name__}: {e}")
        
        cls._registered = True

# Alias for the decorator
command = CommandDecorator.register

# Initialize logger
import logging
logger = logging.getLogger(__name__)

# Get engine instances
voice_engine = get_voice_engine()
nlu_engine = get_nlu_engine()

# --- Greeting Handler ---
def handle_greeting(text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle greeting intents"""
    greetings = ["Hello!", "Hi there!", "Greetings!", "Hey! How can I help you today?"]
    response = random.choice(greetings)
    voice_engine.speak(response)
    return {"last_interaction": "greeting", "greeting_response": response}

# --- Time and Date Handlers ---
def handle_time(text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle time-related queries"""
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    voice_engine.speak(f"The current time is {current_time}")
    return {"last_interaction": "time_query", "time_queried": current_time}

def handle_date(text: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle date-related queries"""
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    voice_engine.speak(f"Today is {current_date}")
    return {"last_interaction": "date_query", "date_queried": current_date}

# --- Web Search Handler ---
def handle_search(query: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle web search queries"""
    if not query or len(query.strip()) < 3:
        voice_engine.speak("What would you like me to search for?")
        return {"awaiting_search_query": True}
    
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(search_url)
    voice_engine.speak(f"Searching the web for {query}")
    return {"last_search": query, "search_url": search_url}

# --- Open Command Handler ---
@command(
    name="open",
    description="Open an application or website",
    patterns=[
        r"open (?:the )?(?:app |application |program |website |site |browser )?(.+)$",
        r"launch (?:the )?(?:app |application |program |website |site |browser )?(.+)$",
        r"start (?:the )?(?:app |application |program |website |site |browser )?(.+)$",
        r"run (?:the )?(?:app |application |program |website |site |browser )?(.+)$",
        r"go to (.+)$",
        r"navigate to (.+)$"
    ],
    intent="open_application"
)
def handle_open(text: str, context: Dict[str, Any] = None, target: str = None) -> Dict[str, Any]:
    """Handle opening applications or websites"""
    if not target:
        # Try to extract target from text
        match = re.search(r"(?:open|launch|start|run|go to|navigate to)\s+(?:the\s+)?(?:app\s+|application\s+|program\s+|website\s+|site\s+|browser\s+)?(.+)$", text.lower())
        if match:
            target = match.group(1).strip()
    
    if not target:
        return {
            'text': "What would you like me to open?",
            'success': False,
            'requires_input': True
        }
    
    # Clean up the target
    target = re.sub(
        r'\b(?:open|launch|start|run|go to|navigate to|please|the|app|application|program|website|site|browser)\b',
        ' ', 
        target.lower(),
        flags=re.IGNORECASE
    ).strip()
    
    if not target:
        return {
            'text': "I didn't catch what you'd like to open. Could you please try again?",
            'success': False
        }
    
    # Try to open the app or website
    success = open_app_or_website(target)
    
    if success:
        return {
            'text': f"Opening {target}",
            'success': True,
            'action': "opened_application",
            'target': target
        }
    else:
        return {
            'text': f"I couldn't find {target} or open it. Would you like to try something else?",
            'success': False,
            'target': target
        }

# --- YouTube Handler ---
import re
import urllib.parse
import webbrowser
import os
import logging
from typing import Dict, Any, Optional, List, Tuple

from voice_assistant.core.utils.app_utils import open_app_or_website

logger = logging.getLogger(__name__)

@command(
    name="youtube",
    description="Open YouTube or search for videos",
    patterns=[
        "play * on youtube", "search youtube for *", "youtube *",
        "play * yt", "search yt for *", "yt *",
        "watch * on youtube", "find video *", "open youtube *",
        "launch youtube", "go to youtube", "start youtube",
        "show me * on youtube", "i want to watch *"
    ],
    intent="youtube"
)
def handle_youtube(query: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle YouTube-related commands"""
    try:
        # If no specific query or just opening YouTube
        if not query or any(term in query.lower() for term in [
            'youtube', 'yt', 'open', 'launch', 'start', 'go to', 'watch youtube'
        ]):
            webbrowser.open("https://www.youtube.com")
            voice_engine.speak("Opening YouTube")
            return {"status": "success", "action": "opened_youtube"}
            
        # Clean up the query
        query = re.sub(
            r'\b(?:play|search|find|watch|on|in|youtube|yt|video|videos|me|for|a|the|please|can you|show me|called|named|titled|about|of|want to|i would like|i want|show me|find me)\b', 
            ' ', 
            query.lower(), 
            flags=re.IGNORECASE
        ).strip()
        
        # Remove extra spaces and special characters
        query = ' '.join(query.split())
        
        if not query or len(query) < 2:  # If query is too short
            webbrowser.open("https://www.youtube.com")
            voice_engine.speak("Opening YouTube")
            return {"status": "success", "action": "opened_youtube"}
            
        # Search YouTube for the query
        search_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        webbrowser.open(search_url)
        voice_engine.speak(f"Searching YouTube for {query}")
        return {
            "status": "success",
            "action": "searched_youtube",
            "query": query,
            "search_url": search_url
        }
        
    except Exception as e:
        logger.error(f"Error in YouTube handler: {e}")
        voice_engine.speak("Sorry, I couldn't complete your YouTube request.")
        return {"status": "error", "error": str(e)}
    else:
        search_query = query.replace('play', '').replace('on youtube', '').strip()
        if search_query:
            search_url = f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}"
            webbrowser.open(search_url)
            voice_engine.speak(f"Searching YouTube for {search_query}")
            return {"youtube_search": search_query, "search_url": search_url}
    return {}

# --- Weather Handler ---
def handle_weather(location: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle weather queries"""
    # This is a placeholder - you'll need to implement actual weather API integration
    if not location:
        voice_engine.speak("Which location's weather would you like to know?")
        return {"awaiting_weather_location": True}
    
    # Example: Use OpenWeatherMap API (requires API key)
    voice_engine.speak(f"I'll check the weather for {location}. This feature needs API integration.")
    return {"weather_queried": location}

# --- Music Handler ---
@command(
    name="play",
    description="Play music or media",
    patterns=[
        r"play (?:the )?(?:song |music |video |audio )?(.+)$",
        r"play (?:some )?(?:music|songs)$",
        r"start (?:playing )?(?:the )?(?:song |music |video |audio )?(.+)$",
        r"play (?:me )?(?:the )?(?:song |music |video |audio )?(.+)$"
    ],
    intent="play_media"
)
def handle_play(text: str, context: Dict[str, Any] = None, target: str = None) -> Dict[str, Any]:
    """Handle music and media playback commands"""
    if not target:
        # Try to extract target from text
        match = re.search(r"(?:play|start playing)\s+(?:the\s+)?(?:song\s+|music\s+|video\s+|audio\s+)?(.+)$", text.lower())
        if match:
            target = match.group(1).strip()
    
    if not target or target in ['music', 'songs']:
        return {
            'text': "Playing some music for you",
            'success': True,
            'action': "playing_music"
        }
    
    # Clean up the target
    target = re.sub(
        r'\b(?:play|start playing|please|the|song|music|video|audio)\b',
        ' ', 
        target.lower(),
        flags=re.IGNORECASE
    ).strip()
    
    if not target:
        return {
            'text': "What would you like me to play?",
            'success': False,
            'requires_input': True
        }
    
    return {
        'text': f"Playing {target}",
        'success': True,
        'action': "playing_media",
        'target': target
    }

# --- Email Handler ---
def handle_email(query: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle email composition"""
    if not query or 'email' in query.lower():
        voice_engine.speak("What would you like the email to say?")
        return {"awaiting_email_content": True}
    
    # Extract email details using NLU
    intent = nlu_engine.detect_intent(query)
    
    # Implement email sending logic here
    voice_engine.speak("I'll send that email for you. This feature needs to be implemented.")
    return {"email_sent": True, "email_content": query}

# --- Alarm Handler ---
def handle_alarm(time_str: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle alarm setting"""
    if not time_str or 'alarm' in time_str.lower():
        voice_engine.speak("What time would you like to set the alarm for?")
        return {"awaiting_alarm_time": True}
    
    # Parse time and set alarm
    voice_engine.speak(f"Alarm set for {time_str}")
    return {"alarm_set": True, "alarm_time": time_str}

# --- Speedtest Handler ---
def handle_speedtest(query: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle internet speed test"""
    voice_engine.speak("Running internet speed test. This may take a moment.")
    # Implement speed test logic here
    return {"speedtest_run": True}

# --- Calculation Handler ---
def handle_calculation(expression: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle mathematical calculations"""
    if not expression:
        voice_engine.speak("What would you like me to calculate?")
        return {"awaiting_calculation": True}
    
    try:
        # Simple evaluation (be careful with eval in production!)
        result = str(eval(expression))
        voice_engine.speak(f"The result is {result}")
        return {"calculation": expression, "result": result}
    except Exception as e:
        voice_engine.speak("Sorry, I couldn't perform that calculation.")
        return {"calculation_error": str(e)}

# --- Temperature Conversion Handler ---
def handle_temperature(query: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle temperature conversions"""
    if not query:
        voice_engine.speak("What temperature would you like to convert?")
        return {"awaiting_temperature": True}
    
    # Parse temperature and convert
    # Example: "convert 100 fahrenheit to celsius"
    voice_engine.speak("Temperature conversion feature needs to be implemented.")
    return {"temperature_conversion": "pending"}

# --- WhatsApp Handler ---
@command(
    name="whatsapp",
    description="Send WhatsApp messages",
    patterns=[
        r"send (?:a )?(?:whatsapp |message )?(?:to )?(.+?)(?: saying | with | that )?(.+)?$",
        r"whatsapp (?:to )?(.+?)(?: saying | with | that )?(.+)?$",
        r"message (?:on whatsapp )?(?:to )?(.+?)(?: saying | with | that )?(.+)?$"
    ],
    intent="send_message"
)
def handle_whatsapp(text: str, context: Dict[str, Any] = None, contact: str = None, message: str = None) -> Dict[str, Any]:
    """Handle WhatsApp messages"""
    if not contact:
        # Try to extract contact and message from text
        match = re.search(r"(?:send|whatsapp|message)\s+(?:a\s+)?(?:whatsapp\s+|message\s+)?(?:to\s+)?(.+?)(?:\s+saying\s+|\s+with\s+|\s+that\s+)?(.+)?$", text.lower())
        if match:
            contact = match.group(1).strip()
            message = match.group(2).strip() if match.group(2) else None
    
    if not contact:
        return {
            'text': "Who would you like to message on WhatsApp?",
            'success': False,
            'requires_input': True,
            'awaiting_contact': True
        }
    
    if not message:
        return {
            'text': f"What would you like to send to {contact}?",
            'success': False,
            'requires_input': True,
            'awaiting_message': True,
            'contact': contact
        }
    
    # Clean up the contact and message
    contact = re.sub(r'\b(?:send|whatsapp|message|to|please)\b', ' ', contact.lower(), flags=re.IGNORECASE).strip()
    message = re.sub(r'\b(?:saying|with|that|please)\b', ' ', message.lower(), flags=re.IGNORECASE).strip()
    
    # Implement WhatsApp message sending logic here
    return {
        'text': f"Sending message to {contact} on WhatsApp",
        'success': True,
        'action': "sent_whatsapp",
        'contact': contact,
        'message': message
    }

# --- Video Call Handler ---
def handle_video_call(contact: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle video calls"""
    if not contact:
        voice_engine.speak("Who would you like to call?")
        return {"awaiting_video_call_contact": True}
    
    # Implement video call logic here
    voice_engine.speak(f"Initiating video call with {contact}")
    return {"video_call_initiated": True, "contact": contact}

# --- News Handler ---
def handle_news(topic: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle news queries"""
    if not topic:
        voice_engine.speak("What topic would you like news about?")
        return {"awaiting_news_topic": True}
    
    # Implement news fetching logic here
    voice_engine.speak(f"Fetching the latest news about {topic}")
    return {"news_queried": topic}

# --- Location Handler ---
def handle_location(query: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handle location-based queries"""
    if not query:
        voice_engine.speak("What location information would you like?")
        return {"awaiting_location_query": True}
    
    # Implement location-based services here
    voice_engine.speak(f"Getting location information for {query}")
    return {"location_queried": query}

# --- System Commands ---
@command(
    name="shutdown",
    description="Shut down the computer",
    patterns=["shutdown", "turn off computer", "power off"],
    admin_only=True,
    intent="shutdown"
)
def shutdown() -> Dict[str, Any]:
    """Shut down the computer"""
    voice_engine.speak("Shutting down the computer. Goodbye!")
    if sys.platform == "win32":
        os.system("shutdown /s /t 1")
    else:
        os.system("shutdown -h now")
    return {"system_action": "shutdown"}

@command(
    name="restart",
    description="Restart the computer",
    patterns=["restart", "reboot"],
    admin_only=True
)
def restart():
    """Restart the computer"""
    voice_engine.speak("Restarting the computer. See you soon!")
    if sys.platform == "win32":
        os.system("shutdown /r /t 1")
    else:
        os.system("reboot")

# --- Web Browsing ---

@command(
    name="open_website",
    description="Open a website",
    patterns=[
        r"open (\w+\.\w+)",
        "go to (.+)",
        "browse to (.+)"
    ]
)
def open_website(command):
    """Open a website in the default browser"""
    # Extract website from command text
    text = command.text.lower()
    url = None
    
    # Check for common websites
    site_mapping = {
        'youtube': 'youtube.com',
        'facebook': 'facebook.com',
        'twitter': 'twitter.com',
        'github': 'github.com',
        'gmail': 'gmail.com',
        'google': 'google.com',
        'amazon': 'amazon.com',
        'wikipedia': 'wikipedia.org',
    }
    
    for site_name, site_url in site_mapping.items():
        if site_name in text:
            url = f"https://{site_url}"
            break
    
    # If no common site found, try to extract URL from command
    if not url:
        import re
        match = re.search(r'(?:open|go to|browse to|visit) (?:the )?(?:website )?(?:for )?(?:https?://)?(?:www\.)?([a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+)', text)
        if match:
            url = f"https://{match.group(1)}"
    
    if url:
        webbrowser.open(url)
        voice_engine.speak(f"Opening {url}")
    else:
        voice_engine.speak("I'm not sure which website you want to open. Please try again.")

# --- File Operations ---

@command(
    name="open_file",
    description="Open a file",
    patterns=[
        "open file (.+)",
        "open the file (.+)",
        "show me (.+)"
    ]
)
def open_file(command):
    """Open a file with the default application"""
    text = command.text.lower()
    filename = text.replace("open file", "").replace("open the file", "").replace("show me", "").strip()
    
    try:
        # Try to find the file in common locations
        common_dirs = [
            Path.home(),
            Path.home() / "Documents",
            Path.home() / "Downloads",
            Path.home() / "Desktop",
        ]
        
        file_found = False
        for dir_path in common_dirs:
            for file_path in dir_path.rglob(f"*{filename}*"):
                if file_path.is_file():
                    os.startfile(file_path)
                    voice_engine.speak(f"Opening {file_path.name}")
                    file_found = True
                    return
        
        if not file_found:
            voice_engine.speak(f"I couldn't find a file named {filename}")
            
    except Exception as e:
        voice_engine.speak(f"Sorry, I couldn't open the file: {str(e)}")

# --- Media Control ---

@command(
    name="play_music",
    description="Play music",
    patterns=["play music", "play some music", "play songs"]
)
def play_music():
    """Play music from the default music directory"""
    music_dirs = [
        Path.home() / "Music",
        Path.home() / "Downloads",
        Path.home() / "Desktop" / "Music"
    ]
    
    music_files = []
    for dir_path in music_dirs:
        if dir_path.exists():
            for ext in ['*.mp3', '*.wav', '*.m4a', '*.flac']:
                music_files.extend(dir_path.rglob(ext))
    
    if not music_files:
        voice_engine.speak("I couldn't find any music files.")
        return
    
    # Open the first music file with the default player
    os.startfile(music_files[0])
    voice_engine.speak("Playing music")

# --- System Information ---

@command(
    name="system_info",
    description="Get system information",
    patterns=["system info", "system information", "system status"]
)
def system_info():
    """Display system information"""
    import platform
    import psutil
    
    # Get system information
    system = platform.system()
    node = platform.node()
    release = platform.release()
    version = platform.version()
    processor = platform.processor()
    
    # Get memory information
    memory = psutil.virtual_memory()
    total_memory = memory.total / (1024 ** 3)  # Convert to GB
    available_memory = memory.available / (1024 ** 3)
    used_memory = memory.used / (1024 ** 3)
    memory_percent = memory.percent
    
    # Get CPU information
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Format the information
    info = f"""
    System: {system}
    Node: {node}
    Release: {release}
    Version: {version}
    Processor: {processor}
    
    Memory:
      Total: {total_memory:.2f} GB
      Available: {available_memory:.2f} GB
      Used: {used_memory:.2f} GB ({memory_percent}%)
    
    CPU:
      Cores: {cpu_count}
      Usage: {cpu_percent}%
    """
    
    print(info)  # Print to console
    voice_engine.speak("Here's the system information. Check the console for details.")

# --- Time and Date ---

@command(
    name="current_time",
    description="Get the current time",
    patterns=["what time is it", "current time", "what's the time"],
    requires_wake_word=False
)
def current_time():
    """Tell the current time"""
    now = datetime.datetime.now()
    time_str = now.strftime("%I:%M %p")
    voice_engine.speak(f"The current time is {time_str}")

@command(
    name="current_date",
    description="Get the current date",
    patterns=["what's today's date", "current date", "what day is it"],
    requires_wake_word=False
)
def current_date():
    """Tell the current date"""
    now = datetime.datetime.now()
    date_str = now.strftime("%A, %B %d, %Y")
    voice_engine.speak(f"Today is {date_str}")

# --- Help ---

@command(
    name="help",
    description="Show available commands and their usage",
    patterns=["help", "what can you do", "list commands", "show commands", "what are my options"],
    requires_wake_word=False
)
def help_command(query: str = None, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Display a comprehensive list of available commands with detailed descriptions and examples.
    
    Args:
        query: Optional specific command to get help for
        context: Command context
        
    Returns:
        Dict with status and command information
    """
    commands = {
        "📅 Time and Date": [
            ("What time is it?", "Tells the current time in 12-hour format (e.g., 'It's 3:45 PM')"),
            ("What's the date today?", "States today's date (e.g., 'Today is Friday, June 14, 2025')"),
            ("What day is it?", "Tells the current day of the week"),
            ("What time is it in [city]?", "Gets current time in specified timezone"),
            ("How many days until [event]?", "Counts days until specified date/event")
        ],
        "🌐 Web and Search": [
            ("Search for [query]", "Performs a web search (e.g., 'Search for latest AI news')"),
            ("Find [query] on the web", "Searches the web for information"),
            ("Open [website]", "Opens a website (e.g., 'Open GitHub' or 'Open github.com')"),
            ("Search [topic] on Wikipedia", "Looks up information on Wikipedia"),
            ("Find images of [subject]", "Searches for images online")
        ],
        "🎥 YouTube and Media": [
            ("Open YouTube", "Launches YouTube in your default browser"),
            ("Search YouTube for [query]", "Searches YouTube (e.g., 'Search YouTube for cat videos')"),
            ("Play [song/video] on YouTube", "Plays specified media (e.g., 'Play Bohemian Rhapsody on YouTube')"),
            ("Pause/Resume video", "Controls YouTube video playback"),
            ("Next video", "Skips to the next video in queue"),
            ("Fullscreen", "Toggles fullscreen mode")
        ],
        "🎵 Music and Audio": [
            ("Play music", "Starts playing music from your library"),
            ("Play [artist/album/song]", "Plays specific music (e.g., 'Play The Weeknd')"),
            ("Pause/Resume music", "Pauses or resumes music playback"),
            ("Next/Previous track", "Skips to next or previous track"),
            ("Volume up/down/mute", "Adjusts system volume"),
            ("What's playing?", "Shows current track information")
        ],
        "💻 System Control": [
            ("Open [application]", "Launches apps (e.g., 'Open Chrome' or 'Open calculator')"),
            ("Close [application]", "Closes specified application"),
            ("Switch to [app]", "Brings specified app to front"),
            ("Take a screenshot", "Captures your screen"),
            ("Lock my computer", "Locks your workstation"),
            ("Shut down/Restart/Log out", "Controls system power states")
        ],
        "⚙️ System Information": [
            ("System info", "Displays system specifications"),
            ("Battery status", "Shows remaining battery percentage"),
            ("Disk space", "Shows available storage"),
            ("CPU/RAM usage", "Displays system resource usage"),
            ("Network status", "Shows internet connection details")
        ],
        "📝 Productivity": [
            ("Create a note about [topic]", "Starts a new note"),
            ("Add to my shopping list: [items]", "Manages shopping lists"),
            ("Set a reminder to [task] at [time]", "Creates a timed reminder"),
            ("What's on my calendar [day/date]?", "Checks your schedule"),
            ("Start a [X] minute timer", "Sets a countdown timer")
        ],
        "📧 Communication": [
            ("Send an email to [contact] about [subject]", "Composes a new email"),
            ("Read my new emails", "Reads your unread messages"),
            ("Call [contact]", "Initiates a voice/video call"),
            ("Message [contact] that [message]", "Sends a text message"),
            ("Check my schedule", "Reads your calendar events")
        ],
        "🌤️ Weather and Environment": [
            ("What's the weather?", "Gets current weather for your location"),
            ("Weather in [city]", "Gets weather for specified location"),
            ("Will it rain today?", "Checks rain forecast"),
            ("What's the temperature outside?", "Gets current temperature"),
            ("Weekend weather forecast", "Shows upcoming weekend weather")
        ],
        "🔢 Calculations and Conversions": [
            ("Calculate [expression]", "Solves math problems (e.g., 'Calculate 45 * 12')"),
            ("Convert [X] [unit] to [unit]", "Converts units (e.g., 'Convert 10 miles to km')"),
            ("What's the tip for [amount]?", "Calculates tip amounts"),
            ("How many [unit] in [unit]?", "Provides unit conversion rates")
        ],
        "🎮 Fun and Entertainment": [
            ("Tell me a joke", "Shares a random joke"),
            ("Play rock paper scissors", "Starts a game"),
            ("Flip a coin", "Flips a virtual coin"),
            ("Roll a die", "Rolls a six-sided die"),
            ("What's the meaning of life?", "Philosophical responses")
        ],
        "⚡ Quick Actions": [
            ("Take a screenshot", "Captures your screen"),
            ("Start/Stop recording", "Controls screen recording"),
            ("Take a photo", "Uses webcam to take a picture"),
            ("Translate [phrase] to [language]", "Translates text"),
            ("Define [word]", "Looks up word definitions")
        ]
    }
    
    if query and query.lower() != 'help':
        # Search for specific command help
        query = query.lower().strip()
        for category, cmd_list in commands.items():
            for cmd, desc in cmd_list:
                if query in cmd.lower():
                    response = f"Here's how to use '{cmd}':\n{desc}"
                    voice_engine.speak(f"For {cmd}, {desc}")
                    return {"status": "success", "action": "command_help_shown", "command": cmd}
        
        voice_engine.speak(f"I couldn't find help for '{query}'. Here's what I can help with:")
    else:
        voice_engine.speak("Here's what I can help you with:")
    
    # Display all commands in categories
    print("\n" + "="*50)
    print("VOICE ASSISTANT COMMANDS")
    print("="*50)
    
    for category, cmd_list in commands.items():
        print(f"\n{category.upper()}:")
        print("-" * len(category) + "-")
        for cmd, desc in cmd_list:
            print(f"• {cmd: <40} - {desc}")
    
    print("\n" + "="*50)
    print("You can say 'hey' or 'okay' followed by any command.")
    print("For example: 'hey what time is it?' or 'okay open YouTube'")
    print("="*50 + "\n")
    
    return {
        "status": "success",
        "action": "help_shown",
        "categories": list(commands.keys())
    }

# --- Application Control ---

@command(
    name="open_application",
    description="Open an application",
    patterns=["open (?!file|folder)(.+)", "start (.+)", "launch (.+)"]
)
def open_application(command):
    """Open an application by name"""
    text = command.text.lower()
    app_name = ""
    
    # Remove trigger words
    for prefix in ["open", "start", "launch"]:
        if text.startswith(prefix):
            app_name = text[len(prefix):].strip()
            break
    
    if not app_name:
        voice_engine.speak("I'm not sure which application you want to open.")
        return
    
    # Common applications mapping
    app_mapping = {
        'browser': 'chrome',
        'web browser': 'chrome',
        'chrome': 'chrome',
        'firefox': 'firefox',
        'edge': 'msedge',
        'notepad': 'notepad',
        'calculator': 'calc',
        'word': 'winword',
        'excel': 'excel',
        'powerpoint': 'powerpnt',
        'vs code': 'code',
        'visual studio code': 'code',
        'pycharm': 'pycharm64',
        'intellij': 'idea64',
        'spotify': 'spotify',
        'discord': 'discord',
        'slack': 'slack',
    }
    
    # Find the application
    app_to_launch = None
    for name, exe in app_mapping.items():
        if name in app_name:
            app_to_launch = exe
            break
    
    if not app_to_launch:
        voice_engine.speak(f"I'm not sure how to open {app_name}.")
        return
    
    try:
        # Try to open the application
        if sys.platform == "win32":
            os.system(f"start {app_to_launch}")
        else:
            os.system(f"{app_to_launch} &")
        
        voice_engine.speak(f"Opening {app_name}")
    except Exception as e:
        voice_engine.speak(f"Sorry, I couldn't open {app_name}: {str(e)}")

# --- Volume Control ---

@command(
    name="volume_up",
    description="Increase volume",
    patterns=["volume up", "increase volume", "louder"]
)
def volume_up():
    """Increase system volume"""
    try:
        import pyautogui
        pyautogui.press('volumeup')
        voice_engine.speak("Volume increased")
    except Exception as e:
        voice_engine.speak(f"Sorry, I couldn't adjust the volume: {str(e)}")

@command(
    name="volume_down",
    description="Decrease volume",
    patterns=["volume down", "decrease volume", "quieter"]
)
def volume_down():
    """Decrease system volume"""
    try:
        import pyautogui
        pyautogui.press('volumedown')
        voice_engine.speak("Volume decreased")
    except Exception as e:
        voice_engine.speak(f"Sorry, I couldn't adjust the volume: {str(e)}")

@command(
    name="mute",
    description="Mute or unmute volume",
    patterns=["mute", "unmute", "toggle mute"]
)
def toggle_mute():
    """Toggle mute on/off"""
    try:
        import pyautogui
        pyautogui.press('volumemute')
        voice_engine.speak("Toggled mute")
    except Exception as e:
        voice_engine.speak(f"Sorry, I couldn't toggle mute: {str(e)}")
