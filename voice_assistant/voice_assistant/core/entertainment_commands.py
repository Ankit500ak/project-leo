"""Entertainment and fun commands for the voice assistant."""
import random
import pyjokes
import webbrowser
from typing import Dict, Any

from voice_assistant.core.registry import get_voice_engine
from voice_assistant.core.builtin_commands import command

voice_engine = get_voice_engine()

# List of fun facts
FUN_FACTS = [
    "Honey never spoils. Archaeologists have found pots of honey in ancient Egyptian tombs that are over 3,000 years old and still perfectly good to eat.",
    "Octopuses have three hearts.",
    "A group of flamingos is called a 'flamboyance'.",
    "The shortest war in history was between Britain and Zanzibar on August 27, 1896. Zanzibar surrendered after 38 minutes.",
    "A day on Venus is longer than a year on Venus.",
    "Bananas are berries, but strawberries aren't.",
    "The inventor of the frisbee was turned into a frisbee after he died.",
    "Some cats are allergic to humans.",
    "The unicorn is the national animal of Scotland.",
    "There's a species of jellyfish that is biologically immortal."
]

# List of would you rather questions
WOULD_YOU_RATHER = [
    "Would you rather be able to fly or be invisible?",
    "Would you rather have unlimited money or unlimited time?",
    "Would you rather be able to speak all languages or be able to talk to animals?",
    "Would you rather always be 10 minutes late or always be 20 minutes early?",
    "Would you rather be famous when you are alive and forgotten when you die, or unknown when you're alive but famous after you die?",
    "Would you rather have a rewind button or a pause button in your life?",
    "Would you rather be able to read minds or be able to predict the future?",
    "Would you rather be able to breathe underwater or fly?",
    "Would you rather be a genius and unhappy or less intelligent but happy?",
    "Would you rather always have to say everything on your mind or never speak again?"
]

@command(
    name="fun_fact",
    description="Tell a random fun fact",
    patterns=["tell me a fun fact", "give me an interesting fact", "fun fact"]
)
def fun_fact() -> Dict[str, Any]:
    """Tell a random fun fact."""
    fact = random.choice(FUN_FACTS)
    voice_engine.speak(fact)
    return {"status": "success", "fact": fact}

@command(
    name="play_game",
    description="Play a simple game",
    patterns=["let's play a game", "play a game", "I want to play"]
)
def play_game() -> Dict[str, Any]:
    """Start a simple interactive game."""
    games = ["rock paper scissors", "number guessing game", "trivia quiz"]
    game = random.choice(games)
    
    if game == "rock paper scissors":
        return play_rock_paper_scissors()
    elif game == "number guessing game":
        return play_number_guessing()
    else:
        return play_trivia()

def play_rock_paper_scissors() -> Dict[str, Any]:
    """Play Rock, Paper, Scissors."""
    choices = ["rock", "paper", "scissors"]
    voice_engine.speak("Let's play Rock, Paper, Scissors! Choose rock, paper, or scissors.")
    
    # In a real implementation, you would listen for the user's choice
    # For now, we'll simulate a choice
    user_choice = "rock"  # This would come from voice recognition
    computer_choice = random.choice(choices)
    
    voice_engine.speak(f"I chose {computer_choice}.")
    
    if user_choice == computer_choice:
        voice_engine.speak("It's a tie!")
        result = "tie"
    elif (
        (user_choice == "rock" and computer_choice == "scissors") or
        (user_choice == "paper" and computer_choice == "rock") or
        (user_choice == "scissors" and computer_choice == "paper")
    ):
        voice_engine.speak("You win!")
        result = "win"
    else:
        voice_engine.speak("I win!")
        result = "lose"
    
    return {
        "status": "success",
        "game": "rock_paper_scissors",
        "user_choice": user_choice,
        "computer_choice": computer_choice,
        "result": result
    }

def play_number_guessing() -> Dict[str, Any]:
    """Play a number guessing game."""
    number = random.randint(1, 100)
    attempts = 0
    max_attempts = 7
    
    voice_engine.speak("I'm thinking of a number between 1 and 100. Can you guess what it is?")
    
    # In a real implementation, you would listen for the user's guess
    # For now, we'll simulate a guess
    user_guess = 50  # This would come from voice recognition
    
    while attempts < max_attempts:
        attempts += 1
        
        if user_guess < number:
            voice_engine.speak("Too low! Try again.")
        elif user_guess > number:
            voice_engine.speak("Too high! Try again.")
        else:
            voice_engine.speak(f"Congratulations! You guessed the number in {attempts} attempts!")
            return {
                "status": "success",
                "game": "number_guessing",
                "number": number,
                "attempts": attempts,
                "result": "win"
            }
    
    voice_engine.speak(f"Game over! The number was {number}.")
    return {
        "status": "success",
        "game": "number_guessing",
        "number": number,
        "attempts": attempts,
        "result": "lose"
    }

