"""
Example Plugin for Voice Assistant

This plugin demonstrates how to create custom commands and extend the functionality
of the voice assistant.
"""
import os
import random
import webbrowser
from typing import Dict, Any
from pathlib import Path

from core.command_processor import command_processor
from core.voice_engine import voice_engine

# Get the plugin's directory for storing data
PLUGIN_DIR = Path(__file__).parent.parent / 'data' / 'example_plugin'
os.makedirs(PLUGIN_DIR, exist_ok=True)

# --- Example 1: Simple Command ---
@command_processor.register_command(
    name="example_hello",
    description="A simple hello command",
    patterns=["say hello", "greet me"],
    requires_wake_word=True
)
def hello_command():
    """Respond with a random greeting"""
    greetings = [
        "Hello there!",
        "Hi! How can I help you today?",
        "Greetings! What can I do for you?",
        "Hey! Nice to hear from you.",
        "Hi there! Ready to assist you."
    ]
    response = random.choice(greetings)
    voice_engine.speak(response)
    return response

# --- Example 2: Command with Parameters ---
@command_processor.register_command(
    name="example_search",
    description="Search the web",
    patterns=["search for (.+)", "look up (.+)", "find (.+)"],
    requires_wake_word=True
)
def search_command(command):
    """Search the web for the given query"""
    # Extract search query from command text
    query = command.text
    for prefix in ["search for", "look up", "find"]:
        if query.lower().startswith(prefix):
            query = query[len(prefix):].strip()
            break
    
    if not query:
        voice_engine.speak("What would you like me to search for?")
        return
    
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(search_url)
    voice_engine.speak(f"Searching for {query}")
    return f"Searched for: {query}"

# --- Example 3: Command with State ---
class TodoList:
    def __init__(self):
        self.todos = []
        self.load_todos()
    
    def add_todo(self, item):
        self.todos.append(item)
        self.save_todos()
    
    def remove_todo(self, index):
        if 0 <= index < len(self.todos):
            return self.todos.pop(index)
        return None
    
    def list_todos(self):
        return self.todos
    
    def clear_todos(self):
        self.todos = []
        self.save_todos()
    
    def save_todos(self):
        with open(PLUGIN_DIR / 'todos.json', 'w') as f:
            json.dump(self.todos, f)
    
    def load_todos(self):
        try:
            with open(PLUGIN_DIR / 'todos.json', 'r') as f:
                self.todos = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.todos = []

# Create a single instance of TodoList
todo_list = TodoList()

@command_processor.register_command(
    name="example_add_todo",
    description="Add an item to the to-do list",
    patterns=["add (.+) to my to do list", "remind me to (.+)"],
    requires_wake_word=True
)
def add_todo(command):
    """Add an item to the to-do list"""
    # Extract the todo item from the command
    text = command.text.lower()
    todo_item = None
    
    for prefix in ["add ", "remind me to "]:
        if text.startswith(prefix):
            todo_item = text[len(prefix):].replace(" to my to do list", "").strip()
            break
    
    if todo_item:
        todo_list.add_todo(todo_item)
        voice_engine.speak(f"I've added '{todo_item}' to your to-do list.")
        return f"Added to-do: {todo_item}"
    else:
        voice_engine.speak("I didn't catch what you'd like to add to your to-do list.")
        return "No to-do item provided"

@command_processor.register_command(
    name="example_list_todos",
    description="List all to-do items",
    patterns=["what's on my to do list", "list my to dos", "show my reminders"],
    requires_wake_word=True
)
def list_todos():
    """List all to-do items"""
    todos = todo_list.list_todos()
    if not todos:
        voice_engine.speak("Your to-do list is empty.")
        return "No to-do items"
    
    response = "Here's your to-do list: " + ", ".join(f"{i+1}. {item}" for i, item in enumerate(todos))
    voice_engine.speak(response)
    return response

# --- Example 4: Command with External API ---
@command_processor.register_command(
    name="example_weather",
    description="Get the current weather",
    patterns=["what's the weather like", "how's the weather", "weather forecast"],
    requires_wake_word=True
)
def get_weather():
    """Get the current weather (example with mock data)"""
    # In a real implementation, you would call a weather API here
    # This is just a mock implementation
    weather_conditions = [
        "sunny with a high of 75 degrees",
        "cloudy with a chance of rain",
        "partly cloudy and mild",
        "rainy with thunderstorms",
        "clear and cool"
    ]
    
    forecast = random.choice(weather_conditions)
    response = f"The weather today is {forecast}."
    voice_engine.speak(response)
    return response

# --- Example 5: System Command ---
@command_processor.register_command(
    name="example_system_info",
    description="Get system information",
    patterns=["system info", "system status", "system information"],
    requires_wake_word=True
)
def system_info():
    """Display system information"""
    import platform
    import psutil
    
    # Get system information
    system = platform.system()
    node = platform.node()
    release = platform.release()
    
    # Get memory information
    memory = psutil.virtual_memory()
    total_memory = memory.total / (1024 ** 3)  # Convert to GB
    used_memory = memory.used / (1024 ** 3)
    memory_percent = memory.percent
    
    # Get CPU information
    cpu_percent = psutil.cpu_percent(interval=1)
    cpu_count = psutil.cpu_count()
    
    # Format the response
    response = f"""
    System: {system}
    Node: {node}
    Release: {release}
    
    Memory Usage: {used_memory:.1f} GB / {total_memory:.1f} GB ({memory_percent}%)
    CPU Usage: {cpu_percent}% across {cpu_count} cores
    """
    
    print(response)  # Print to console
    voice_engine.speak("Here's the system information. Check the console for details.")
    return "System information displayed in console"

# This function will be called when the plugin is loaded
def initialize():
    """Initialize the plugin"""
    print("Example plugin initialized")
    # Perform any initialization here

# Call initialize when the module is loaded
initialize()
