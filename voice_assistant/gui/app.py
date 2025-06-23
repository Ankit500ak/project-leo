"""Main GUI application for the Voice Assistant"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
from typing import Optional, Callable, Any
from pathlib import Path

class VoiceAssistantGUI:
    """Main GUI application for the Voice Assistant"""
    
    def __init__(self, voice_engine, command_processor):
        """Initialize the GUI"""
        self.voice_engine = voice_engine
        self.command_processor = command_processor
        self.root = tk.Tk()
        self.root.title("Voice Assistant")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configure styles
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self._setup_styles()
        
        # Status variables
        self.is_listening = False
        self.message_queue = queue.Queue()
        
        # Initialize UI
        self._setup_ui()
        
        # Start the message pump
        self.root.after(100, self._process_messages)
        
        # Register callbacks
        self.voice_engine.register_callback(self._on_voice_command)
        
    def _setup_styles(self):
        """Configure custom styles"""
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TButton', padding=6)
        self.style.configure('TNotebook', background='#f0f0f0')
        self.style.configure('TNotebook.Tab', padding=[10, 5])
        
        # Custom styles
        self.style.configure('Listen.TButton',
                           foreground='white',
                           background='#e74c3c',
                           font=('Helvetica', 12, 'bold'))
        
        self.style.map('Listen.TButton',
                      background=[('active', '#c0392b')])
    
    def _setup_ui(self):
        """Set up the user interface"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title
        title_label = ttk.Label(
            header_frame,
            text="Voice Assistant",
            font=('Helvetica', 18, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        # Status indicator
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(
            header_frame,
            textvariable=self.status_var,
            foreground='#666666'
        )
        status_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Console tab
        self._setup_console_tab()
        
        # Commands tab
        self._setup_commands_tab()
        
        # Settings tab
        self._setup_settings_tab()
        
        # Footer with controls
        footer_frame = ttk.Frame(main_frame)
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Listen button
        self.listen_btn = ttk.Button(
            footer_frame,
            text="🎤 Start Listening",
            command=self._toggle_listening,
            style='Listen.TButton',
            width=20
        )
        self.listen_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Command entry
        self.command_var = tk.StringVar()
        command_entry = ttk.Entry(
            footer_frame,
            textvariable=self.command_var,
            font=('Helvetica', 12)
        )
        command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        command_entry.bind('<Return>', self._on_send_command)
        
        # Send button
        send_btn = ttk.Button(
            footer_frame,
            text="Send",
            command=self._on_send_command,
            width=10
        )
        send_btn.pack(side=tk.RIGHT)
    
    def _setup_console_tab(self):
        """Set up the console tab"""
        console_frame = ttk.Frame(self.notebook)
        self.notebook.add(console_frame, text="Console")
        
        # Console output
        self.console = scrolledtext.ScrolledText(
            console_frame,
            wrap=tk.WORD,
            font=('Consolas', 10),
            bg='#1e1e1e',
            fg='#e0e0e0',
            insertbackground='#ffffff',
            selectbackground='#264f78',
            insertwidth=2,
            padx=10,
            pady=10
        )
        self.console.pack(fill=tk.BOTH, expand=True)
        
        # Add welcome message
        self._log_message("Voice Assistant initialized. Ready to receive commands.", "info")
    
    def _setup_commands_tab(self):
        """Set up the commands tab"""
        commands_frame = ttk.Frame(self.notebook)
        self.notebook.add(commands_frame, text="Commands")
        
        # Search bar
        search_frame = ttk.Frame(commands_frame)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        search_label = ttk.Label(search_frame, text="Search:")
        search_label.pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        search_entry.bind('<KeyRelease>', self._filter_commands)
        
        # Commands list
        self.commands_tree = ttk.Treeview(
            commands_frame,
            columns=('description', 'patterns'),
            show='headings',
            selectmode='browse'
        )
        
        # Configure columns
        self.commands_tree.heading('description', text='Command')
        self.commands_tree.heading('patterns', text='Patterns')
        
        self.commands_tree.column('description', width=200)
        self.commands_tree.column('patterns', width=400, stretch=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(
            commands_frame,
            orient=tk.VERTICAL,
            command=self.commands_tree.yview
        )
        self.commands_tree.configure(yscroll=scrollbar.set)
        
        # Pack widgets
        self.commands_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Populate commands
        self._populate_commands()
    
    def _setup_settings_tab(self):
        """Set up the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Settings notebook
        settings_notebook = ttk.Notebook(settings_frame)
        settings_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Voice settings
        voice_frame = ttk.Frame(settings_notebook, padding=10)
        settings_notebook.add(voice_frame, text="Voice")
        
        # Voice selection
        ttk.Label(voice_frame, text="Voice:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.voice_var = tk.StringVar(value="female")
        ttk.Radiobutton(voice_frame, text="Female", variable=self.voice_var, value="female").grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Radiobutton(voice_frame, text="Male", variable=self.voice_var, value="male").grid(row=0, column=2, sticky=tk.W, padx=5)
        
        # Voice rate
        ttk.Label(voice_frame, text="Speech Rate:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.rate_var = tk.IntVar(value=170)
        ttk.Scale(
            voice_frame,
            from_=100,
            to=300,
            orient=tk.HORIZONTAL,
            variable=self.rate_var,
            command=lambda v: self._on_voice_setting_changed('rate', int(float(v))))
        ttk.Label(voice_frame, textvariable=self.rate_var).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        # Voice volume
        ttk.Label(voice_frame, text="Volume:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.volume_var = tk.DoubleVar(value=0.9)
        ttk.Scale(
            voice_frame,
            from_=0.0,
            to=1.0,
            orient=tk.HORIZONTAL,
            variable=self.volume_var,
            command=lambda v: self._on_voice_setting_changed('volume', float(v)))
        ttk.Label(voice_frame, textvariable=self.volume_var).grid(row=2, column=2, sticky=tk.W, padx=5)
        
        # Hotkeys settings
        hotkeys_frame = ttk.Frame(settings_notebook, padding=10)
        settings_notebook.add(hotkeys_frame, text="Hotkeys")
        
        # Add hotkey configuration here
        ttk.Label(hotkeys_frame, text="Push-to-Talk Hotkey:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.hotkey_var = tk.StringVar(value="Ctrl+Space")
        hotkey_entry = ttk.Entry(hotkeys_frame, textvariable=self.hotkey_var, width=15)
        hotkey_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Save button
        save_btn = ttk.Button(
            settings_frame,
            text="Save Settings",
            command=self._save_settings,
            style='Accent.TButton'
        )
        save_btn.pack(pady=10)
    
    def _populate_commands(self):
        """Populate the commands list"""
        # Clear existing items
        for item in self.commands_tree.get_children():
            self.commands_tree.delete(item)
        
        # Get commands from processor
        commands = self.command_processor.list_commands()
        
        # Group by category
        categories = {}
        for cmd in commands:
            category = cmd['name'].split('_')[0].title()
            if category not in categories:
                categories[category] = []
            categories[category].append(cmd)
        
        # Add to tree
        for category, cmds in categories.items():
            parent = self.commands_tree.insert('', 'end', text=category, values=(f"{category} Commands", ""))
            for cmd in sorted(cmds, key=lambda x: x['name']):
                patterns = ", ".join(f'"{p}"' for p in cmd['patterns'][:2])
                if len(cmd['patterns']) > 2:
                    patterns += f", ..."
                self.commands_tree.insert(
                    parent, 'end',
                    values=(cmd['name'], patterns, cmd['description'])
                )
    
    def _filter_commands(self, event=None):
        """Filter commands based on search text"""
        search_text = self.search_var.get().lower()
        
        for item in self.commands_tree.get_children():
            # Skip category items
            if not self.commands_tree.parent(item):
                continue
                
            # Get command name and description
            values = self.commands_tree.item(item, 'values')
            if not values:
                continue
                
            # Check if search text matches
            cmd_name = values[0].lower()
            cmd_desc = values[2].lower() if len(values) > 2 else ""
            
            if (search_text in cmd_name or search_text in cmd_desc):
                self.commands_tree.item(item, open=True)  # Expand parent
                self.commands_tree.see(item)
                self.commands_tree.selection_set(item)
                break
    
    def _toggle_listening(self):
        """Toggle voice listening"""
        if self.is_listening:
            self.voice_engine.stop_continuous_listening()
            self.is_listening = False
            self.listen_btn.config(text="🎤 Start Listening")
            self.status_var.set("Ready")
        else:
            self.voice_engine.start_continuous_listening()
            self.is_listening = True
            self.listen_btn.config(text="🛑 Stop Listening")
            self.status_var.set("Listening...")
            self._log_message("Listening for voice commands...", "info")
    
    def _on_send_command(self, event=None):
        """Handle send command button press"""
        command = self.command_var.get().strip()
        if not command:
            return
            
        self._log_message(f"You: {command}", "user")
        self.command_var.set("")
        
        # Process the command
        from core.voice_engine import VoiceCommand
        cmd = VoiceCommand(
            text=command,
            confidence=1.0,
            is_wake_word=any(w in command.lower() for w in self.voice_engine.WAKE_WORDS)
        )
        self.command_processor.process_voice_command(cmd)
    
    def _on_voice_command(self, command):
        """Handle voice command from engine"""
        self.message_queue.put(('command', command))
    
    def _on_voice_setting_changed(self, setting, value):
        """Handle voice setting changes"""
        if setting == 'rate':
            self.voice_engine.engine.setProperty('rate', value)
        elif setting == 'volume':
            self.voice_engine.engine.setProperty('volume', value)
    
    def _save_settings(self):
        """Save application settings"""
        # TODO: Implement settings persistence
        messagebox.showinfo("Settings", "Settings saved successfully!")
    
    def _log_message(self, message, msg_type='info'):
        """Add a message to the console"""
        self.message_queue.put(('log', message, msg_type))
    
    def _process_messages(self):
        """Process messages from the queue"""
        try:
            while True:
                try:
                    msg = self.message_queue.get_nowait()
                    msg_type = msg[0]
                    
                    if msg_type == 'log':
                        message, msg_type = msg[1], msg[2]
                        self._write_to_console(message, msg_type)
                    elif msg_type == 'command':
                        command = msg[1]
                        self._write_to_console(f"Heard: {command.text}", "command")
                    
                except queue.Empty:
                    break
        except Exception as e:
            print(f"Error processing messages: {e}")
        
        # Schedule next check
        self.root.after(100, self._process_messages)
    
    def _write_to_console(self, message, msg_type='info'):
        """Write a message to the console"""
        # Configure tags for different message types
        if not hasattr(self, 'console_tags_configured'):
            self.console.tag_configure('info', foreground='#ffffff')
            self.console.tag_configure('error', foreground='#ff6b6b')
            self.console.tag_configure('warning', foreground='#feca57')
            self.console.tag_configure('success', foreground='#1dd1a1')
            self.console.tag_configure('command', foreground='#54a0ff')
            self.console.tag_configure('user', foreground='#5f27cd')
            self.console_tags_configured = True
        
        # Add timestamp
        timestamp = time.strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{timestamp}] ", 'info')
        
        # Add message with appropriate tag
        self.console.insert(tk.END, message + "\n", msg_type)
        
        # Auto-scroll to bottom
        self.console.see(tk.END)
    
    def run(self):
        """Run the main application loop"""
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.mainloop()
    
    def _on_close(self):
        """Handle window close event"""
        if messagebox.askokcancel("Quit", "Are you sure you want to quit?"):
            self.voice_engine.stop_continuous_listening()
            self.root.destroy()


if __name__ == "__main__":
    # For testing the GUI standalone
    from core.voice_engine import VoiceEngine
    from core.command_processor import CommandProcessor
    
    voice_engine = VoiceEngine()
    command_processor = CommandProcessor()
    
    app = VoiceAssistantGUI(voice_engine, command_processor)
    app.run()
