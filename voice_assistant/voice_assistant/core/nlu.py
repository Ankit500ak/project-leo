import torch
import re
from dataclasses import dataclass
from typing import Dict, Any, Optional, List, Tuple
import logging
from enum import Enum

from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification
from voice_assistant.core.registry import register_nlu_engine

logger = logging.getLogger(__name__)

class IntentType(Enum):
    GREETING = "greeting"
    TIME = "time"
    DATE = "date"
    SEARCH = "search"
    YOUTUBE = "youtube"
    WEATHER = "weather"
    MUSIC = "music"
    EMAIL = "email"
    ALARM = "alarm"
    CALCULATE = "calculate"
    SYSTEM = "system"
    CHAT = "chat"
    UNKNOWN = "unknown"

@dataclass
class Intent:
    """Represents an identified user intent"""
    name: str
    confidence: float
    entities: Dict[str, str]
    context: Dict[str, Any] = None

    def __post_init__(self):
        if self.context is None:
            self.context = {}

class NLUEngine:
    """Enhanced Natural Language Understanding engine with hybrid rule-based and ML approaches"""
    
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._initialize_models()
        self._setup_intent_patterns()
        self._setup_entity_patterns()
    
    def _initialize_models(self):
        """Initialize ML models for intent classification and entity recognition"""
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-uncased")
            self.entity_model = AutoModelForTokenClassification.from_pretrained(
                "dbmdz/bert-large-cased-finetuned-conll03-english"
            )
            self.intent_model = AutoModelForSequenceClassification.from_pretrained(
                "facebook/bart-large-mnli"
            ).to(self.device)
            self.entity_model = self.entity_model.to(self.device)
        except Exception as e:
            logger.warning(f"Could not load ML models: {e}")
            self.ml_available = False
        else:
            self.ml_available = True
    
    def _setup_intent_patterns(self):
        """Setup patterns for intent detection"""
        self.intent_patterns = {
            IntentType.GREETING: [
                r"(hi|hello|hey|greetings|good (morning|afternoon|evening))\b",
                r"how(?:'s| is) it going",
                r"what's up"
            ],
            IntentType.TIME: [
                r"what(?:'s| is) the time",
                r"time(?: please)?\??",
                r"current time"
            ],
            IntentType.DATE: [
                r"what(?:'s| is) (?:the )?date",
                r"today'?s? date",
                r"current date"
            ],
            IntentType.SEARCH: [
                r"(search|look up|find)(?: (?:me|for))? (.+?)(?:\?|$)",
                r"(?:can you )?(?:please )?(?:search|find) (?:for )?(.+?)(?:\?|$)"
            ],
            IntentType.YOUTUBE: [
                # Open/launch patterns
                r"\b(?:open|launch|start|go to)\s+(?:the\s+)?(?:youtube|yt)\b",
                r"\b(?:youtube|yt)\s*(?:please)?\s*$",
                
                # Play/search patterns
                r"\b(?:play|search|find|watch|show\s+me)\s+(?:me\s+)?(?:a\s+)?(?:video\s+)?(?:on\s+)?(?:youtube|yt)\b(?:\s+(?:video\s+)?(?:about|of|for)\s+)?(.+?)(?:\?|$)",
                r"\b(?:youtube|yt)\s+(?:me\s+)?(?:a\s+)?(?:video\s+)?(?:about|of|for)\s+(.+?)(?:\?|$)",
                
                # More natural language patterns
                r"\b(?:can you\s+)?(?:please\s+)?(?:play|search|find|show|watch)(?:\s+me)?(?:\s+a)?(?:\s+video)?(?:\s+on)?(?:\s+youtube|\s+yt)?(?:\s+(?:called|named|titled|about))?\s+(.+?)(?:\?|$)",
                r"\b(?:i\s+)?(?:want\s+to\s+)?(?:watch|see|find|search\s+for)\s+(?:a\s+)?(?:video\s+)?(?:on\s+)?(?:youtube|yt)?(?:\s+about)?\s+(.+?)(?:\?|$)"
            ],
            IntentType.WEATHER: [
                r"(?:what'?s?|how'?s?) (?:the )?weather (?:like )?(?:in|at|for)?\s*(.+?)?(?:\?|$)",
                r"(?:weather|forecast)(?: in| at| for)?\s*(.+?)?(?:\?|$)"
            ],
            IntentType.SYSTEM: [
                r"\b(?:open|launch|start|run)\s+(?:me\s+)?(?:the\s+)?(.+?)(?:\?|$)",
                r"\b(?:can you\s+)?(?:please\s+)?(?:open|launch|start|run)(?:\s+the\s+)?(.+?)(?:\?|$)",
                r"\b(?:i\s+)?(?:want\s+to\s+)?(?:open|launch|start|run)(?:\s+the\s+)?(.+?)(?:\?|$)"
            ]
        }
    
    def _setup_entity_patterns(self):
        """Setup patterns for entity extraction"""
        self.entity_patterns = {
            'location': [
                r"(?:in|at|from|to|for)\s+(?:the\s+)?([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)",
                r"(?:location|place|city|town|country)\s+(?:of\s+)?([A-Z][A-Za-z]+(?:\s+[A-Z][A-Za-z]+)*)"
            ],
            'time': [
                r"(?:at|by|before|after)\s+(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)",
                r"(\d{1,2}(?::\d{2})?\s*(?:am|pm|AM|PM)?)\s+(?:o'?clock)?"
            ],
            'date': [
                r"(?:on\s+)?(\w+\s+\d{1,2}(?:st|nd|rd|th)?(?:\s*,\s*\d{4})?)",
                r"(?:on\s+)?(today|tomorrow|yesterday|next\s+\w+)"
            ]
        }
    
    def _match_intent(self, text: str) -> Tuple[IntentType, float, Dict[str, str]]:
        """Match text against intent patterns"""
        entities = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    # Extract entities from the match
                    if intent_type == IntentType.SEARCH and len(match.groups()) > 0:
                        entities['query'] = match.group(2 if len(match.groups()) > 1 else 1).strip()
                    elif intent_type == IntentType.YOUTUBE and len(match.groups()) > 0:
                        entities['query'] = match.group(1).strip()
                    elif intent_type == IntentType.WEATHER and len(match.groups()) > 0 and match.group(1):
                        entities['location'] = match.group(1).strip()
                    
                    # Higher confidence for more specific patterns
                    confidence = 0.8 + (0.1 * len(match.groups()))
                    return intent_type, min(confidence, 1.0), entities
        
        return IntentType.UNKNOWN, 0.0, {}
    
    def _extract_entities(self, text: str) -> Dict[str, str]:
        """Extract entities from text using patterns"""
        entities = {}
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match and match.group(1):
                    entities[entity_type] = match.group(1).strip()
        return entities
    
    def detect_intent(self, text: str) -> Optional[Intent]:
        """
        Detect the intent and entities from the given text.
        
        Args:
            text: Input text to analyze
            
        Returns:
            Intent object containing detected intent and entities, or None if text is empty
        """
        if not text or not text.strip():
            return None
            
        text = text.lower().strip()
        
        # First try pattern matching
        intent_type, confidence, entities = self._match_intent(text)
        
        # If no intent found or low confidence, try ML model if available
        if (intent_type == IntentType.UNKNOWN or confidence < 0.7) and self.ml_available:
            try:
                # Here you would add ML-based intent classification
                # For now, we'll just keep the pattern-based result
                pass
            except Exception as e:
                logger.warning(f"ML intent classification failed: {e}")
        
        # Extract additional entities
        entities.update(self._extract_entities(text))
        
        return Intent(
            name=intent_type.value,
            confidence=confidence,
            entities=entities
        )
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract named entities from text using BERT"""
        if not self.ml_available:
            return {}
            
        try:
            inputs = self.tokenizer(text, return_tensors="pt").to(self.device)
            outputs = self.entity_model(**inputs)
            predictions = torch.argmax(outputs.logits, dim=2)
            
            tokens = self.tokenizer.convert_ids_to_tokens(inputs["input_ids"][0])
            entities = []
            current_entity = None
            current_type = None
            
            for token, prediction in zip(tokens, predictions[0]):
                if token in ["[CLS]", "[SEP]", "[PAD]"]:
                    continue
                    
                if prediction != 0:  # 0 is 'O' (no entity)
                    entity_type = self.entity_model.config.id2label[prediction.item()]
                    if entity_type.startswith("B-"):
                        if current_entity:
                            entities.append((current_type[2:], " ".join(current_entity)))
                        current_entity = [token]
                        current_type = entity_type
                    elif entity_type.startswith("I-") and current_type[2:] == entity_type[2:]:
                        current_entity.append(token)
                    
            if current_entity:
                entities.append((current_type[2:], " ".join(current_entity)))
                
            return {entity_type: [entity for _, entity in entities if entity_type == entity_type] 
                    for entity_type, _ in entities}
            
        except Exception as e:
            logger.error(f"Error extracting entities: {e}")
            return {}
            
    def classify_intent(self, text: str) -> Intent:
        """Classify the intent of the given text using BART"""
        try:
            # Prepare input for BART
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            ).to(self.device)
            
            # Get model predictions
            outputs = self.intent_model(**inputs)
            logits = outputs.logits
            
            # Get probabilities
            probabilities = torch.softmax(logits, dim=1)
            max_prob, predicted_class = torch.max(probabilities, dim=1)
            
            # Map predicted class to intent
            intent = self.intent_categories[predicted_class.item()]
            confidence = max_prob.item()
            
            # Extract entities
            entities = self.extract_entities(text)
            
            return Intent(
                name=intent,
                confidence=confidence,
                entities=entities,
                context={
                    "raw_text": text,
                    "timestamp": time.time()
                }
            )
            
        except Exception as e:
            logger.error(f"Error classifying intent: {e}")
            return Intent(
                name="unknown",
                confidence=0.0,
                entities={},
                context={
                    "raw_text": text,
                    "timestamp": time.time()
                }
            )

# Create and register the NLU engine instance
nlu_engine = NLUEngine()
register_nlu_engine(nlu_engine)
