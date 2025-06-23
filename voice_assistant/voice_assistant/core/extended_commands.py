"""Extended command implementations for the voice assistant."""
import os
import sys
import webbrowser
import subprocess
import datetime
import json
import random
import logging
import subprocess
import webbrowser
import datetime
import requests
import platform
import psutil
import pyautogui
import pyperclip
import wikipedia
import pyjokes
import wolframalpha
import speedtest
import pywhatkit
import pyttsx3
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import quote

# Third-party imports
import psutil
import speedtest
import wikipedia
import pyjokes

# Local imports
from voice_assistant.core.voice_engine import voice_engine
from voice_assistant.core.command_processor import command
from voice_assistant.config import config
from voice_assistant.core.registry import get_command_processor, get_voice_engine, get_nlu_engine
from voice_assistant.core.models import Command
from voice_assistant.core.builtin_commands import command, CommandDecorator

# Initialize logger
logger = logging.getLogger(__name__)

# Initialize engines
voice_engine = get_voice_engine()
nlu_engine = get_nlu_engine()
logger = logging.getLogger(__name__)

# --- System Information ---
@command(
    name="system_info_extended",
    description="Get detailed system information",
    patterns=["system details", "system specifications", "detailed system info"]
)
def system_info_extended():
    """Return detailed system information."""
    try:
        system = platform.system()
        release = platform.release()
        version = platform.version()
        machine = platform.machine()
        processor = platform.processor()
        
        # CPU information
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory information
        memory = psutil.virtual_memory()
        total_memory = round(memory.total / (1024 ** 3), 2)  # Convert to GB
        available_memory = round(memory.available / (1024 ** 3), 2)
        used_memory = round(memory.used / (1024 ** 3), 2)
        memory_percent = memory.percent
        
        # Disk information
        disk = psutil.disk_usage('/')
        total_disk = round(disk.total / (1024 ** 3), 2)
        used_disk = round(disk.used / (1024 ** 3), 2)
        free_disk = round(disk.free / (1024 ** 3), 2)
        disk_percent = disk.percent
        
        # Network information
        net_io = psutil.net_io_counters()
        bytes_sent = round(net_io.bytes_sent / (1024 ** 2), 2)  # Convert to MB
        bytes_recv = round(net_io.bytes_recv / (1024 ** 2), 2)
        
        # Battery information
        try:
            battery = psutil.sensors_battery()
            battery_percent = battery.percent
            power_plugged = "plugged in" if battery.power_plugged else "not plugged in"
            battery_info = f"{battery_percent}% ({power_plugged})"
        except:
            battery_info = "Not available"
        
        # Format the information
        info = f"""
        System Information:
        -------------------
        OS: {system} {release} ({version})
        Machine: {machine}
        Processor: {processor}
        
        CPU Usage: {cpu_percent}% of {cpu_count} cores
        
        Memory:
          Total: {total_memory} GB
          Used: {used_memory} GB ({memory_percent}%)
          Available: {available_memory} GB
        
        Disk Usage:
          Total: {total_disk} GB
          Used: {used_disk} GB ({disk_percent}%)
          Free: {free_disk} GB
        
        Network:
          Sent: {bytes_sent} MB
          Received: {bytes_recv} MB
        
        Battery: {battery_info}
        """
        
        voice_engine.speak("Here's your system information.")
        return {"status": "success", "info": info}
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        voice_engine.speak("I couldn't retrieve the system information.")
        return {"status": "error", "error": str(e)}

