"""ChatGPT integration for handling unknown commands and providing intelligent responses."""
import os
import json
import logging
import requests
from typing import Dict, Any, Optional
from dataclasses import dataclass

from voice_assistant.config import config

logger = logging.getLogger(__name__)

@dataclass
class ChatGPTResponse:
    """Represents a response from ChatGPT"""
    text: str
    success: bool
    action: Optional[str] = None
    confidence: float = 1.0
    metadata: Dict[str, Any] = None

class ChatGPTHandler:
    """Handles interactions with ChatGPT API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-3.5-turbo"
        self.max_tokens = 150
        self.temperature = 0.7
        
        if not self.api_key:
            logger.warning("OpenAI API key not found. ChatGPT features will be disabled.")
    
    def process_command(self, text: str, context: Dict[str, Any] = None) -> ChatGPTResponse:
        """Process a command using ChatGPT"""
        if not self.api_key:
            return ChatGPTResponse(
                text="I'm sorry, I don't have access to ChatGPT right now. Please set up your OpenAI API key.",
                success=False
            )
        
        try:
            # Prepare the prompt
            system_prompt = """You are a helpful voice assistant. The user has given a command that I don't know how to handle.
            Please help me understand what they want and provide a helpful response. Consider:
            1. What is the user trying to do?
            2. What information do they need?
            3. What action should be taken?
            4. Are there any potential issues or clarifications needed?
            
            Respond in a concise, natural way that a voice assistant would speak."""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            # Make the API call
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            # Parse the response
            result = response.json()
            assistant_message = result['choices'][0]['message']['content']
            
            # Extract any potential action or metadata
            action = None
            metadata = {}
            
            # Try to parse any structured data in the response
            try:
                if "ACTION:" in assistant_message:
                    parts = assistant_message.split("ACTION:", 1)
                    assistant_message = parts[0].strip()
                    action = parts[1].strip()
                if "METADATA:" in assistant_message:
                    parts = assistant_message.split("METADATA:", 1)
                    assistant_message = parts[0].strip()
                    metadata = json.loads(parts[1].strip())
            except Exception as e:
                logger.warning(f"Error parsing ChatGPT response structure: {e}")
            
            return ChatGPTResponse(
                text=assistant_message,
                success=True,
                action=action,
                metadata=metadata
            )
            
        except Exception as e:
            logger.error(f"Error calling ChatGPT API: {e}")
            return ChatGPTResponse(
                text="I'm having trouble processing that request right now. Could you try again?",
                success=False,
                metadata={"error": str(e)}
            )
    
    def get_command_suggestion(self, text: str) -> ChatGPTResponse:
        """Get a suggestion for how to handle an unknown command"""
        try:
            system_prompt = """You are a voice assistant command analyzer. The user has given a command that I don't recognize.
            Please analyze the command and suggest:
            1. What type of command this might be
            2. What parameters or information might be needed
            3. A similar command that I do know how to handle
            4. Any potential issues or ambiguities
            
            Format your response as:
            COMMAND_TYPE: [type]
            SUGGESTED_COMMAND: [command]
            PARAMETERS: [parameters]
            ISSUES: [issues]
            RESPONSE: [natural language response]"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": messages,
                "max_tokens": 200,
                "temperature": 0.3
            }
            
            response = requests.post(self.api_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            suggestion = result['choices'][0]['message']['content']
            
            # Parse the structured response
            command_type = None
            suggested_command = None
            parameters = None
            issues = None
            response_text = None
            
            for line in suggestion.split('\n'):
                if line.startswith('COMMAND_TYPE:'):
                    command_type = line.split(':', 1)[1].strip()
                elif line.startswith('SUGGESTED_COMMAND:'):
                    suggested_command = line.split(':', 1)[1].strip()
                elif line.startswith('PARAMETERS:'):
                    parameters = line.split(':', 1)[1].strip()
                elif line.startswith('ISSUES:'):
                    issues = line.split(':', 1)[1].strip()
                elif line.startswith('RESPONSE:'):
                    response_text = line.split(':', 1)[1].strip()
            
            return ChatGPTResponse(
                text=response_text or suggestion,
                success=True,
                action=suggested_command,
                metadata={
                    "command_type": command_type,
                    "parameters": parameters,
                    "issues": issues
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting command suggestion: {e}")
            return ChatGPTResponse(
                text="I'm not sure how to handle that command. Could you try rephrasing it?",
                success=False,
                metadata={"error": str(e)}
            )

# Create a singleton instance
chatgpt_handler = ChatGPTHandler() 