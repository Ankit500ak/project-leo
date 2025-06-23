import os
import queue
import threading
import time
import logging
import re
import speech_recognition as sr
import pyttsx3
import pyaudio
import numpy as np
from dataclasses import dataclass
from typing import Optional, Callable, List, Dict, Any

from voice_assistant.core.terminal_ui import terminal_ui
from voice_assistant.config import config
from voice_assistant.core.registry import register_voice_engine, get_nlu_engine
from voice_assistant.core.nlu import Intent

# Configure root logger to only show errors
logging.basicConfig(level=logging.ERROR)

# Create a custom logger for our application
logger = logging.getLogger('voice_assistant')
logger.setLevel(logging.INFO)

# Create file handler for debug logs
file_handler = logging.FileHandler('voice_assistant.log')
file_handler.setLevel(logging.DEBUG)
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)

# Suppress all console output except our custom UI
logging.getLogger().addHandler(logging.NullHandler())
logging.captureWarnings(True)

# Suppress unnecessary library logs
for lib in ['comtypes', 'speech_recognition', 'urllib3', 'PIL', 'numpy', 'requests']:
    logging.getLogger(lib).setLevel(logging.ERROR)

@dataclass
class VoiceCommand:
    """Represents a recognized voice command with NLU information"""
    text: str
    confidence: float
    intent: Optional[Intent] = None
    is_wake_word: bool = False
    speaker_id: Optional[str] = None
    timestamp: float = time.time()

