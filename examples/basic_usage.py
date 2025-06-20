#!/usr/bin/env python3
"""
AI Music Mixer - Basic Usage Examples
"""

from agent.orchestrator import create_music_mix, MusicMixerOrchestrator

def example_basic_mix():
    """Create a basic mix"""
    print("Creating a basic chill mix...")
    
    result = create_music_mix(
        prompt="Create a relaxing ambient mix perfect for studying",
        max_duration_minutes=5
    )
    
    if result['status'] == 'completed':
        print("✅ Mix created successfully!")
        print(f"Iterations: {result['iterations']}")
    else:
        print(f"❌ Failed: {result.get('error')}")

def example_custom_mix():
    """Create a custom mix with specific requirements"""
    print("Creating a custom energetic mix...")
    
    result = create_music_mix(
        prompt="""Create an energetic electronic dance mix with:
        - Progressive energy building from chill to intense
        - Seamless beat-matched transitions
        - Duration around 8 minutes
        - Perfect for a workout session""",
        max_duration_minutes=8
    )
    
    if result['status'] == 'completed':
        print("✅ Custom mix created!")
    else:
        print(f"❌ Failed: {result.get('error')}")

def example_suggestions():
    """Get mix suggestions"""
    print("Getting mix suggestions...")
    
    orchestrator = MusicMixerOrchestrator()
    suggestions = orchestrator.get_mix_suggestions(
        mood="energetic",
        genre="electronic",
        duration_minutes=6
    )
    
    print("Suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")

if __name__ == "__main__":
    # Run examples
    example_suggestions()
    print("\n" + "="*50 + "\n")
    
    example_basic_mix()
    print("\n" + "="*50 + "\n")
    
    example_custom_mix()