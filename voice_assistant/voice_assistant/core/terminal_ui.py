"""Terminal UI module for the voice assistant."""
import os
import sys
import time
import threading
import queue
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime

# ANSI color codes
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

@dataclass
class StatusMessage:
    """Represents a status message with timestamp and type"""
    message: str
    timestamp: float = time.time()
    type: str = 'info'  # info, warning, error, success
    duration: Optional[float] = None  # How long to display the message

class TerminalUI:
    """Handles all terminal output and status updates efficiently"""
    
    def __init__(self):
        self._output_queue = queue.Queue()
        self._status_message: Optional[StatusMessage] = None
        self._status_lock = threading.Lock()
        self._running = False
        self._display_thread: Optional[threading.Thread] = None
        self._last_clear = time.time()
        self._clear_interval = 300  # Clear screen every 5 minutes
        self._command_history: List[str] = []
        self._max_history = 10
        self._wake_words: List[str] = []
        
        # Start the display thread
        self.start()
    
    def start(self):
        """Start the terminal UI display thread"""
        if self._running:
            return
            
        self._running = True
        self._display_thread = threading.Thread(target=self._display_loop, daemon=True)
        self._display_thread.start()
        self.clear()
        self.print_header()
    
    def stop(self):
        """Stop the terminal UI display thread"""
        self._running = False
        if self._display_thread:
            self._display_thread.join(timeout=1.0)
        self._display_thread = None
    
    def _display_loop(self):
        """Main display loop that handles all terminal output"""
        while self._running:
            try:
                # Check if we need to clear the screen
                current_time = time.time()
                if current_time - self._last_clear > self._clear_interval:
                    self.clear()
                    self.print_header()
                    self._last_clear = current_time
                
                # Process any pending output
                try:
                    while True:
                        item = self._output_queue.get_nowait()
                        if isinstance(item, StatusMessage):
                            self._update_status(item)
                        elif isinstance(item, str):
                            print(item)
                        self._output_queue.task_done()
                except queue.Empty:
                    pass
                
                # Display current status
                self._display_status()
                
                # Small sleep to prevent CPU overuse
                time.sleep(0.1)
                
            except Exception as e:
                print(f"\n{Colors.RED}Error in display loop: {e}{Colors.ENDC}")
                time.sleep(1)
    
    def _update_status(self, message: StatusMessage):
        """Update the current status message"""
        with self._status_lock:
            self._status_message = message
    
    def _display_status(self):
        """Display the current status message"""
        with self._status_lock:
            if self._status_message:
                # Check if status message has expired
                if (self._status_message.duration and 
                    time.time() - self._status_message.timestamp > self._status_message.duration):
                    self._status_message = None
                    return
                
                # Format the status message
                color = {
                    'info': Colors.BLUE,
                    'warning': Colors.YELLOW,
                    'error': Colors.RED,
                    'success': Colors.GREEN
                }.get(self._status_message.type, Colors.BLUE)
                
                # Clear the status line and print new status
                sys.stdout.write('\r' + ' ' * 100 + '\r')  # Clear line
                sys.stdout.write(f"{color}[{self._status_message.type.upper()}] {self._status_message.message}{Colors.ENDC}")
                sys.stdout.flush()
    
    def clear(self):
        """Clear the terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
        self._last_clear = time.time()
    
    def print_header(self):
        """Print the application header"""
        header = f"""
{Colors.CYAN}{Colors.BOLD}{'=' * 50}
{'VOICE ASSISTANT'.center(50)}
{'=' * 50}{Colors.ENDC}
"""
        self._output_queue.put(header)
    
    def print_status(self, message: str, msg_type: str = 'info', duration: Optional[float] = None):
        """Print a status message"""
        self._output_queue.put(StatusMessage(
            message=message,
            type=msg_type,
            duration=duration
        ))
    
    def print_command(self, text: str):
        """Print a user command"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self._command_history.append(text)
        if len(self._command_history) > self._max_history:
            self._command_history.pop(0)
        
        output = f"\n{Colors.YELLOW}[{timestamp}] You: {text}{Colors.ENDC}"
        self._output_queue.put(output)
    
    def print_assistant(self, text: str):
        """Print an assistant response"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        output = f"\n{Colors.GREEN}[{timestamp}] Assistant: {text}{Colors.ENDC}"
        self._output_queue.put(output)
    
    def print_error(self, text: str):
        """Print an error message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        output = f"\n{Colors.RED}[{timestamp}] Error: {text}{Colors.ENDC}"
        self._output_queue.put(output)
    
    def print_warning(self, text: str):
        """Print a warning message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        output = f"\n{Colors.YELLOW}[{timestamp}] Warning: {text}{Colors.ENDC}"
        self._output_queue.put(output)
    
    def print_wake_words(self, wake_words: List[str]):
        """Print the available wake words"""
        self._wake_words = wake_words
        words = ", ".join(f'"{w}"' for w in wake_words)
        output = f"\n{Colors.CYAN}Say one of these to activate: {words}{Colors.ENDC}\n"
        self._output_queue.put(output)
    
    def print_command_history(self):
        """Print the command history"""
        if not self._command_history:
            self.print_status("No commands in history", "info")
            return
        
        output = f"\n{Colors.CYAN}Recent Commands:{Colors.ENDC}\n"
        for i, cmd in enumerate(self._command_history, 1):
            output += f"{i}. {cmd}\n"
        self._output_queue.put(output)
    
    def print_help(self):
        """Print help information"""
        help_text = f"""
{Colors.CYAN}Voice Assistant Help{Colors.ENDC}
-------------------
Commands:
  - Say a wake word ({", ".join(f'"{w}"' for w in self._wake_words)}) to activate
  - Speak your command clearly
  - Say "help" for this message
  - Say "history" to see recent commands
  - Say "clear" to clear the screen
  - Say "exit" to quit

Tips:
  - Speak clearly and at a normal pace
  - Wait for the assistant to respond before speaking again
  - Keep background noise to a minimum
  - Make sure your microphone is properly connected
"""
        self._output_queue.put(help_text)

# Create a singleton instance
terminal_ui = TerminalUI() 