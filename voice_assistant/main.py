import os
import sys
import json
import time
import logging
import logging.handlers
import datetime
from typing import Dict, Any, Optional
from pathlib import Path
from simple_colors import *

# Set up logging
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.handlers.RotatingFileHandler(
            log_dir / 'voice_assistant.log',
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3
        )
    ]
)

logger = logging.getLogger(__name__)

# Add the project root to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import core functionality
from voice_assistant.core import (
    voice_engine, 
    VoiceCommand,
    Intent,
    event_bus,
    VoiceCommandEvent,
    command_processor
)

# Initialize text-to-speech
import pyttsx3
bot = pyttsx3.init('sapi5') 
voices = bot.getProperty('voices')
bot.setProperty('voice', voices[1].id)  
bot.setProperty('rate', 170)

# Global flag to control the main loop
running = True 

# Get user's home directory dynamically
HOME_DIR = os.path.expanduser("~")
DATA_DIR = os.path.join(HOME_DIR, "voice_assistant_data")
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR) 

def speak(audio): 
    print("   ") 
    print('zero : ', green(f'{audio}', 'bold'))  
    print("   ") 
    bot.say(audio) 
    bot.runAndWait() 

def takecommand():
    try:
        # Use our voice engine with NLU
        command = voice_engine.get_command()
        if command:
            print(f"Recognized: {command.text}")
            print(f"Intent: {command.intent.name}")
            print(f"Entities: {command.intent.entities}")
            return command
        return None
    except Exception as e:
        print(f"Error in takecommand: {e}")
        speak("Sorry, I had trouble understanding your command. Please try again.")
        return None 

def wish_me(): 
    hour=int(datetime.datetime.now().hour) 
    if hour>=0 and hour<12: 
        speak("Good Morning Sir!") 
    elif hour>=12 and hour<=18: 
        speak("Good Afternoon Sir!") 
    else: 
        speak("Good Evening Sir!") 
    speak('my name is Zero . How can i Help you ?') 

def Alarm(query):
    try:
        data_file = os.path.join(DATA_DIR, "data.txt")
        with open(data_file, 'a') as time_file:
            time_file.write(query + "\n")
        alarm_script = os.path.join(DATA_DIR, "alarm.py")
        os.startfile(alarm_script)
    except Exception as e:
        speak(f"Error setting alarm: {str(e)}")
        return False
    return True     

def downyoutube(): 
    try:
        from pytube import YouTube 
        from pyautogui import click 
        from pyautogui import hotkey 
        import pyperclip 
     
        from time import sleep 
     
        sleep(2) 
     
        click(x=205,y=62) 
     
        hotkey('ctrl','c') 
     
        value= pyperclip.paste() 
     
        link = str(value) 
 
        def download(link): 
        
            url = YouTube(link) 
            vedio = url.streams.get_highest_resolution() 
            speak("sir the download has been started") 
            download_dir = os.path.join(DATA_DIR, "downloads", "youtube")
            if not os.path.exists(download_dir):
                os.makedirs(download_dir)
            vedio.download(download_dir) 
        download(link) 
        speak("sir i have downloaded the vedio") 
        speak("you can check it out") 
        os.startfile(download_dir) 
    except Exception as e:
        speak(f"Error downloading video: {str(e)}") 

def Speedtest(): 
    try:
        test_script = os.path.join(DATA_DIR, "gui_program", "SpeedTestGui.py")
        os.startfile(test_script)
        speak("Speed test has been initiated")
    except Exception as e:
        speak(f"Error running speed test: {str(e)}") 

def teach(query): 
    api_key = "7RAJ2A-8YUGV5Q2WG" 
    request = wolframalpha.Client(api_key) 
    requested = request.query(query) 
    
     
    try: 
        answer = next(requested.results).text 
        return answer 
    except: 
        speak(" According to my database this Question is not Answerable")         

def My_location(): 
    open  ='https://www.google.co.in/maps/@28.4729472,77.0363116,613a,35y,39.13t/data=!3m1!1e3?entry=ttu' 
    speak("checking....") 
    webbrowser.open(open) 
     
    ip_add = requests.get('https://api.ipify.org').text 
    url = 'https://get.geojs.io/v1/ip/geo/' + ip_add + '.json' 
    geo_q = requests.get(url) 
    geo_d = geo_q.json() 
    state = geo_d['city'] 
    country = geo_d['country'] 
    speak(f"sir you are now in {state, country}") 
  
 
 
 
 
