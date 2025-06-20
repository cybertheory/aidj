import json
from typing import Dict, List, Optional, Any
from openai import OpenAI
from config import Config

# Import all tools
from tools.music_discovery import music_discovery_tool
from tools.audio_analysis import audio_analysis_tool, batch_audio_analysis_tool
from tools.mix_generation import mix_generation_tool
from tools.iterative_feedback import iterative_feedback_tool, iterative_improvement_tool
from tools.final_export import final_mix_export_tool, create_mix_package_tool

class MusicMixerOrchestrator:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.tools = self._define_tools()
        self.conversation_history = []
        
    def _define_tools(self) -> List[Dict]:
        """Define all available tools for the LLM"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "music_discovery_tool",
                    "description": "Searches for royalty-free songs using keywords and downloads MP3s",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "Search query for music (e.g., 'ambient dreamy', 'upbeat electronic')"},
                            "duration_min": {"type": "integer", "description": "Minimum track duration in seconds", "default": 60},
                            "duration_max": {"type": "integer", "description": "Maximum track duration in seconds", "default": 300},
                            "max_tracks": {"type": "integer", "description": "Maximum number of tracks to download", "default": 5}
                        },
                        "required": ["query"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "batch_audio_analysis_tool",
                    "description": "Analyzes multiple music files for tempo, key, mood, and mixing points",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array", 
                                "items": {"type": "string"}, 
                                "description": "List of audio file paths to analyze"
                            }
                        },
                        "required": ["file_paths"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "mix_generation_tool",
                    "description": "Generates a music mix using PyDub with various transition types",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_paths": {
                                "type": "array", 
                                "items": {"type": "string"}, 
                                "description": "List of audio files to mix"
                            },
                            "analyses": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "file_path": {"type": "string"},
                                        "duration": {"type": "number"},
                                        "tempo": {"type": "number"},
                                        "estimated_key": {"type": "string"},
                                        "energy_level": {"type": "string"},
                                        "mood": {"type": "string"},
                                        "mixing_metadata": {"type": "object"}
                                    }
                                },
                                "description": "Audio analysis results for each file"
                            },
                            "transition_type": {
                                "type": "string", 
                                "enum": ["crossfade", "beat_match", "simple"], 
                                "default": "crossfade"
                            },
                            "fade_duration_ms": {
                                "type": "integer", 
                                "description": "Fade duration in milliseconds", 
                                "default": 3000
                            },
                            "mix_style": {
                                "type": "string", 
                                "enum": ["seamless", "energetic", "basic"], 
                                "default": "seamless"
                            },
                            "target_duration_ms": {
                                "type": "integer", 
                                "description": "Target mix duration in milliseconds (optional)"
                            }
                        },
                        "required": ["file_paths", "analyses"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "iterative_improvement_tool",
                    "description": "Gets AI feedback on a mix and applies improvements iteratively",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the mix file to analyze"},
                            "prompt": {"type": "string", "description": "Original user prompt/request for the mix"},
                            "mix_metadata": {
                                "type": "object", 
                                "description": "Metadata about the mix",
                                "properties": {
                                    "transition_type": {"type": "string"},
                                    "fade_duration_ms": {"type": "integer"},
                                    "mix_style": {"type": "string"},
                                    "final_bpm": {"type": "number"},
                                    "energy_progression": {"type": "array", "items": {"type": "string"}}
                                }
                            },
                            "max_iterations": {"type": "integer", "description": "Maximum improvement iterations", "default": 3}
                        },
                        "required": ["file_path", "prompt", "mix_metadata"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "final_mix_export_tool",
                    "description": "Exports the final mix with metadata and proper file organization",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {"type": "string", "description": "Path to the mix file to export"},
                            "title": {"type": "string", "description": "Title for the mix"},
                            "metadata": {
                                "type": "object", 
                                "description": "Mix metadata including BPM, genre, etc.",
                                "properties": {
                                    "bpm": {"type": "number"},
                                    "genre": {"type": "string"},
                                    "vibe": {"type": "string"},
                                    "tracks_used": {"type": "integer"},
                                    "mix_style": {"type": "string"},
                                    "pydub_code": {"type": "string"}
                                }
                            },
                            "export_format": {"type": "string", "enum": ["mp3", "wav"], "default": "mp3"},
                            "bitrate": {"type": "string", "description": "Audio bitrate", "default": "320k"}
                        },
                        "required": ["file_path", "title", "metadata"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_mix_package_tool",
                    "description": "Creates a complete package with mix file, report, and script",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "export_result": {
                                "type": "object", 
                                "description": "Result from final_mix_export_tool",
                                "properties": {
                                    "status": {"type": "string"},
                                    "export_path": {"type": "string"},
                                    "report_path": {"type": "string"},
                                    "script_path": {"type": "string"},
                                    "metadata": {"type": "object"}
                                }
                            },
                            "include_source_files": {"type": "boolean", "description": "Whether to include source audio files", "default": False}
                        },
                        "required": ["export_result"]
                    }
                }
            }
        ]
    
    def _execute_tool(self, tool_name: str, arguments: Dict) -> Any:
        """Execute a tool function with given arguments"""
        tool_functions = {
            "music_discovery_tool": music_discovery_tool,
            "batch_audio_analysis_tool": batch_audio_analysis_tool,
            "mix_generation_tool": mix_generation_tool,
            "iterative_improvement_tool": iterative_improvement_tool,
            "final_mix_export_tool": final_mix_export_tool,
            "create_mix_package_tool": create_mix_package_tool
        }
        
        if tool_name not in tool_functions:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            return tool_functions[tool_name](**arguments)
        except Exception as e:
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def create_mix(self, user_prompt: str, max_duration_minutes: int = 10) -> Dict:
        """Main orchestration function to create a mix from user prompt"""
        
        print(f"🎵 Starting mix creation for: '{user_prompt}'")
        
        # Initialize conversation
        system_prompt = """You are an expert AI music producer and DJ. Your job is to create amazing music mixes based on user requests using the available tools.

