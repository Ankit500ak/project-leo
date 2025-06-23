"""
Test script to verify all voice assistant commands are registered correctly.
"""
import sys
import os
import io
import sys
from pathlib import Path

# Configure console output to handle Unicode
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add the project root to the Python path
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from voice_assistant.core import command_processor

def test_command_registration():
    """Test that all commands are registered correctly."""
    print("\n=== Testing Command Registration ===\n")
    
    # Get all registered commands
    commands = command_processor.list_commands()
    
    if not commands:
        print("❌ No commands found! Something is wrong with the registration.")
        return False
    
    print(f"✅ Found {len(commands)} registered commands:")
    
    # Group commands by category for better readability
    categories = {}
    for cmd in commands:
        category = cmd.get('category', 'Uncategorized')
        if category not in categories:
            categories[category] = []
        categories[category].append(cmd)
    
    # Print commands by category
    for category, cmds in categories.items():
        print(f"\n📁 {category}:")
        print("-" * (len(category) + 2))
        for cmd in sorted(cmds, key=lambda x: x['name']):
            patterns = ", ".join(f'"{p}"' for p in cmd.get('patterns', [])[:2])
            if len(cmd.get('patterns', [])) > 2:
                patterns += f", ... ({len(cmd['patterns']) - 2} more)"
            
            print(f"• {cmd['name']}")
            print(f"  Description: {cmd.get('description', 'No description')}")
            print(f"  Patterns: {patterns}")
            if cmd.get('requires_wake_word') is False:
                print("  ⚡ No wake word required")
            if cmd.get('admin_only'):
                print("  🔒 Admin only")
            print()
    
    return True

if __name__ == "__main__":
    print("Starting command registration test...")
    success = test_command_registration()
    
    if success:
        print("\n✅ Command registration test completed successfully!")
    else:
        print("\n❌ Command registration test failed!")
    
    print("\nYou can now try saying commands like:")
    print("• 'Hey, what time is it?'")
    print("• 'Search for Python programming'")
    print("• 'Open YouTube'")
    print("• 'Tell me a joke'")
    print("• 'System info'")
    print("\nSay 'help' to see all available commands.")
