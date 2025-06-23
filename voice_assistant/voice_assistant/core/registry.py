"""
Registry for core components to avoid circular imports.

This module provides a central registry for core components that need to be
accessed from multiple modules, helping to avoid circular imports.
"""

# These will be set when the respective components are created
_command_processor = None
_voice_engine = None
_nlu_engine = None

def register_command_processor(processor):
    """Register the command processor instance."""
    global _command_processor
    _command_processor = processor

def register_voice_engine(engine):
    """Register the voice engine instance."""
    global _voice_engine
    _voice_engine = engine

def register_nlu_engine(engine):
    """Register the NLU engine instance."""
    global _nlu_engine
    _nlu_engine = engine

def get_command_processor():
    """Get the registered command processor instance."""
    return _command_processor

def get_voice_engine():
    """Get the registered voice engine instance."""
    return _voice_engine

def get_nlu_engine():
    """Get the registered NLU engine instance."""
    return _nlu_engine

# For backward compatibility
command_processor = property(get_command_processor)
voice_engine = property(get_voice_engine)
nlu_engine = property(get_nlu_engine)
