#!/usr/bin/env python3
"""
AI Music Mixer - Command Line Interface
"""

import argparse
import sys
import os
from typing import Optional
import json
from config import Config
from agent.orchestrator import MusicMixerOrchestrator, create_music_mix

def main():
    parser = argparse.ArgumentParser(
        description="AI Music Mixer - Create amazing music mixes using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Create a dreamy ambient mix for sunset"
  %(prog)s "Upbeat electronic mix for workout" --duration 8
  %(prog)s --suggest --mood "chill" --genre "lofi"
  %(prog)s --interactive
        """
    )
    
    # Main arguments
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Description of the mix you want to create"
    )
    
    parser.add_argument(
        "--duration",
        type=int,
        default=6,
        help="Target mix duration in minutes (default: 6)"
    )
    
    parser.add_argument(
        "--output-dir",
        default=Config.EXPORTS_DIR,
        help=f"Output directory for exports (default: {Config.EXPORTS_DIR})"
    )
    
    # Interactive mode
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Run in interactive mode"
    )
    
    # Suggestions
    parser.add_argument(
        "--suggest",
        action="store_true",
        help="Get mix prompt suggestions"
    )
    
    parser.add_argument(
        "--mood",
        help="Mood for suggestions (e.g., 'chill', 'energetic', 'dark')"
    )
    
    parser.add_argument(
        "--genre",
        help="Genre for suggestions (e.g., 'electronic', 'ambient', 'hip-hop')"
    )
    
    # Configuration
    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run initial setup and configuration"
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="AI Music Mixer v1.0"
    )
    
    args = parser.parse_args()
    
    # Check if setup is needed
    if args.setup or not Config.OPENAI_API_KEY:
        run_setup()
        return
    
    # Handle different modes
    if args.suggest:
        run_suggestions(args.mood or "chill", args.genre or "", args.duration)
    elif args.interactive:
        run_interactive_mode()
    elif args.prompt:
        run_single_mix(args.prompt, args.duration)
    else:
        parser.print_help()

def run_setup():
    """Run initial setup"""
    print("🎵 AI Music Mixer Setup")
    print("=" * 50)
    
    # Check for .env file
    env_file = ".env"
    if not os.path.exists(env_file):
        print("Creating .env file...")
        with open(env_file, "w") as f:
            f.write("# AI Music Mixer Configuration\n")
            f.write("OPENAI_API_KEY=your_openai_api_key_here\n")
            f.write("JAMENDO_CLIENT_ID=your_jamendo_client_id_here\n")
            f.write("FREESOUND_API_KEY=your_freesound_api_key_here\n")
    
    print(f"Please edit {env_file} and add your API keys:")
    print("1. OpenAI API Key (required) - https://platform.openai.com/api-keys")
    print("2. Jamendo Client ID (optional) - https://developer.jamendo.com/")
    print("3. Freesound API Key (optional) - https://freesound.org/apiv2/")
    print()
    print("After adding your keys, run the mixer again!")
    
    # Create directories
    Config.ensure_directories()
    print(f"Created directories: {Config.MUSIC_DIR}, {Config.EXPORTS_DIR}, {Config.TEMP_DIR}")

def run_suggestions(mood: str, genre: str, duration: int):
    """Generate mix suggestions"""
    print(f"🎵 Mix Suggestions for {mood} {genre}".strip())
    print("=" * 50)
    
    try:
        orchestrator = MusicMixerOrchestrator()
        suggestions = orchestrator.get_mix_suggestions(mood, genre, duration)
        
        for i, suggestion in enumerate(suggestions, 1):
            print(f"{i}. {suggestion}")
        
        print("\nUse any of these prompts with:")
        print(f'python cli.py "your chosen prompt"')
        
    except Exception as e:
        print(f"❌ Error generating suggestions: {e}")

def run_interactive_mode():
    """Run interactive mode"""
    print("🎵 AI Music Mixer - Interactive Mode")
    print("=" * 50)
    print("Type 'quit' to exit, 'help' for commands")
    print()
    
    orchestrator = MusicMixerOrchestrator()
    
    while True:
        try:
            prompt = input("🎵 Describe your mix: ").strip()
            
            if prompt.lower() in ['quit', 'exit', 'q']:
                print("Goodbye! 🎵")
                break
            elif prompt.lower() == 'help':
                print_help()
                continue
            elif not prompt:
                continue
            
            # Ask for duration
            duration_input = input("⏱️  Duration in minutes (default 6): ").strip()
            try:
                duration = int(duration_input) if duration_input else 6
            except ValueError:
                duration = 6
            
            print(f"\n🚀 Creating mix: '{prompt}'")
            print("This may take a few minutes...")
            
            result = create_music_mix(prompt, duration)
            
            if result.get('status') == 'completed':
                print("✅ Mix created successfully!")
                print(f"Check the {Config.EXPORTS_DIR} directory for your mix.")
            else:
                print(f"❌ Mix creation failed: {result.get('error', 'Unknown error')}")
            
            print("\n" + "="*50)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye! 🎵")
            break
        except Exception as e:
            print(f"❌ Error: {e}")

def run_single_mix(prompt: str, duration: int):
    """Create a single mix"""
    print(f"🎵 Creating Mix: '{prompt}'")
    print(f"⏱️  Target Duration: {duration} minutes")
    print("=" * 50)
    print("This may take a few minutes...")
    print()
    
    try:
        result = create_music_mix(prompt, duration)
        
        if result.get('status') == 'completed':
            print("✅ Mix created successfully!")
            print(f"📁 Check the {Config.EXPORTS_DIR} directory for your mix.")
            print(f"🔄 Completed in {result.get('iterations', 0)} AI iterations")
            
            # Show final response if available
            if result.get('final_response'):
                print(f"\n🤖 AI Summary:")
                print(result['final_response'])
        else:
            print(f"❌ Mix creation failed")
            if result.get('error'):
                print(f"Error: {result['error']}")
            
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)

def print_help():
    """Print interactive mode help"""
    print("""
Interactive Mode Commands:
- Just type your mix description and press Enter
- 'quit' or 'q' - Exit the program
- 'help' - Show this help message

Example prompts:
- "Create a chill lofi mix for studying"
- "Upbeat electronic dance mix"
- "Ambient space music for relaxation"
- "Progressive house mix with building energy"
    """)

if __name__ == "__main__":
    main()