Your workflow should be:
1. Analyze the user's request to understand the desired mood, genre, energy, and style
2. Use music_discovery_tool to find appropriate royalty-free tracks
3. Use batch_audio_analysis_tool to analyze the downloaded tracks
4. Use mix_generation_tool to create an initial mix
5. Use iterative_improvement_tool to get feedback and improve the mix
6. Use final_mix_export_tool to export the final result
7. Use create_mix_package_tool to create a complete package

Be creative and thoughtful about track selection, transitions, and overall flow. Consider energy progression, key compatibility, and mood consistency."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Create a music mix based on this request: {user_prompt}. Target duration should be around {max_duration_minutes} minutes."}
        ]
        
        max_iterations = 10
        iteration = 0
        
        while iteration < max_iterations:
            try:
                print(f"\n🤖 AI Agent - Iteration {iteration + 1}")
                
                response = self.client.chat.completions.create(
                    model="gpt-4",
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.7,
                    max_tokens=2000
                )
                
                message = response.choices[0].message
                messages.append(message)
                
                # Check if the assistant wants to use tools
                if message.tool_calls:
                    print(f"🔧 Executing {len(message.tool_calls)} tool(s)...")
                    
                    for tool_call in message.tool_calls:
                        tool_name = tool_call.function.name
                        arguments = json.loads(tool_call.function.arguments)
                        
                        print(f"   → {tool_name}({', '.join(f'{k}={v}' for k, v in arguments.items() if k != 'analyses')})")
                        
                        # Execute the tool
                        result = self._execute_tool(tool_name, arguments)
                        
                        # Add tool result to conversation
                        tool_message = {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result, default=str)
                        }
                        messages.append(tool_message)
                        
                        # Print result summary
                        if isinstance(result, dict):
                            if result.get('status') == 'success':
                                print(f"   ✅ {tool_name} completed successfully")
                            elif 'error' in result:
                                print(f"   ❌ {tool_name} failed: {result['error']}")
                            else:
                                print(f"   ℹ️  {tool_name} completed")
                
                else:
                    # No more tools to call, check if we have a final result
                    final_response = message.content
                    print(f"\n🎉 Mix creation completed!")
                    print(f"Final response: {final_response}")
                    
                    return {
                        "status": "completed",
                        "final_response": final_response,
                        "conversation_history": messages,
                        "iterations": iteration + 1
                    }
                
                iteration += 1
                
            except Exception as e:
                print(f"❌ Error in orchestration: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "conversation_history": messages,
                    "iterations": iteration
                }
        
        return {
            "status": "max_iterations_reached",
            "conversation_history": messages,
            "iterations": iteration
        }
    
    def get_mix_suggestions(self, mood: str, genre: str = "", duration_minutes: int = 5) -> List[str]:
        """Get AI suggestions for mix prompts"""
        
        prompt = f"""Generate 5 creative music mix prompts for:
- Mood: {mood}
- Genre: {genre if genre else 'any'}
- Duration: ~{duration_minutes} minutes

Each prompt should be specific and inspiring, mentioning energy flow, transitions, and vibe.
Return as a JSON list of strings."""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative music curator. Generate inspiring mix prompts."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            content = response.choices[0].message.content
            
            # Try to extract JSON
            import re
            json_match = re.search(r'\[.*\]', content, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                return suggestions
            else:
                # Fallback: split by lines
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                return lines[:5]
                
        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return [
                f"Create a {mood} mix with smooth transitions",
                f"Build a {duration_minutes}-minute journey through {mood} vibes",
                f"Mix {mood} tracks with perfect energy flow",
                f"Craft a {mood} atmosphere with seamless blending",
                f"Design a {mood} experience with dynamic progression"
            ]

# Convenience function for direct usage
def create_music_mix(prompt: str, max_duration_minutes: int = 10) -> Dict:
    """Create a music mix from a text prompt"""
    Config.ensure_directories()
    orchestrator = MusicMixerOrchestrator()
    return orchestrator.create_mix(prompt, max_duration_minutes)