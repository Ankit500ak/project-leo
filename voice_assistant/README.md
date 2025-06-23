# 🎙️ Zero - Voice Assistant

A powerful, extensible voice assistant built with Python that can understand and execute voice commands to control your computer, automate tasks, and provide entertainment. Zero is designed to be your personal AI assistant, helping with everything from system control to answering questions and playing games.

## ✨ Features

- 🎙️ **Voice Control**
  - Natural language voice commands
  - Customizable wake word
  - Background listening mode

- 💻 **System Control**
  - Manage applications (open/close)
  - Control system volume
  - Get system information
  - Shutdown/restart computer (admin only)

- 🔍 **Web & Search**
  - Web search
  - Wikipedia lookups
  - YouTube video search and playback

- 🎮 **Entertainment**
  - Tell jokes and fun facts
  - Play interactive games
  - Tell stories
  - Magic 8-ball
  - Roll dice and flip coins

- 🛠️ **Productivity**
  - Manage clipboard
  - Create desktop shortcuts
  - Get weather information
  - Set alarms
  - Perform calculations

## 🚀 Getting Started

### 1. First Steps

1. **Install Dependencies**
   ```bash
   # Install required packages
   pip install -r requirements.txt
   
   # Install optional packages for full functionality
   pip install wikipedia pyjokes pyperclip
   ```

2. **Configure Settings**
   Create a `config.ini` file in the project root:
   ```ini
   [voice]
   wake_word = zero
   language = en-US
   volume = 1.0
   rate = 200

   [features]
   wikipedia = true
   weather = true
   games = true
   ```

### 2. Activation Methods

#### Method 1: Wake Word
- Default wake word: "Hey Zero"
- Alternative wake words: "Computer", "Assistant"
- Example: "Hey Zero, what time is it?"

#### Method 2: Hotkey
- Press `Ctrl + Space` to activate
- No wake word needed
- Example: Press `Ctrl + Space`, then say "What time is it?"

### 3. Detailed Command Examples

#### Time & Date
- "What time is it?"
- "What's the current time?"
- "Tell me the time please"
- "What's today's date?"
- "What day is it today?"

#### System Control
- "Open Chrome" (or any application)
- "Close Chrome" (or any application)
- "Volume up"
- "Volume down"
- "Mute"
- "Unmute"
- "System info"
- "System details"

#### Web & Search
- "Search for Python programming"
- "Wikipedia search for AI"
- "Play happy songs on YouTube"
- "Open Google"
- "Open Facebook"

#### Entertainment
- "Tell me a joke"
- "Tell me another joke"
- "Tell me a fun fact"
- "Would you rather?"
- "Tell me a story"
- "Flip a coin"
- "Roll a die"
- "Roll a d20"
- "Magic 8 ball should I go to the gym today?"

#### Games
- "Play rock paper scissors"
- "Play number guessing game"
- "Play trivia"
- "Play a game"

#### Productivity
- "Copy this text to clipboard"
- "Read clipboard contents"
- "Create shortcut for Chrome"
- "Set an alarm for 10 minutes"
- "Calculate 2 plus 2"

#### Help & Information
- "Help"
- "What can you do?"
- "Show all commands"
- "How do I use you?"

### 4. Command Variations

Zero understands natural language variations. For example:
- "What time is it?" = "Could you tell me the time?" = "Time please"
- "Open Chrome" = "Launch Chrome" = "Start Chrome"
- "Search for cats" = "Look up cats" = "Find information about cats"

### 5. Special Features

#### Voice Feedback
- Zero will speak responses when appropriate
- Volume and speed can be adjusted in config.ini
- Multiple voice options available

#### Error Handling
- If a command isn't recognized, Zero will ask for clarification
- If an action fails, Zero will explain why
- Detailed logs are available in the logs directory

#### Security Features
- Admin commands require confirmation
- Sensitive actions are logged
- Wake word can be customized for privacy

### 6. Troubleshooting Tips

1. **Voice Recognition Issues**
   - Speak clearly and at a moderate pace
   - Reduce background noise
   - Check microphone settings
   - Try running as administrator (Windows)

2. **Command Not Working**
   - Verify the feature is enabled in config.ini
   - Check if required dependencies are installed
   - Run with `--debug` flag to see detailed logs

3. **Volume Problems**
   - Adjust volume in config.ini
   - Check system volume settings
   - Try different voice profiles

### 7. Advanced Usage

#### Custom Wake Words
```bash
# Change wake word
python main.py --wake-word "computer"

# Run without wake word (always listening)
python main.py --no-wake-word
```

