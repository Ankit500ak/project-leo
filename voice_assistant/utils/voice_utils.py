"""Voice-related utility functions for the Voice Assistant.

This module provides utility functions for working with voice input and output,
including text-to-speech, speech recognition, and voice processing.
"""

import logging
import queue
import re
import threading
import time
import wave
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Callable, Any

import numpy as np
import pyaudio
import speech_recognition as sr
from pydub import AudioSegment
from pydub.effects import normalize

from ..core.settings import settings

logger = logging.getLogger(__name__)

class AudioFormat:
    """Audio format constants."""
    RATE = 16000  # Sample rate in Hz
    CHANNELS = 1  # Mono audio
    CHUNK = 1024  # Number of frames per buffer
    FORMAT = pyaudio.paInt16  # 16-bit audio
    THRESHOLD = 500  # Silence threshold
    SILENCE_LIMIT = 1.0  # Seconds of silence to mark end of speech
    PREV_AUDIO = 0.5  # Seconds of audio to keep before voice is detected

class VoiceState(Enum):
    """Voice recognition states."""
    IDLE = auto()
    LISTENING = auto()
    PROCESSING = auto()
    SPEAKING = auto()
    ERROR = auto()

@dataclass
class VoiceCommand:
    """Represents a recognized voice command."""
    text: str
    confidence: float
    is_wake_word: bool = False
    raw_audio: Optional[bytes] = None
    timestamp: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'confidence': self.confidence,
            'is_wake_word': self.is_wake_word,
            'timestamp': self.timestamp
        }

class WakeWordDetector:
    """Detects wake words in audio input."""
    
    def __init__(self, wake_words: Optional[List[str]] = None, sensitivity: float = 0.5):
        """Initialize the wake word detector.
        
        Args:
            wake_words: List of wake words to detect
            sensitivity: Detection sensitivity (0.0 to 1.0)
        """
        self.wake_words = wake_words or settings.get('voice.wake_words', [])
        self.sensitivity = max(0.0, min(1.0, sensitivity))
        self.recognizer = sr.Recognizer()
        self.recognizer.pause_threshold = settings.get('voice.pause_threshold', 0.8)
        self.recognizer.energy_threshold = settings.get('voice.energy_threshold', 300)
        self.recognizer.dynamic_energy_threshold = settings.get('voice.dynamic_energy_threshold', True)
    
    def is_wake_word(self, text: str) -> Tuple[bool, Optional[str]]:
        """Check if the given text contains a wake word.
        
        Args:
            text: Text to check
            
        Returns:
            Tuple of (is_wake_word, wake_word_found)
        """
        if not text or not self.wake_words:
            return False, None
            
        text = text.lower().strip()
        for word in self.wake_words:
            if word.lower() in text:
                # Calculate confidence based on position and length
                word_len = len(word)
                pos = text.find(word.lower())
                confidence = 0.5  # Base confidence
                
                # Increase confidence if at start of phrase
                if pos == 0:
                    confidence += 0.3
                
                # Increase confidence if it's the only word
                if len(text.split()) == 1:
                    confidence += 0.2
                
                if confidence >= self.sensitivity:
                    return True, word
        
        return False, None