def calculator(query): 
    term  =str(query) 
    term = term.replace("multiply","*") 
    term = term.replace("plus","+") 
    term = term.replace("multiply","*") 
    term = term.replace("devide by","/") 
    term = term.replace("minus","-") 
    term = term.replace("into","*") 
     
    final = str(term) 
    result=teach(final) 
    speak(f"Output is :{result}")   
def temp(query): 
    term = str(query) 
     
    term=term.replace("zero","") 
    term=term.replace("in","") 
    term=term.replace("what is","") 
    term=term.replace("temperature","") 
     
    temp_query = str(term) 
     
    if 'outside' in temp_query: 
        var1 = "Temperature in Haryana" 
        answer = teach(var1) 
        speak(f"{var1} is {answer}") 
         
    else: 
        var2  = "Temperature in"+temp_query 
        answer = teach(var2) 
        speak(f"{var2} is {answer}")  
def close_window():
    try:
        pg.click(1341, 11)
    except Exception as e:
        speak(f"Error closing window: {str(e)}") 

def whatsapp(name,message): 
    click(x=503, y=744) 
    sleep(2) 
    key='whatsapp' 
    write(key) 
    sleep(2) 
    click(x=568, y=175) 
    sleep(2) 
    write(name) 
    sleep(2) 
    click(x=233, y=169) 
    sleep(2) 
    write(message) 
    press('enter') 
    close() 
     
    speak(f" Sir i have sent the message to {name}") 
def vediocall(name): 
    click(x=547, y=743) 
    sleep(2) 
    key='whatsapp' 
    write(key) 
    sleep(2) 
    click(x=568, y=175) 
    sleep(2) 
    write(name) 
    sleep(2) 
    click(x=233, y=169) 
    sleep(2) 
    click(x=1218, y=64) 
def call(name): 
    click(x=547, y=743) 
    sleep(2) 
    key='whatsapp' 
    write(key) 
    sleep(2) 
    click(x=568, y=175) 
    sleep(2) 
    write(name) 
    sleep(2) 
    click(x=233, y=169) 
    sleep(2) 
    click(x=1270, y=71) 
def chat(name): 
    click(x=547, y=743) 
    sleep(2) 
    key='whatsapp' 
    write(key) 
    sleep(2) 
    click(x=568, y=175) 
    sleep(2) 
    write(name) 
    sleep(2) 
    click(x=233, y=169) 
 
   
def youtube(command): 
    query=str(command) 
    if 'pause' in query: 
        press_and_release('k') 
    elif 'mute' in query: 
        press_and_release('m') 
    elif 'unmute' in query: 
        press_and_release('m') 
    elif 'seek back' in query: 
        press_and_release('j') 
    elif 'seek front' in query: 
        press_and_release('l') 
    elif 'full screen' in query: 
        press_and_release('f') 
    elif 'film' in query: 
        press_and_release('t') 
    elif 'skip' in query: 
        press_and_release('l') 
    elif 'increase' in query: 
        press_and_release('shift + >') 
    elif 'decrease' in query: 
        press_and_release('shift + <') 
    elif 'previous' in query: 
        press_and_release('shift + p')  
    elif 'next' in query: 
        press_and_release('shift + n') 
    elif 'search' in query: 
        click(x=550, y=98) 
        search=query.replace("youtube","") 
        search1=search.replace("search","") 
        write(search1) 
        sleep(1) 
        press('enter') 
def date_converter(query): 
    date = query.replace(" and ","-") 
    date = query.replace(" and","-") 
    date = query.replace("and ","-") 
    date = query.replace("and","-") 
    date = query.replace(" ","") 
    return str(date) 
def NasaNews(date): 
            api_key="XNN3qHB7sIu5egaoKKBcUhJ4aM4yGodEHLBYfHnh" 
            url = "http://api.nasa.gov/planetary/apod?api_key=" + str(api_key) 
            Para = {'date':str(date)} 
            r=requests.get(url,params = Para) 
            data = r.json() 
            info = data['explanation'] 
            title =data['title'] 
             
            Img_url=data['url'] 
            image_r = requests.get(Img_url) 
            FileName = str(date)+'.jpg' 
            with open(FileName,'wb') as f: 
                f.write(image_r.content) 
            path1="C:\\Users\\abc\\Desktop\\MY AI PROJECT\\"+str(FileName) 
            path2=""
            os.rename(path1,path2) 
            img=Image.open(path2) 
            img.show() 
            speak(title) 
            speak(f"According to nasa:{info}") 

