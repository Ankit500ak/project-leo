from setuptools import setup, find_packages
import os

# Read the contents of README.md
this_directory = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

# Core dependencies
install_requires = [
    'SpeechRecognition>=3.8.1',
    'pyttsx3>=2.90',
    'python-dotenv>=0.19.0',
    'pyautogui>=0.9.53',
    'keyboard>=0.13.5',
    'Pillow>=8.4.0',
    'numpy>=1.21.4',
    'pandas>=1.3.4',
    'pywin32>=303',
    'comtypes>=1.1.10',
    'pydub>=0.25.1',
    'sounddevice>=0.4.3',
    'soundfile>=0.10.3',
    'librosa>=0.8.1',
    'colorama>=0.4.4',
    'pyyaml>=6.0',
    'requests>=2.26.0',
    'transformers>=4.30.0',
    'torch>=2.0.0',
    'beautifulsoup4>=4.10.0',
    'python-dateutil>=2.8.2',
    'pywhatkit>=5.2',
    'wikipedia>=1.4.0',
    'wolframalpha>=5.0.0',
    'google-generativeai>=0.3.0',
    'pywinauto>=0.6.8',
    'pygetwindow>=0.0.9',
    'pytesseract>=0.3.8',
    'opencv-python>=4.5.4.58',
    'pyperclip>=1.8.2',
    'pyjokes>=0.6.0',
    'geocoder>=1.38.1',
    'geopy>=2.2.0',
    'pytz>=2021.3',
    'python-weather>=0.5.0',
    'pyfiglet>=0.8.post1'
]

setup(
    name="voice-assistant",
    version="0.1.0",
    author="Ankit",
    author_email="your.email@example.com",
    description="A powerful voice assistant with natural language understanding capabilities",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/voice-assistant",
    packages=find_packages(include=['voice_assistant', 'voice_assistant.*']),
    package_data={
        'voice_assistant': ['*.json', '*.yaml', '*.yml', '*.md'],
    },
    python_requires='>=3.8',
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'voice-assistant=voice_assistant.main:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Topic :: Multimedia :: Sound/Audio :: Speech',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    keywords='voice-assistant nlu speech-recognition nlp',
    project_urls={
        'Bug Reports': 'https://github.com/yourusername/voice-assistant/issues',
        'Source': 'https://github.com/yourusername/voice-assistant',
    }
)