class AudioRecorder:
    """Records audio from the microphone."""
    
    def __init__(self, format: AudioFormat = AudioFormat):
        """Initialize the audio recorder.
        
        Args:
            format: Audio format to use for recording
        """
        self.format = format
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.frames = []
        self.is_recording = False
        self.recording_thread = None
        self._stop_event = threading.Event()
    
    def start_recording(self) -> None:
        """Start recording audio from the microphone."""
        if self.is_recording:
            return
            
        self.frames = []
        self._stop_event.clear()
        
        self.stream = self.audio.open(
            format=self.format.FORMAT,
            channels=self.format.CHANNELS,
            rate=self.format.RATE,
            input=True,
            frames_per_buffer=self.format.CHUNK,
            stream_callback=self._audio_callback
        )
        
        self.is_recording = True
        logger.info("Audio recording started")
    
    def stop_recording(self) -> bytes:
        """Stop recording and return the recorded audio data.
        
        Returns:
            bytes: Recorded audio data
        """
        if not self.is_recording:
            return b''
            
        self._stop_event.set()
        
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception as e:
                logger.error(f"Error stopping audio stream: {e}")
        
        self.is_recording = False
        logger.info("Audio recording stopped")
        
        # Combine all frames into a single audio buffer
        audio_data = b''.join(self.frames)
        self.frames = []
        
        return audio_data
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Callback for audio stream."""
        if self._stop_event.is_set():
            return (None, pyaudio.paComplete)
            
        self.frames.append(in_data)
        return (None, pyaudio.paContinue)
    
    def record_until_silence(
        self, 
        silence_limit: float = 2.0, 
        silence_threshold: float = 0.03,
        record_seconds: Optional[float] = None
    ) -> bytes:
        """Record audio until silence is detected or max time is reached.
        
        Args:
            silence_limit: Maximum seconds of silence to allow before stopping
            silence_threshold: Threshold for considering audio as silence (0.0 to 1.0)
            record_seconds: Maximum seconds to record (None for no limit)
            
        Returns:
            bytes: Recorded audio data
        """
        self.frames = []
        self._stop_event.clear()
        
        # Open stream
        stream = self.audio.open(
            format=self.format.FORMAT,
            channels=self.format.CHANNELS,
            rate=self.format.RATE,
            input=True,
            frames_per_buffer=self.format.CHUNK
        )
        
        try:
            # Buffer to store audio data
            audio_buffer = []
            silent_chunks = 0
            audio_started = False
            start_time = time.time()
            
            while True:
                # Check if we've exceeded the maximum recording time
                if record_seconds and (time.time() - start_time) > record_seconds:
                    logger.debug("Maximum recording time reached")
                    break
                
                # Read audio data
                data = stream.read(self.format.CHUNK, exception_on_overflow=False)
                audio_buffer.append(data)
                
                # Convert to numpy array for analysis
                audio_data = np.frombuffer(data, dtype=np.int16)
                
                # Check if audio level is above threshold
                rms = np.sqrt(np.mean(audio_data ** 2)) / 32768.0  # Convert to 0.0-1.0 range
                
                if rms > silence_threshold:
                    audio_started = True
                    silent_chunks = 0
                elif audio_started:
                    silent_chunks += 1
                    
                    # Stop if we've had enough silent chunks
                    if silent_chunks > (silence_limit * self.format.RATE) / self.format.CHUNK:
                        logger.debug("Silence detected, stopping recording")
                        break
                
                # Keep only the last N seconds of audio in the buffer
                max_buffer_chunks = int((self.format.RATE * 10) / self.format.CHUNK)  # 10 second buffer
                if len(audio_buffer) > max_buffer_chunks:
                    audio_buffer = audio_buffer[-max_buffer_chunks:]
            
            return b''.join(audio_buffer)
            
        finally:
            stream.stop_stream()
            stream.close()
    
    def save_audio(self, audio_data: bytes, file_path: Union[str, Path]) -> bool:
        """Save audio data to a WAV file.
        
        Args:
            audio_data: Audio data to save
            file_path: Path to save the audio file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path).with_suffix('.wav')
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with wave.open(str(file_path), 'wb') as wf:
                wf.setnchannels(self.format.CHANNELS)
                wf.setsampwidth(self.audio.get_sample_size(self.format.FORMAT))
                wf.setframerate(self.format.RATE)
                wf.writeframes(audio_data)
            
            logger.debug(f"Audio saved to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving audio to {file_path}: {e}")
            return False
    
    def play_audio(self, audio_data: bytes) -> None:
        """Play audio data through the default audio output device.
        
        Args:
            audio_data: Audio data to play
        """
        stream = self.audio.open(
            format=self.format.FORMAT,
            channels=self.format.CHANNELS,
            rate=self.format.RATE,
            output=True
        )
        
        try:
            stream.write(audio_data)
        finally:
            stream.stop_stream()
            stream.close()
    
    def __del__(self):
        """Clean up resources."""
        if hasattr(self, 'stream') and self.stream:
            self.stream.close()
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()