def isstracker():
    """Track the International Space Station's current location"""
    try:
        # Get ISS location
        url = "http://api.open-notify.org/iss-now.json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Extract data
        timestamp = data['timestamp']
        lat = float(data['iss_position']['latitude'])
        lon = float(data['iss_position']['longitude'])
        
        # Convert timestamp to readable format
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
        
        # Get location info
        from geopy.geocoders import Nominatim
        geolocator = Nominatim(user_agent="voice_assistant")
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True)
        
        # Speak the information
        location_info = location.address if location else "over the ocean"
        speak(f"As of {dt}, the International Space Station is currently "
              f"at latitude {lat:.2f}, longitude {lon:.2f}, "
              f"which is near {location_info}.")
        
        # Create a map
        plt.figure(figsize=(10, 5))
        ax = plt.axes(projection=cart.PlateCarree())
        ax.stock_img()
        plt.scatter(lon, lat, color='red', marker='o', s=100, 
                   label='ISS Position', transform=cart.PlateCarree())
        plt.legend()
        plt.title(f"ISS Location - {dt}")
        
        # Save and show the map
        map_path = os.path.join(DATA_DIR, 'iss_location.png')
        plt.savefig(map_path)
        img = Image.open(map_path)
        img.show()
        
    except requests.RequestException as e:
        speak("Sorry, I couldn't connect to the ISS tracking service.")
    except Exception as e:
        speak(f"An error occurred while tracking the ISS: {str(e)}") 
 
def email_alert(subject, body, to, config_file=None):
    """Send an email using Gmail SMTP
    
    Args:
        subject (str): Email subject
        body (str): Email body
        to (str): Recipient email address
        config_file (str, optional): Path to config file with email credentials
    """
    try:
        # Default config file location
        if config_file is None:
            config_file = os.path.join(DATA_DIR, 'email_config.json')
        
        # Load email config
        if not os.path.exists(config_file):
            speak("Email configuration not found. Let's set it up.")
            email = input("Enter your Gmail address: ").strip()
            password = input("Enter your Gmail app password: ").strip()
            
            # Save config for future use
            config = {
                'email': email,
                'password': password
            }
            os.makedirs(os.path.dirname(config_file), exist_ok=True)
            with open(config_file, 'w') as f:
                json.dump(config, f)
        else:
            with open(config_file, 'r') as f:
                config = json.load(f)
        
        # Create message
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = config['email']
        msg['To'] = to
        
        # Send email
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(config['email'], config['password'])
            server.send_message(msg)
        
        speak(f"I've sent the email to {to}")
        return True
        
    except smtplib.SMTPAuthenticationError:
        speak("Authentication failed. Please check your email and password.")
        # Remove invalid config
        if os.path.exists(config_file):
            os.remove(config_file)
    except Exception as e:
        speak(f"Failed to send email: {str(e)}")
    
    return False 
 
def play_music(query=''):
    """Play music from the default music directory
    
    Args:
        query (str, optional): Optional search term for specific songs
    """
    try:
        # Check for default music directories
        music_dirs = [
            os.path.join(os.path.expanduser('~'), 'Music'),
            os.path.join(os.path.expanduser('~'), 'Downloads'),
            os.path.join(os.path.expanduser('~'), 'Desktop', 'music')
        ]
        
        # Find the first directory that exists and has music files
        music_dir = None
        songs = []
        
        for dir_path in music_dirs:
            if os.path.exists(dir_path):
                try:
                    files = [f for f in os.listdir(dir_path) 
                            if f.lower().endswith(('.mp3', '.wav', '.m4a', '.flac'))]
                    if files:
                        music_dir = dir_path
                        songs = files
                        break
                except Exception:
                    continue
        
        if not music_dir or not songs:
            speak("I couldn't find any music files in your default music directories.")
            return
            
        # If specific song is requested
        if query and 'play' in query.lower():
            search_term = query.lower().replace('play', '').strip()
            matching_songs = [s for s in songs if search_term in s.lower()]
            if matching_songs:
                song = random.choice(matching_songs)
                speak(f"Playing {os.path.splitext(song)[0]}")
                os.startfile(os.path.join(music_dir, song))
                return
        
        # Play a random song
        song = random.choice(songs)
        speak(f"Playing {os.path.splitext(song)[0]}")
        os.startfile(os.path.join(music_dir, song))
        
    except Exception as e:
        speak(f"Sorry, I couldn't play music: {str(e)}") 

