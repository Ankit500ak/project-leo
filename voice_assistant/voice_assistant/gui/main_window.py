import sys
import os
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QIcon, QFont, QColor, QPalette, QPixmap
from voice_assistant.core.voice_engine import voice_engine, VoiceCommand

class VoiceAssistantGUI(QMainWindow):
    """Main window for the Voice Assistant application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Voice Assistant")
        self.setMinimumSize(800, 600)
        
        # Set the application style
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QLabel {
                color: #ffffff;
                font-size: 14px;
            }
            QTextEdit {
                background-color: #2d2d2d;
                color: #ffffff;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
                font-size: 13px;
            }
            QPushButton {
                background-color: #0d6efd;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 16px;
                font-size: 14px;
                min-width: 100px;
            }
            QPushButton:hover {
                background-color: #0b5ed7;
            }
            QPushButton:pressed {
                background-color: #0a58ca;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
            QFrame {
                background-color: #2d2d2d;
                border-radius: 10px;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Create header
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        
        # Assistant icon/avatar
        avatar_label = QLabel()
        avatar_label.setFixedSize(60, 60)
        avatar_label.setStyleSheet("""
            QLabel {
                background-color: #0d6efd;
                border-radius: 30px;
                font-size: 24px;
                font-weight: bold;
            }
        """)
        avatar_label.setText("VA")
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Title and status
        title_layout = QVBoxLayout()
        title_label = QLabel("Voice Assistant")
        title_label.setStyleSheet("font-size: 24px; font-weight: bold;")
        self.status_label = QLabel("Ready to listen...")
        self.status_label.setStyleSheet("color: #6c757d;")
        title_layout.addWidget(title_label)
        title_layout.addWidget(self.status_label)
        
        header_layout.addWidget(avatar_label)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Add header to main layout
        main_layout.addWidget(header_frame)
        
        # Create conversation display
        self.conversation_display = QTextEdit()
        self.conversation_display.setReadOnly(True)
        self.conversation_display.setMinimumHeight(300)
        self.conversation_display.setStyleSheet("""
            QTextEdit {
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.5;
            }
        """)
        main_layout.addWidget(self.conversation_display)
        
        # Create control buttons
        button_frame = QFrame()
        button_layout = QHBoxLayout(button_frame)
        
        self.start_button = QPushButton("Start Listening")
        self.start_button.clicked.connect(self.start_listening)
        self.stop_button = QPushButton("Stop Listening")
        self.stop_button.clicked.connect(self.stop_listening)
        self.stop_button.setEnabled(False)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addStretch()
        
        main_layout.addWidget(button_frame)
        
        # Create status bar
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2d2d2d;
                color: #6c757d;
            }
        """)
        self.statusBar().showMessage("Voice Assistant is ready")
        
        # Initialize voice engine callback
        voice_engine.register_callback(self.on_voice_command)
        
        # Add initial message
        self.add_to_conversation("Assistant", "Hello! I'm your voice assistant. Click 'Start Listening' to begin.")
        
    def start_listening(self):
        """Start the voice assistant"""
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText("Listening...")
        self.status_label.setStyleSheet("color: #28a745;")
        self.statusBar().showMessage("Voice Assistant is listening")
        voice_engine.start_continuous_listening()
        
    def stop_listening(self):
        """Stop the voice assistant"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.status_label.setText("Ready to listen...")
        self.status_label.setStyleSheet("color: #6c757d;")
        self.statusBar().showMessage("Voice Assistant is stopped")
        voice_engine.stop_continuous_listening()
        
    def on_voice_command(self, command: VoiceCommand):
        """Handle voice commands"""
        if command.is_wake_word:
            self.add_to_conversation("You", command.text, is_wake_word=True)
            self.add_to_conversation("Assistant", "Yes? How can I help you?")
        else:
            self.add_to_conversation("You", command.text)
            # The actual response will be handled by the command processor
            # and will be added to the conversation through the event system
            
    def add_to_conversation(self, speaker: str, text: str, is_wake_word: bool = False):
        """Add a message to the conversation display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format the message based on the speaker
        if speaker == "You":
            style = "color: #0d6efd;"
            prefix = "👤"
        else:
            style = "color: #28a745;"
            prefix = "🤖"
            
        if is_wake_word:
            style += " font-style: italic;"
            
        message = f'<div style="margin: 5px 0;"><span style="{style}">{prefix} {speaker} ({timestamp}):</span> {text}</div>'
        
        self.conversation_display.append(message)
        # Scroll to the bottom
        self.conversation_display.verticalScrollBar().setValue(
            self.conversation_display.verticalScrollBar().maximum()
        )
        
    def closeEvent(self, event):
        """Handle window close event"""
        voice_engine.stop_continuous_listening()
        event.accept()

def run_gui():
    """Run the GUI application"""
    app = QApplication(sys.argv)
    window = VoiceAssistantGUI()
    window.show()
    sys.exit(app.exec()) 