class SpeechSynthesizer:
    """Converts text to speech."""
    
    def __init__(self, engine: str = 'pyttsx3'):
        """Initialize the speech synthesizer.
        
        Args:
            engine: TTS engine to use ('pyttsx3' or 'gtts')
        """
        self.engine_name = engine.lower()
        self.engine = None
        self.voices = []
        self.current_voice = 0
        self.rate = settings.get('voice.rate', 170)
        self.volume = settings.get('voice.volume', 0.9)
        
        self._init_engine()
    
    def _init_engine(self) -> None:
        """Initialize the TTS engine."""
        try:
            if self.engine_name == 'pyttsx3':
                import pyttsx3
                self.engine = pyttsx3.init()
                self.voices = self.engine.getProperty('voices')
                self.engine.setProperty('rate', self.rate)
                self.engine.setProperty('volume', self.volume)
                
                # Set voice based on settings
                voice_id = settings.get('voice.voice_id', 1)  # 0 for male, 1 for female (Windows)
                if 0 <= voice_id < len(self.voices):
                    self.engine.setProperty('voice', self.voices[voice_id].id)
            
            elif self.engine_name == 'gtts':
                from gtts import gTTS
                import tempfile
                import os
                self.temp_dir = tempfile.mkdtemp()
                self.temp_files = []
            
            else:
                raise ValueError(f"Unsupported TTS engine: {self.engine_name}")
                
        except ImportError as e:
            logger.error(f"Failed to initialize TTS engine {self.engine_name}: {e}")
            # Fall back to the first available engine
            if self.engine_name != 'pyttsx3':
                logger.info("Falling back to pyttsx3")
                self.engine_name = 'pyttsx3'
                self._init_engine()
            else:
                raise RuntimeError("No TTS engine available. Please install pyttsx3 or gTTS.")
    
    def set_voice(self, voice_id: int) -> bool:
        """Set the voice to use for speech synthesis.
        
        Args:
            voice_id: Index of the voice to use
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.engine or not self.voices:
            return False
            
        if 0 <= voice_id < len(self.voices):
            self.current_voice = voice_id
            
            if self.engine_name == 'pyttsx3':
                self.engine.setProperty('voice', self.voices[voice_id].id)
                return True
                
        return False
    
    def set_rate(self, rate: int) -> None:
        """Set the speech rate in words per minute.
        
        Args:
            rate: Words per minute (default is around 200)
        """
        self.rate = max(50, min(300, rate))  # Clamp to reasonable values
        
        if self.engine and self.engine_name == 'pyttsx3':
            self.engine.setProperty('rate', self.rate)
    
    def set_volume(self, volume: float) -> None:
        """Set the speech volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.volume = max(0.0, min(1.0, volume))  # Clamp to 0.0-1.0
        
        if self.engine and self.engine_name == 'pyttsx3':
            self.engine.setProperty('volume', self.volume)
    
    def speak(self, text: str, block: bool = True) -> None:
        """Convert text to speech and speak it.
        
        Args:
            text: Text to speak
            block: If True, block until speech is complete
        """
        if not text.strip():
            return
            
        # Create an event for the speech synthesis
        event = SpeechSynthesisEvent(text=text)
        
        # Publish the event to allow modification
        from ..core.events import publish
        publish(event)
        
        if event.cancelled:
            return
            
        text = event.text
        
        try:
            if self.engine_name == 'pyttsx3' and self.engine:
                if block:
                    self.engine.say(text)
                    self.engine.runAndWait()
                else:
                    # Run in a separate thread to avoid blocking
                    def _speak():
                        self.engine.say(text)
                        self.engine.runAndWait()
                    
                    import threading
                    thread = threading.Thread(target=_speak)
                    thread.daemon = True
                    thread.start()
            
            elif self.engine_name == 'gtts':
                from gtts import gTTS
                import tempfile
                import os
                import platform
                
                # Create a temporary file for the speech
                with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
                    temp_file = f.name
                
                # Generate speech
                tts = gTTS(text=text, lang='en')
                tts.save(temp_file)
                self.temp_files.append(temp_file)
                
                # Play the audio file
                if platform.system() == 'Windows':
                    import winsound
                    winsound.PlaySound(temp_file, winsound.SND_FILENAME)
                else:
                    from pydub import AudioSegment
                    from pydub.playback import play
                    sound = AudioSegment.from_mp3(temp_file)
                    play(sound)
                
                # Clean up old temporary files
                while len(self.temp_files) > 5:  # Keep last 5 files
                    old_file = self.temp_files.pop(0)
                    try:
                        os.unlink(old_file)
                    except OSError:
                        pass
                        
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
    
    def save_to_file(self, text: str, file_path: Union[str, Path]) -> bool:
        """Save speech to an audio file.
        
        Args:
            text: Text to convert to speech
            file_path: Path to save the audio file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            file_path = Path(file_path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if self.engine_name == 'pyttsx3' and self.engine:
                self.engine.save_to_file(text, str(file_path))
                self.engine.runAndWait()
                return True
                
            elif self.engine_name == 'gtts':
                from gtts import gTTS
                tts = gTTS(text=text, lang='en')
                tts.save(str(file_path))
                return True
                
        except Exception as e:
            logger.error(f"Error saving speech to file {file_path}: {e}")
            
        return False
    
    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get a list of available voices.
        
        Returns:
            List of voice information dictionaries
        """
        voices = []
        
        if self.engine_name == 'pyttsx3' and self.engine:
            for i, voice in enumerate(self.voices):
                voices.append({
                    'id': i,
                    'name': voice.name,
                    'gender': 'male' if 'male' in voice.name.lower() else 'female',
                    'languages': getattr(voice, 'languages', ['en']),
                })
        
        return voices