def browser(query=''):
    """Open browser and optional search query
    
    Args:
        query (str, optional): Search query or URL to open
    """
    try:
        # Try to find the browser path
        browsers = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files\Mozilla Firefox\firefox.exe"
        ]
        
        browser_path = None
        for browser in browsers:
            if os.path.exists(browser):
                browser_path = browser
                break
                
        if not browser_path:
            speak("I couldn't find any web browser installed.")
            return
            
        if 'search' in query.lower():
            search_term = query.lower().replace('search', '').strip()
            if browser_path.endswith('msedge.exe'):
                os.startfile(f"microsoft-edge:https://www.bing.com/search?q={search_term}")
            else:
                os.startfile(f"https://www.google.com/search?q={search_term}")
        elif query and ('http://' in query or 'https://' in query):
            os.startfile(query)
        elif query:
            if browser_path.endswith('msedge.exe'):
                os.startfile(f"microsoft-edge:https://www.bing.com/search?q={query}")
            else:
                os.startfile(f"https://www.google.com/search?q={query}")
        else:
            os.startfile(browser_path)
            
    except Exception as e:
        speak(f"Sorry, I couldn't open the browser: {str(e)}") 
 
def handle_voice_command(command: VoiceCommand):
    """Handle incoming voice commands"""
    if not command or not command.text:
        return
        
    query = command.text.lower()
    
    try:
        # Process the command
        if 'youtube' in query:
            youtube(query)
        elif 'play music' in query:
            play_music()
        elif 'wikipedia' in query:
            speak('Searching Wikipedia...')
            results = wikipedia.summary(query, sentences=2)
            speak("According to Wikipedia" + results)
        elif 'search' in query:
            search_term = query.replace('search', '').strip()
            browser(f"https://www.google.com/search?q={search_term}")
        # Add more command handlers here
        
    except Exception as e:
        print(f"Error handling command: {e}")
        speak("Sorry, I had trouble processing that command.")

def search_wikipedia(query):
    """Search Wikipedia for information"""
    try:
        speak('Searching Wikipedia...')
        query = query.replace("wikipedia", "")
        results = wikipedia.summary(query, sentences=2)
        speak(f"According to Wikipedia: {results}")
    except Exception as e:
        print(f"Wikipedia search error: {e}")
        speak("I couldn't find any information on that topic.")

def search_web(query):
    """Search the web using default browser"""
    try:
        search_term = query.replace('search', '').strip()
        if search_term:
            url = f"https://www.google.com/search?q={search_term}"
            webbrowser.open(url)
            speak(f"Here's what I found for {search_term}")
    except Exception as e:
        print(f"Web search error: {e}")
        speak("I couldn't perform that web search.")

# Register the command handler
event_bus.subscribe(VoiceCommandEvent, handler=handle_voice_command)

if __name__ == "__main__":
    # Initialize components
    from voice_assistant.core.command_processor import command_processor
    from voice_assistant.core.voice_engine import voice_engine
    
    # Greet the user
    wish_me()
    
    try:
        # Start the voice engine in continuous listening mode
        print("Voice assistant is ready.")
        
        # Configure wake words
        wake_words = ["hey", "okay", "computer", "zero"]
        print(f"Say one of these to activate: {', '.join(wake_words)}")
        
        # Start continuous listening
        voice_engine.start_continuous_listening()
        
        # Keep the main thread alive
        try:
            while voice_engine.is_listening:
                time.sleep(0.5)
                
        except KeyboardInterrupt:
            print("\nShutting down...")
            
    except Exception as e:
        print(f"Fatal error: {e}")
        
    finally:
        # Clean up
        voice_engine.stop_continuous_listening()
        print("Voice assistant stopped.")