class VoiceEngine:
    """Handles all voice-related functionality including wake word detection and speech recognition"""
    
    def __init__(self):
        """Initialize the voice engine"""
        self.recognizer = sr.Recognizer()
        # Set more sensitive values for better voice recognition
        self.recognizer.energy_threshold = 400  # Reduced from 1000 for better sensitivity
        self.recognizer.pause_threshold = 0.8    # Increased for better phrase detection
        self.recognizer.phrase_threshold = 0.3   # Keep this the same
        self.recognizer.non_speaking_duration = 0.5  # Increased for better phrase completion
        self.recognizer.dynamic_energy_threshold = True  # Keep dynamic adjustment
        self.recognizer.dynamic_energy_adjustment_damping = 0.2  # Increased damping for stability
        self.recognizer.dynamic_energy_ratio = 1.2  # Reduced ratio for better sensitivity
        
        # Initialize other attributes
        self.engine = pyttsx3.init()
        self.command_queue = queue.Queue()
        self.is_listening = False
        self.callbacks = []
        self._stop_listening = threading.Event()
        self._listening_thread = None
        self._last_noise_adjustment = 0
        self._mic_setup_complete = False
        self._min_energy_threshold = 300  # Minimum threshold
        self._max_energy_threshold = 800  # Maximum threshold
        
        # Setup voice engine first
        self._setup_voice_engine()
        
        # Try to get microphone, but don't fail if it doesn't work immediately
        try:
            self.microphone = self._get_best_microphone()
            self._mic_setup_complete = True
        except Exception as e:
            logger.error(f"Initial microphone setup failed: {e}")
            terminal_ui.print_error(f"Microphone setup failed: {e}")
            self.microphone = None
        
        # Register this instance with the registry
        register_voice_engine(self)
        
        # Print wake words
        terminal_ui.print_wake_words(config.voice.WAKE_WORDS)
    
    def _get_best_microphone(self):
        """Try to find the best available microphone"""
        try:
            # Get list of available microphones first
            mic_list = sr.Microphone.list_microphone_names()
            logger.debug(f"Available microphones: {mic_list}")
            terminal_ui.print_status("Searching for microphones...", "info")
            
            # First try default microphone (index 0)
            try:
                mic = sr.Microphone(device_index=0)
                # Test microphone without ambient noise adjustment
                test_audio = None
                with mic as source:
                    test_audio = self.recognizer.listen(
                        source,
                        timeout=1.0,
                        phrase_time_limit=1.0
                    )
                
                if test_audio:
                    terminal_ui.print_status("Default microphone test successful", "success")
                    # Do ambient noise adjustment in a separate context
                    with mic as source:
                        self.recognizer.adjust_for_ambient_noise(source, duration=1)
                        terminal_ui.print_status(f"Energy threshold set to: {self.recognizer.energy_threshold}", "info")
                    return mic
            except Exception as e:
                logger.debug(f"Default microphone failed: {e}")
                terminal_ui.print_warning("Default microphone failed, trying alternatives...")
            
            # If default fails, try all available microphones
            for mic_name in mic_list:
                try:
                    device_index = mic_list.index(mic_name)
                    mic = sr.Microphone(device_index=device_index)
                    terminal_ui.print_status(f"Trying microphone: {mic_name}", "info")
                    
                    # Test microphone without ambient noise adjustment
                    test_audio = None
                    with mic as source:
                        test_audio = self.recognizer.listen(
                            source,
                            timeout=1.0,
                            phrase_time_limit=1.0
                        )
                    
                    if test_audio:
                        terminal_ui.print_status(f"Microphone {mic_name} test successful", "success")
                        # Do ambient noise adjustment in a separate context
                        with mic as source:
                            self.recognizer.adjust_for_ambient_noise(source, duration=1)
                            terminal_ui.print_status(f"Energy threshold set to: {self.recognizer.energy_threshold}", "info")
                        return mic
                except Exception as e:
                    logger.warning(f"Microphone {mic_name} failed: {e}")
                    continue
            
            # If no microphone works, raise an error
            raise RuntimeError("No working microphone found")
                
        except Exception as e:
            logger.error(f"Error in microphone initialization: {e}")
            terminal_ui.print_error(f"Failed to initialize microphone: {e}")
            raise RuntimeError(f"Failed to initialize microphone: {e}")
    
    def _setup_voice_engine(self):
        """Configure the text-to-speech engine"""
        voices = self.engine.getProperty('voices')
        if 0 <= config.voice.VOICE_ID < len(voices):
            self.engine.setProperty('voice', voices[config.voice.VOICE_ID].id)
        self.engine.setProperty('rate', config.voice.VOICE_RATE)
        self.engine.setProperty('volume', config.voice.VOICE_VOLUME)
    
    def _setup_microphone(self):
        """Configure the microphone with fixed settings"""
        if not self.microphone:
            raise RuntimeError("No microphone available for setup")
            
        if self._mic_setup_complete:
            return
            
        try:
            # Set more sensitive values for better voice recognition
            self.recognizer.energy_threshold = 400  # Reduced from 1000
            self.recognizer.pause_threshold = 0.8    # Increased for better phrase detection
            self.recognizer.phrase_threshold = 0.3
            self.recognizer.non_speaking_duration = 0.5  # Increased for better phrase completion
            self.recognizer.dynamic_energy_threshold = True
            self.recognizer.dynamic_energy_adjustment_damping = 0.2
            self.recognizer.dynamic_energy_ratio = 1.2
            
            # Test microphone without ambient noise adjustment
            terminal_ui.print_status("Testing microphone...", "info")
            test_audio = None
            with self.microphone as source:
                test_audio = self.recognizer.listen(
                    source,
                    timeout=1.0,
                    phrase_time_limit=1.0
                )
            
            if test_audio:
                terminal_ui.print_status("Microphone test successful", "success")
                # Do ambient noise adjustment in a separate context
                with self.microphone as source:
                    self.recognizer.adjust_for_ambient_noise(source, duration=2)
                    # Ensure energy threshold is within bounds
                    self.recognizer.energy_threshold = max(
                        min(self.recognizer.energy_threshold, self._max_energy_threshold),
                        self._min_energy_threshold
                    )
                    terminal_ui.print_status(f"Microphone setup complete. Energy threshold: {self.recognizer.energy_threshold}", "info")
                self._mic_setup_complete = True
            else:
                terminal_ui.print_warning("Microphone test: No audio detected")
                    
        except Exception as e:
            logger.error(f"Error setting up microphone: {e}")
            terminal_ui.print_error(f"Error setting up microphone: {e}")
            terminal_ui.print_warning("Continuing with default microphone settings")
    
    def speak(self, text: str, wait: bool = True):
        """Convert text to speech"""
        def _speak():
            try:
                terminal_ui.print_assistant(text)
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception as e:
                logger.error(f"Error in text-to-speech: {e}")
                terminal_ui.print_error(f"Speech error: {e}")
        
        if wait:
            _speak()
        else:
            threading.Thread(target=_speak, daemon=True).start()
    
    def listen(self, timeout: Optional[float] = 3.0, phrase_time_limit: float = 5.0) -> Optional[VoiceCommand]:
        """Listen for a voice command
        
        Args:
            timeout: Maximum time to wait for speech (None for no timeout)
            phrase_time_limit: Maximum time for a single phrase
            
        Returns:
            VoiceCommand if speech was recognized, None otherwise
        """
        if not self.microphone:
            logger.error("No microphone available for listening")
            return None
            
        try:
            with self.microphone as source:
                logger.debug("Listening...")
                try:
                    # Listen for audio input with adjusted parameters
                    audio = self.recognizer.listen(
                        source,
                        timeout=timeout,
                        phrase_time_limit=phrase_time_limit
                    )
                    
                    if audio:
                        logger.debug("Audio captured, processing...")
                        # Process the audio data
                        audio_data = audio.get_wav_data(
                            convert_rate=16000,  # Standard sample rate for speech recognition
                            convert_width=2      # 16-bit audio
                        )
                        
                        if audio_data:
                            command = self.process_speech(audio_data)
                            
                            if command and hasattr(command, 'text') and command.text:
                                # Check for wake words with better matching
                                command_text = command.text.lower().strip()
                                is_wake_word = any(
                                    re.search(rf'\b{re.escape(wake_word)}\b', command_text)
                                    for wake_word in config.voice.WAKE_WORDS
                                )
                                command.is_wake_word = is_wake_word
                                
                                if is_wake_word:
                                    logger.info(f"Wake word detected in: {command_text}")
                                
                                # Notify callbacks
                                for callback in self.callbacks:
                                    try:
                                        callback(command)
                                    except Exception as e:
                                        logger.error(f"Error in callback: {e}")
                                
                                return command
                            
                            logger.debug("No valid command processed from audio")
                            return None
                        
                        logger.warning("No audio data in captured audio")
                        return None
                    
                    logger.debug("No audio captured")
                    return None
                    
                except sr.WaitTimeoutError:
                    logger.debug("Listening timed out")
                    return None
                    
                except sr.UnknownValueError:
                    logger.debug("Speech recognition could not understand audio")
                    return None
                    
                except sr.RequestError as e:
                    logger.error(f"Speech recognition service error: {e}")
                    return None
                    
                except Exception as e:
                    logger.error(f"Unexpected error in listen: {e}", exc_info=True)
                    return None
                
        except Exception as e:
            logger.error(f"Error with microphone during listening: {e}", exc_info=True)
            return None
    
    def process_speech(self, audio_data: bytes) -> Optional[VoiceCommand]:
        """Process audio data and return a VoiceCommand if speech is recognized"""
        # Log audio data length for debugging
        logger.debug(f"Processing audio data of length: {len(audio_data)} bytes")
        
        if not audio_data:
            logger.debug("No audio data received")
            return None
            
        if len(audio_data) < 20:  # Extremely low minimum length
            logger.debug(f"Audio data too short: {len(audio_data)} bytes")
            return None
            
        try:
            # Create an AudioData object from the raw audio data
            audio = sr.AudioData(
                frame_data=audio_data,
                sample_rate=16000,
                sample_width=2
            )
            
            # Convert speech to text with a timeout
            try:
                logger.debug("Attempting speech recognition...")
                text = self.recognizer.recognize_google(
                    audio,
                    language='en-US',
                    show_all=False  # Get single best result
                )
                logger.debug(f"Raw recognition result: {text}")
                terminal_ui.print_command(text)  # Print the recognized command
            except sr.UnknownValueError:
                logger.debug("Speech recognition returned no results")
                terminal_ui.print_warning("Could not understand audio")
                return None
            except sr.RequestError as e:
                logger.error(f"Speech recognition service error: {e}")
                terminal_ui.print_error(f"Speech recognition service error: {e}")
                return None
            
            if not text or not text.strip():
                logger.debug("Empty speech recognition result")
                return None
                
            logger.info(f"Recognized speech: {text}")
            
            # Get NLU intent if available
            nlu = get_nlu_engine()
            intent = None
            confidence = 0.3  # Very low default confidence threshold
            
            if nlu is not None:
                try:
                    intent = nlu.detect_intent(text)
                    if intent:
                        confidence = max(confidence, intent.confidence)
                        logger.debug(f"Detected intent: {intent.name} (confidence: {confidence:.2f})")
                    else:
                        logger.debug("No intent detected, using default confidence")
                except Exception as e:
                    logger.warning(f"NLU processing warning: {e}")
            
            # Accept any non-empty text
            text = text.strip()
            if not text:
                logger.debug("Empty text after stripping")
                return None
                
            logger.debug(f"Creating VoiceCommand with text: {text}")
            return VoiceCommand(
                text=text,
                confidence=confidence,
                intent=intent
            )
            
        except Exception as e:
            logger.error(f"Unexpected error in process_speech: {str(e)}", exc_info=True)
            terminal_ui.print_error(f"Error processing speech: {e}")
            return None
    
    def start_continuous_listening(self):
        """Start continuous listening in a separate thread"""
        if self.is_listening:
            logger.warning("Already listening")
            return
        
        # Create and start the listening thread
        self.is_listening = True
        self._stop_listening.clear()
        self._listening_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self._listening_thread.start()
        logger.info("Started continuous listening")
        
    def _listen_loop(self):
        """Main listening loop for continuous listening"""
        try:
            logger.info("Starting continuous listening loop")
            self.is_listening = True
            consecutive_errors = 0
            
            while self.is_listening:
                try:
                    if self._listening_thread and self._listening_thread != threading.current_thread():
                        self._listening_thread.join(timeout=2.0)
                    
                    if not self.microphone or not self._mic_setup_complete:
                        self.microphone = self._get_best_microphone()
                        if not self.microphone:
                            raise RuntimeError("No working microphone found")
                        self._setup_microphone()
                    
                    # Adjust for ambient noise less frequently
                    current_time = time.time()
                    if not hasattr(self, '_last_noise_adjustment') or \
                       current_time - self._last_noise_adjustment > 60:
                        logger.debug("Adjusting for ambient noise...")
                        try:
                            with self.microphone as source:
                                self.recognizer.adjust_for_ambient_noise(source, duration=2)
                                # Ensure energy threshold is within bounds
                                self.recognizer.energy_threshold = max(
                                    min(self.recognizer.energy_threshold, self._max_energy_threshold),
                                    self._min_energy_threshold
                                )
                                self._last_noise_adjustment = current_time
                                logger.debug(f"Energy threshold adjusted to: {self.recognizer.energy_threshold}")
                        except Exception as e:
                            logger.warning(f"Ambient noise adjustment failed: {e}")
                    
                    # Listen for audio in a separate context
                    audio = None
                    with self.microphone as source:
                        audio = self.recognizer.listen(
                            source,
                            timeout=1.0,
                            phrase_time_limit=5.0
                        )
                    
                    if audio:
                        try:
                            command = self.process_speech(audio.get_wav_data())
                            if command and command.text:
                                self.command_queue.put(command)
                                consecutive_errors = 0
                            else:
                                consecutive_errors += 1
                                if consecutive_errors >= 3:
                                    logger.warning("Too many unrecognized commands, adjusting sensitivity...")
                                    # Decrease energy threshold to be more sensitive
                                    self.recognizer.energy_threshold = max(
                                        self.recognizer.energy_threshold * 0.8,  # Reduce by 20%
                                        self._min_energy_threshold
                                    )
                                    consecutive_errors = 0
                        except Exception as e:
                            logger.error(f"Error processing audio: {e}")
                            consecutive_errors += 1
                            if consecutive_errors >= 3:
                                logger.warning("Too many consecutive errors, attempting to recover...")
                                self.microphone = None
                                self._mic_setup_complete = False
                                consecutive_errors = 0
                                time.sleep(0.5)
                
                except sr.WaitTimeoutError:
                    continue
                except Exception as e:
                    logger.error(f"Error in listen loop: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= 3:
                        logger.warning("Too many consecutive errors, attempting to recover...")
                        self.microphone = None
                        self._mic_setup_complete = False
                        consecutive_errors = 0
                        time.sleep(0.5)
                
        except Exception as e:
            logger.error(f"Fatal error in listen loop: {e}")
        finally:
            self.is_listening = False
            self._stop_listening.set()
            logger.info("Continuous listening stopped")
    
    def stop_continuous_listening(self):
        """Stop continuous listening"""
        if not self.is_listening:
            logger.warning("Not currently listening")
            return
        
        self.is_listening = False
        
        # Wait for the listening thread to finish, but don't join if it's the current thread
        if self._listening_thread and self._listening_thread != threading.current_thread():
            try:
                self._listening_thread.join(timeout=5.0)
            except Exception as e:
                logger.warning(f"Error stopping listening thread: {e}")
        
        self._listening_thread = None
        logger.info("Stopped continuous listening")
    
    def register_callback(self, callback: Callable[[VoiceCommand], None]):
        """Register a callback to be called when a command is recognized"""
        self.callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[VoiceCommand], None]):
        """Unregister a callback"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def process_command_queue(self):
        """Process all commands in the queue
        
        Returns:
            List of processed commands
        """
        commands = []
        while not self.command_queue.empty():
            try:
                commands.append(self.command_queue.get_nowait())
            except queue.Empty:
                break
        return commands


# Singleton instance
voice_engine = VoiceEngine()

# Example usage
if __name__ == "__main__":
    def on_command(command: VoiceCommand):
        print(f"Heard: {command.text}")
        if command.is_wake_word:
            print("Wake word detected!")
    
    voice_engine.register_callback(on_command)
    print("Listening for commands... Say 'hey assistant' to activate.")
    voice_engine.start_continuous_listening()
    
    try:
        while True:
            commands = voice_engine.process_command_queue()
            for cmd in commands:
                print(f"Processed: {cmd.text}")
            time.sleep(0.1)
    except KeyboardInterrupt:
        voice_engine.stop_continuous_listening()
        print("\nStopped listening")