# --- Internet Speed Test ---
@command(
    name="speed_test",
    description="Run an internet speed test",
    patterns=["test internet speed", "check my connection speed", "speed test"]
)
def speed_test():
    """Run an internet speed test and report the results."""
    try:
        voice_engine.speak("Running speed test. This may take a moment.")
        st = speedtest.Speedtest()
        
        # Get best server
        voice_engine.speak("Finding the best server.")
        st.get_best_server()
        
        # Test download speed
        voice_engine.speak("Testing download speed.")
        download_speed = st.download() / 1_000_000  # Convert to Mbps
        
        # Test upload speed
        voice_engine.speak("Testing upload speed.")
        upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        
        # Get ping
        ping = st.results.ping
        
        # Format results
        results = f"""
        Speed Test Results:
        -------------------
        Download: {download_speed:.2f} Mbps
        Upload: {upload_speed:.2f} Mbps
        Ping: {ping:.2f} ms
        """
        
        voice_engine.speak(f"Your download speed is {download_speed:.1f} megabits per second.")
        voice_engine.speak(f"Your upload speed is {upload_speed:.1f} megabits per second.")
        voice_engine.speak(f"Your ping is {ping:.0f} milliseconds.")
        
        return {
            "status": "success",
            "download_speed": download_speed,
            "upload_speed": upload_speed,
            "ping": ping,
            "results": results
        }
    except Exception as e:
        logger.error(f"Error running speed test: {e}")
        voice_engine.speak("I couldn't complete the speed test. Please check your internet connection.")
        return {"status": "error", "error": str(e)}

# --- Wikipedia Search ---
@command(
    name="wikipedia_search",
    description="Search Wikipedia for information",
    patterns=["search wikipedia for *", "look up * on wikipedia", "wikipedia *"]
)
def wikipedia_search(query: str):
    """Search Wikipedia for the given query and return a summary."""
    try:
        voice_engine.speak(f"Searching Wikipedia for {query}.")
        
        # Set language (you can change this based on user preferences)
        wikipedia.set_lang("en")
        
        # Search for the page
        search_results = wikipedia.search(query)
        if not search_results:
            voice_engine.speak(f"I couldn't find any information about {query} on Wikipedia.")
            return {"status": "not_found", "query": query}
        
        # Get the first result
        page_title = search_results[0]
        try:
            page = wikipedia.page(page_title, auto_suggest=False)
        except wikipedia.DisambiguationError as e:
            # If it's a disambiguation page, get the first option
            page = wikipedia.page(e.options[0])
        
        # Get the summary (first 2 sentences)
        summary = wikipedia.summary(page_title, sentences=2)
        
        voice_engine.speak(summary)
        
        return {
            "status": "success",
            "title": page.title,
            "summary": summary,
            "url": page.url
        }
    except Exception as e:
        logger.error(f"Error searching Wikipedia: {e}")
        voice_engine.speak("I encountered an error while searching Wikipedia.")
        return {"status": "error", "error": str(e)}

# --- Joke Telling ---
@command(
    name="tell_joke",
    description="Tell a random joke",
    patterns=["tell me a joke", "make me laugh", "say something funny"]
)
def tell_joke():
    """Tell a random joke."""
    try:
        joke = pyjokes.get_joke()
        voice_engine.speak(joke)
        return {"status": "success", "joke": joke}
    except Exception as e:
        logger.error(f"Error telling joke: {e}")
        voice_engine.speak("Why don't scientists trust atoms? Because they make up everything!")
        return {"status": "error", "error": str(e), "default_joke": True}

# --- Calculator ---
@command(
    name="calculator",
    description="Perform calculations",
    patterns=["calculate *", "what is *", "how much is *"]
)
def calculator(expression: str):
    """Evaluate a mathematical expression and return the result."""
    try:
        # Remove question words and other non-math text
        expression = expression.lower()
        for word in ["calculate", "what is", "how much is", "what's", ""]:
            expression = expression.replace(word, '').strip()
        
        # Replace words with operators
        expression = expression.replace('plus', '+')
        expression = expression.replace('add', '+')
        expression = expression.replace('minus', '-')
        expression = expression.replace('subtract', '-')
        expression = expression.replace('times', '*')
        expression = expression.replace('multiplied by', '*')
        expression = expression.replace('divided by', '/')
        expression = expression.replace('over', '/')
        expression = expression.replace('to the power of', '**')
        expression = expression.replace('squared', '**2')
        expression = expression.replace('cubed', '**3')
        
        # Evaluate the expression safely
        allowed_chars = '0123456789+-*/.()^% '  # Allowed characters
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Invalid characters in expression")
            
        result = eval(expression)
        
        voice_engine.speak(f"The result is {result}")
        return {"status": "success", "expression": expression, "result": result}
    except Exception as e:
        logger.error(f"Error in calculation: {e}")
        voice_engine.speak("I couldn't calculate that. Please try a different expression.")
        return {"status": "error", "error": str(e)}