def text_to_speech(text: str, block: bool = True) -> None:
    """Convert text to speech using the default synthesizer.
    
    Args:
        text: Text to speak
        block: If True, block until speech is complete
    """
    synthesizer = SpeechSynthesizer()
    synthesizer.speak(text, block)

def recognize_speech(timeout: float = 5.0, phrase_time_limit: float = 10.0) -> Optional[str]:
    """Recognize speech from the microphone.
    
    Args:
        timeout: Timeout in seconds for speech recognition
        phrase_time_limit: Maximum time in seconds for a phrase
        
    Returns:
        Recognized text or None if no speech was recognized
    """
    recognizer = sr.Recognizer()
    
    with sr.Microphone() as source:
        logger.debug("Listening...")
        try:
            audio = recognizer.listen(source, timeout=timeout, phrase_time_limit=phrase_time_limit)
            text = recognizer.recognize_google(audio)
            logger.debug(f"Recognized: {text}")
            return text
        except sr.WaitTimeoutError:
            logger.debug("No speech detected")
        except sr.UnknownValueError:
            logger.debug("Could not understand audio")
        except sr.RequestError as e:
            logger.error(f"Could not request results from speech recognition service; {e}")
        except Exception as e:
            logger.error(f"Error in speech recognition: {e}")
    
    return None

def normalize_audio(audio_data: bytes, target_dBFS: float = -20.0) -> bytes:
    """Normalize audio volume.
    
    Args:
        audio_data: Input audio data
        target_dBFS: Target volume in dBFS
        
    Returns:
        Normalized audio data
    """
    try:
        # Create an AudioSegment from the raw data
        audio = AudioSegment(
            audio_data,
            frame_rate=AudioFormat.RATE,
            sample_width=pyaudio.PyAudio().get_sample_size(AudioFormat.FORMAT),
            channels=AudioFormat.CHANNELS
        )
        
        # Normalize the audio
        normalized = normalize(audio).apply_gain(target_dBFS - audio.dBFS)
        
        # Convert back to raw data
        return normalized.raw_data
    
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}")
        return audio_data  # Return original if normalization fails

def convert_audio_format(
    input_data: bytes, 
    input_format: str = 'wav', 
    output_format: str = 'mp3',
    sample_rate: int = 16000,
    channels: int = 1
) -> Optional[bytes]:
    """Convert audio between formats.
    
    Args:
        input_data: Input audio data
        input_format: Input format (e.g., 'wav', 'mp3')
        output_format: Output format (e.g., 'wav', 'mp3')
        sample_rate: Sample rate in Hz
        channels: Number of audio channels
        
    Returns:
        Converted audio data or None if conversion fails
    """
    try:
        # Create a temporary file for the input
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=f'.{input_format}', delete=False) as f_in:
            f_in.write(input_data)
            temp_input = f_in.name
        
        # Create a temporary file for the output
        with tempfile.NamedTemporaryFile(suffix=f'.{output_format}', delete=True) as f_out:
            temp_output = f_out.name
        
        # Load the audio file
        audio = AudioSegment.from_file(temp_input, format=input_format)
        
        # Set sample rate and channels
        audio = audio.set_frame_rate(sample_rate).set_channels(channels)
        
        # Export to the output format
        audio.export(temp_output, format=output_format)
        
        # Read the converted data
        with open(temp_output, 'rb') as f:
            output_data = f.read()
        
        # Clean up temporary files
        import os
        os.unlink(temp_input)
        os.unlink(temp_output)
        
        return output_data
    
    except Exception as e:
        logger.error(f"Error converting audio from {input_format} to {output_format}: {e}")
        return None

# Export commonly used functions and classes
__all__ = [
    'AudioFormat',
    'VoiceState',
    'VoiceCommand',
    'WakeWordDetector',
    'AudioRecorder',
    'SpeechSynthesizer',
    'text_to_speech',
    'recognize_speech',
    'normalize_audio',
    'convert_audio_format',
]