#### Debug Mode
```bash
# Run with detailed logging
python main.py --debug

# View logs in real-time
tail -f logs/voice_assistant.log
```

#### Configuration Options
```ini
[voice]
# Wake word settings
wake_word = zero
sensitivity = 0.5

[features]
# Enable/disable features
wikipedia = true
weather = true
games = true

[performance]
# Performance settings
max_threads = 4
memory_limit = 2048
```

#### Hotkeys
- `Ctrl + Space`: Activate voice assistant
- `Ctrl + Shift + S`: Toggle speech recognition
- `Ctrl + Shift + V`: Show visual feedback
- `Ctrl + Shift + L`: Show logs window

### 8. Command Categories

#### System Commands
- **Time & Date**
  - Get current time and date
  - Set alarms and reminders
  - Manage system clock

- **Application Control**
  - Open/close applications
  - Switch between windows
  - Manage application states

- **System Settings**
  - Adjust volume
  - Control display
  - Manage system resources

#### Web & Search
- **Web Browsing**
  - Open websites
  - Search web
  - Navigate browser

- **YouTube**
  - Search videos
  - Play music
  - Control playback

- **Wikipedia**
  - Look up information
  - Read articles
  - Get summaries

#### Entertainment
- **Games**
  - Rock Paper Scissors
  - Number Guessing
  - Trivia
  - Would You Rather

- **Fun Features**
  - Jokes
  - Stories
  - Facts
  - Magic 8 Ball

- **Random Activities**
  - Coin flips
  - Dice rolls
  - Random choices

#### Productivity
- **Clipboard Management**
  - Copy/paste
  - History
  - Formatting

- **Shortcuts**
  - Create desktop shortcuts
  - Manage links
  - Quick access

- **Calculations**
  - Basic math
  - Conversions
  - Formulas

#### Help & Support
- **Command Reference**
  - List all commands
  - Show examples
  - Explain usage

- **Troubleshooting**
  - Common issues
  - Solutions
  - Support resources

- **Settings**
  - Configuration
  - Customization
  - Updates

### 9. Best Practices

1. **Speak Clearly**
   - Use clear, simple language
   - Speak at a moderate pace
   - Avoid background noise

2. **Use Natural Language**
   - Ask questions naturally
   - Use complete sentences
   - Be specific in requests

3. **Be Patient**
   - Give Zero time to process
   - Wait for confirmation
   - Try again if needed

4. **Check Logs**
   - Review logs for errors
   - Track command history
   - Monitor performance

5. **Customize Settings**
   - Adjust voice settings
   - Modify wake word
   - Enable/disable features

### 10. Support & Resources