def play_trivia() -> Dict[str, Any]:
    """Play a simple trivia game."""
    questions = [
        {
            "question": "What is the capital of France?",
            "answer": "Paris"
        },
        {
            "question": "Which planet is known as the Red Planet?",
            "answer": "Mars"
        },
        {
            "question": "What is the largest mammal in the world?",
            "answer": "Blue Whale"
        },
        {
            "question": "What is the chemical symbol for gold?",
            "answer": "Au"
        },
        {
            "question": "Who painted the Mona Lisa?",
            "answer": "Leonardo da Vinci"
        }
    ]
    
    question = random.choice(questions)
    voice_engine.speak(question["question"])
    
    # In a real implementation, you would listen for the user's answer
    # For now, we'll simulate an answer
    user_answer = "Paris"  # This would come from voice recognition
    
    if user_answer.lower() == question["answer"].lower():
        voice_engine.speak("Correct! Well done!")
        result = "correct"
    else:
        voice_engine.speak(f"Incorrect. The correct answer is {question['answer']}.")
        result = "incorrect"
    
    return {
        "status": "success",
        "game": "trivia",
        "question": question["question"],
        "correct_answer": question["answer"],
        "user_answer": user_answer,
        "result": result
    }

@command(
    name="would_you_rather",
    description="Ask a 'would you rather' question",
    patterns=["would you rather", "ask me a question", "give me a dilemma"]
)
def would_you_rather() -> Dict[str, Any]:
    """Ask a 'would you rather' question."""
    question = random.choice(WOULD_YOU_RATHER)
    voice_engine.speak(question)
    return {
        "status": "success",
        "question": question,
        "type": "would_you_rather"
    }

@command(
    name="tell_story",
    description="Tell a short story",
    patterns=["tell me a story", "tell me a short story", "tell me a bedtime story"]
)
def tell_story() -> Dict[str, Any]:
    """Tell a short story."""
    stories = [
        "Once upon a time, in a land far, far away, there was a brave little robot who dreamed of exploring the stars. "
        "One day, it built a spaceship from old computer parts and set off on an adventure across the galaxy.",
        
        "There was once a wise old owl who lived in an enchanted forest. All the animals would come to the owl for advice, "
        "but the owl's best wisdom came from simply listening to others.",
        
        "In a small village by the sea, there was a young girl who could talk to dolphins. Together, they would explore the "
        "ocean and discover hidden treasures beneath the waves.",
        
        "Long ago, in a kingdom where music was magic, a young musician discovered a mysterious instrument that could control "
        "the weather. With each note, they could summon rain or sunshine, creating beautiful melodies that shaped the world around them."
    ]
    
    story = random.choice(stories)
    voice_engine.speak(story)
    return {
        "status": "success",
        "story": story,
        "length": len(story.split())
    }

@command(
    name="roll_dice",
    description="Roll a die with specified number of sides",
    patterns=["roll a d*", "roll a * sided die", "roll *"]
)
def roll_dice(sides: str = "6") -> Dict[str, Any]:
    """
    Roll a die with the specified number of sides.
    
    Args:
        sides: Number of sides on the die (default: 6)
        
    Returns:
        Dict with status and the result of the roll
    """
    try:
        # Extract number from patterns like "roll a d20" or "roll a 6 sided die"
        if sides.startswith('d'):
            sides = sides[1:]
        if ' ' in sides:
            sides = sides.split()[0]
            
        sides = int(sides) if sides.isdigit() else 6
        result = random.randint(1, sides)
        
        voice_engine.speak(f"You rolled a {result} on a {sides}-sided die!")
        return {
            "status": "success",
            "result": result,
            "sides": sides
        }
    except Exception as e:
        logger.error(f"Error rolling die: {e}")
        voice_engine.speak("I couldn't roll the die. Let's try a standard six-sided die.")
        result = random.randint(1, 6)
        return {
            "status": "success",
            "result": result,
            "sides": 6,
            "error": str(e)
        }

@command(
    name="flip_coin",
    description="Flip a coin",
    patterns=["flip a coin", "toss a coin", "heads or tails"]
)
def flip_coin() -> Dict[str, Any]:
    """
    Flip a coin and return the result.
    
    Returns:
        Dict with status and the result (heads or tails)
    """
    result = random.choice(["heads", "tails"])
    voice_engine.speak(f"It's {result}!")
    return {
        "status": "success",
        "result": result
    }

@command(
    name="magic_8_ball",
    description="Ask the magic 8-ball a question",
    patterns=["magic 8 ball *", "should i *", "will i *", "can i *"]
)
def magic_8_ball(question: str = None) -> Dict[str, Any]:
    """
    Answer a yes/no question with a magic 8-ball response.
    
    Args:
        question: The question to ask (optional)
        
    Returns:
        Dict with status and the 8-ball's response
    """
    responses = [
        "It is certain.",
        "It is decidedly so.",
        "Without a doubt.",
        "Yes, definitely.",
        "You may rely on it.",
        "As I see it, yes.",
        "Most likely.",
        "Outlook good.",
        "Yes.",
        "Signs point to yes.",
        "Reply hazy, try again.",
        "Ask again later.",
        "Better not tell you now.",
        "Cannot predict now.",
        "Concentrate and ask again.",
        "Don't count on it.",
        "My reply is no.",
        "My sources say no.",
        "Outlook not so good.",
        "Very doubtful."
    ]
    
    response = random.choice(responses)
    voice_engine.speak(response)
    
    return {
        "status": "success",
        "question": question,
        "response": response
    }
