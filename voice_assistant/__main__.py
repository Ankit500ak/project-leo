#!/usr/bin/env python3
"""
Voice Assistant - A powerful voice-controlled assistant

Usage:
    python -m voice_assistant [options]

Options:
    --debug    Enable debug mode
    --no-gui   Run without GUI
"""
import os
import sys
import logging
import argparse
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent.absolute()))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('voice_assistant.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Voice Assistant')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--no-gui', action='store_true', help='Run without GUI')
    args = parser.parse_args()
    
    # Set log level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info("Starting Voice Assistant...")
    
    try:
        # Import core components
        from core.voice_engine import voice_engine
        from core.command_processor import command_processor
        
        # Import GUI if not disabled
        if not args.no_gui:
            try:
                from gui.app import VoiceAssistantGUI
                gui = VoiceAssistantGUI(voice_engine, command_processor)
                gui.run()
            except ImportError as e:
                logger.warning(f"GUI not available: {e}. Running in console mode.")
                run_console_mode(voice_engine, command_processor)
        else:
            run_console_mode(voice_engine, command_processor)
            
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        print(f"A critical error occurred: {e}")
        sys.exit(1)

def run_console_mode(voice_engine, command_processor):
    """Run the assistant in console mode"""
    print("Voice Assistant - Console Mode")
    print("Type 'exit' or press Ctrl+C to quit")
    print("Listening for commands...")
    
    # Start listening for voice commands
    voice_engine.start_continuous_listening()
    
    try:
        while True:
            # Process any voice commands
            commands = voice_engine.process_command_queue()
            for cmd in commands:
                command_processor.process_voice_command(cmd)
            
            # Check for console input
            try:
                user_input = input("\nYou: ")
                if user_input.lower() in ('exit', 'quit'):
                    break
                    
                # Process text command
                from core.voice_engine import VoiceCommand
                cmd = VoiceCommand(
                    text=user_input,
                    confidence=1.0,
                    is_wake_word=any(w in user_input.lower() for w in voice_engine.WAKE_WORDS)
                )
                command_processor.process_voice_command(cmd)
                
            except (KeyboardInterrupt, EOFError):
                break
            except Exception as e:
                logger.error(f"Error processing input: {e}", exc_info=True)
                
    except KeyboardInterrupt:
        pass
    finally:
        voice_engine.stop_continuous_listening()
        print("\nGoodbye!")

if __name__ == "__main__":
    main()