- **Documentation**: [Read the Docs](https://docs.example.com/voice-assistant)
- **Support**: [Open an Issue](https://github.com/yourusername/voice-assistant/issues)
- **Community**: [Discord](https://discord.gg/your-invite-link)
- **Contributing**: [GitHub Repository](https://github.com/yourusername/voice-assistant)

#### Troubleshooting Checklist

1. **Microphone Issues**
   - Check microphone connection
   - Test microphone settings
   - Verify permissions

2. **Command Recognition**
   - Check wake word
   - Verify command patterns
   - Review logs

3. **Performance Issues**
   - Check system resources
   - Review configuration
   - Monitor logs

4. **Security Concerns**
   - Verify permissions
   - Check logs
   - Review settings

#### Additional Tips

1. **Voice Recognition**
   - Speak clearly
   - Use natural language
   - Be specific

2. **Command Structure**
   - Start with wake word
   - Be specific
   - Use natural language

3. **Error Handling**
   - Check logs
   - Verify dependencies
   - Try again

4. **Performance Optimization**
   - Adjust settings
   - Monitor resources
   - Update regularly

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/voice-assistant.git
   cd voice-assistant
   ```

2. **Set up a virtual environment** (recommended):
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the assistant**:
   ```bash
   python main.py
   ```

## 📋 Complete Command Reference

### System Commands
- **`what time is it`** - Get current time
- **`what's today's date`** - Get current date
- **`system info`** - Show basic system information
- **`system details`** - Show detailed system specifications
- **`shutdown`** - Shut down the computer (admin only)
- **`restart`** - Restart the computer (admin only)
- **`mute`/`unmute`** - Toggle system mute
- **`volume up`/`volume down`** - Adjust system volume

### Web & Search
- **`search for *`** - Search the web
- **`search wikipedia for *`** - Search Wikipedia
- **`play * on youtube`** - Search and play YouTube videos
- **`open website *`** - Open a specific website

### Entertainment
- **`tell me a joke`** - Tell a random joke
- **`tell me a fun fact`** - Share an interesting fact
- **`would you rather`** - Ask a "would you rather" question
- **`tell me a story`** - Tell a short story
- **`flip a coin`** - Flip a virtual coin
- **`roll a die`** - Roll a six-sided die
- **`roll a d20`** - Roll a twenty-sided die
- **`magic 8 ball *`** - Ask the magic 8-ball a question

### Games
- **`play a game`** - Start an interactive game
- **`play rock paper scissors`** - Play Rock, Paper, Scissors
- **`play number guessing`** - Play a number guessing game
- **`play trivia`** - Answer trivia questions

### Productivity
- **`open *`** - Open an application
- **`close *`** - Close an application
- **`copy * to clipboard`** - Copy text to clipboard
- **`read clipboard`** - Read clipboard contents
- **`create shortcut for *`** - Create a desktop shortcut
- **`set an alarm for *`** - Set an alarm
- **`calculate *`** - Perform calculations

### Help
- **`help`** - Show all available commands
- **`what can you do`** - List available features

## 🛠️ Advanced Usage

### Configuration

Customize Zero's behavior by creating or editing the `config.ini` file in the project root:

```ini
[voice]
wake_word = zero  # Change the wake word
language = en-US   # Set the recognition language
volume = 1.0       # Voice volume (0.0 to 1.0)
rate = 200        # Speech rate (words per minute)

[features]
wikipedia = true
weather = true
games = true

[api_keys]
# Add your API keys here
openweather_api = your_api_key
```

### Running Modes

```bash
# Start with GUI (default)
python main.py

# Console-only mode
python main.py --no-gui

# Debug mode (shows detailed logs)
python main.py --debug

# Change wake word
python main.py --wake-word "computer"

# Run without wake word (always listening)
python main.py --no-wake-word
```

### Voice Command Patterns

Zero understands natural language variations. For example, all these will work:
- "What's the time?"
- "Could you tell me the current time?"
- "Time please"

## 🐛 Troubleshooting

### Common Issues

1. **Microphone not detected**
   - Ensure your microphone is properly connected
   - Check system sound settings
   - Try running as administrator (Windows)

2. **Voice recognition issues**
   - Speak clearly and at a moderate pace
   - Reduce background noise
   - Check your internet connection (required for speech recognition)

3. **Command not recognized**
   - Try rephrasing your request
   - Check if the feature is enabled in config.ini
   - Run with `--debug` flag to see detailed logs

### Logs

Logs are stored in `logs/` directory. Check these files if you encounter issues:
- `voice_assistant.log` - Main application logs
- `voice_engine.log` - Voice recognition logs
- `commands.log` - Command execution history

## 🏗️ Project Structure

```
voice_assistant/
├── core/                   # Core functionality
│   ├── __init__.py
│   ├── voice_engine.py      # Voice recognition and synthesis
│   ├── command_processor.py # Command processing logic
│   ├── builtin_commands.py  # Built-in voice commands
│   ├── extended_commands.py # Extended functionality
│   ├── entertainment_commands.py # Games and fun
│   └── utility_commands.py  # System utilities
├── data/                   # Application data
│   ├── sounds/             # Sound effects
│   └── voices/             # Voice profiles
├── logs/                   # Log files
├── plugins/                # Custom plugins (optional)
├── config.ini             # Configuration file
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Report Issues**
   - Check existing issues first
   - Include steps to reproduce the problem
   - Add relevant logs and system information

2. **Suggest Features**
   - Open an issue with the "enhancement" label
   - Explain the use case and benefits

3. **Code Contributions**
   - Fork the repository
   - Create a feature branch (`git checkout -b feature/amazing-feature`)
   - Commit your changes (`git commit -m 'Add some amazing feature'`)
   - Push to the branch (`git push origin feature/amazing-feature`)
   - Open a Pull Request

### Development Setup

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. Run tests:
   ```bash
   pytest tests/
   ```

3. Format code:
   ```bash
   black .
   isort .
   ```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

- [SpeechRecognition](https://pypi.org/project/SpeechRecognition/) - For voice recognition
- [pyttsx3](https://pypi.org/project/pyttsx3/) - For text-to-speech
- [psutil](https://psutil.readthedocs.io/) - For system monitoring
- [pyjokes](https://pyjok.es/) - For the jokes database
- And all the amazing open-source projects that made this possible!

## 📞 Support

For support, please [open an issue](https://github.com/yourusername/voice-assistant/issues) or join our [Discord community](https://discord.gg/your-invite-link).
