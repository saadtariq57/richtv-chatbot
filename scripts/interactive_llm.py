"""
Interactive LLM Testing Script

Direct, unfiltered access to the LLM for quality assessment.
No classification, no data fetching - just pure prompt-response interaction.

Usage:
    python scripts/interactive_llm.py
    
Commands:
    - Type your prompt and press Enter
    - 'temp X' to set temperature (e.g., 'temp 0.7')
    - 'clear' to clear screen
    - 'exit' or 'quit' to exit
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.llm.client import get_llm_client
import os


def clear_screen():
    """Clear the terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')


def print_banner():
    """Print welcome banner"""
    print("=" * 70)
    print("🤖 INTERACTIVE LLM TESTING")
    print("=" * 70)
    print("Direct access to your LLM for quality assessment")
    print("\nCommands:")
    print("  • Type your prompt and press Enter")
    print("  • 'temp X' - Set temperature (0.0-1.0, default: 0.7)")
    print("  • 'clear' - Clear screen")
    print("  • 'exit' or 'quit' - Exit")
    print("=" * 70)
    print()


def main():
    """Interactive REPL for LLM testing"""
    
    # Initialize LLM client
    try:
        llm = get_llm_client()
        print("✅ LLM client initialized successfully")
        print(f"📡 Model: {llm.model}")
        print()
    except Exception as e:
        print(f"❌ Error initializing LLM client: {e}")
        print("\nPlease check your .env file and API key configuration.")
        return
    
    # Default temperature
    temperature = 0.7
    
    print_banner()
    print(f"Current temperature: {temperature}")
    print()
    
    # Main loop
    while True:
        try:
            # Get user input
            prompt = input("💬 You: ").strip()
            
            # Handle empty input
            if not prompt:
                continue
            
            # Handle commands
            if prompt.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            elif prompt.lower() == 'clear':
                clear_screen()
                print_banner()
                print(f"Current temperature: {temperature}")
                print()
                continue
            
            elif prompt.lower().startswith('temp '):
                try:
                    new_temp = float(prompt.split()[1])
                    if 0.0 <= new_temp <= 1.0:
                        temperature = new_temp
                        print(f"✅ Temperature set to {temperature}")
                    else:
                        print("⚠️  Temperature must be between 0.0 and 1.0")
                except (ValueError, IndexError):
                    print("⚠️  Usage: temp 0.7")
                print()
                continue
            
            # Call LLM
            print("\n🤔 Thinking...\n")
            
            response = llm.generate(prompt, temperature=temperature)
            
            if response:
                print("🤖 LLM Response:")
                print("-" * 70)
                print(response)
                print("-" * 70)
            else:
                print("❌ No response from LLM (check API key or network)")
            
            print()
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print()


if __name__ == "__main__":
    main()

