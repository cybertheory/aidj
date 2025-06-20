import openai
import os
import json
import base64
from typing import Dict, List, Optional
import asyncio
import aiohttp
from pydub import AudioSegment
from pydub.effects import normalize
from config import Config

class IterativeFeedbackTool:
    def __init__(self):
        self.client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        
    def encode_audio_to_base64(self, file_path: str) -> str:
        """Encode audio file to base64 for API transmission"""
        try:
            with open(file_path, "rb") as audio_file:
                return base64.b64encode(audio_file.read()).decode('utf-8')
        except Exception as e:
            print(f"Error encoding audio: {e}")
            return ""
    
    def get_mix_feedback(self, file_path: str, prompt: str, mix_metadata: Optional[Dict] = None) -> Dict:
        """Get feedback on mix using GPT-4 with audio analysis"""
        
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        try:
            # Prepare context about the mix
            context = f"""
            You are an expert music producer and DJ reviewing an AI-generated music mix.
            
            Mix Request: {prompt}
            
            Mix Metadata:
            {json.dumps(mix_metadata, indent=2) if mix_metadata else "No metadata available"}
            
            Please analyze this mix and provide structured feedback in JSON format with the following structure:
            {{
                "overall_rating": 1-10,
                "matches_request": true/false,
                "feedback": "detailed feedback text",
                "specific_issues": [
                    {{"timestamp_ms": 0, "issue": "description", "severity": "low/medium/high"}}
                ],
                "suggestions": [
                    {{"action": "trim/volume_adjust/eq/crossfade", "parameters": {{}}, "reason": "explanation"}}
                ],
                "energy_flow": "description of energy progression",
                "transition_quality": "assessment of transitions",
                "technical_issues": ["list of technical problems"],
                "creative_suggestions": ["list of creative improvements"]
            }}
            
            Focus on:
            1. How well the mix matches the original request
            2. Quality of transitions between tracks
            3. Energy flow and progression
            4. Technical audio quality
            5. Creative and artistic elements
            6. Specific actionable improvements
            """
            
            # For now, we'll use text-based analysis since audio input to GPT-4 is limited
            # In a production system, you might use Whisper for transcription or other audio analysis
            
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert music producer and DJ providing detailed feedback on music mixes."
                    },
                    {
                        "role": "user",
                        "content": context + f"\n\nMix file: {os.path.basename(file_path)}\nDuration: {self._get_audio_duration(file_path)} seconds"
                    }
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            feedback_text = response.choices[0].message.content
            
            # Try to parse JSON from response
            try:
                json_start = feedback_text.find('{')
                json_end = feedback_text.rfind('}') + 1
                if json_start != -1 and json_end != -1:
                    feedback_json = json.loads(feedback_text[json_start:json_end])
                    
                    # Ensure overall_rating is an integer
                    if 'overall_rating' in feedback_json:
                        try:
                            feedback_json['overall_rating'] = int(feedback_json['overall_rating'])
                        except (ValueError, TypeError):
                            feedback_json['overall_rating'] = 7  # Default fallback
                            
                else:
                    # Fallback: create structured response from text
                    feedback_json = self._parse_text_feedback(feedback_text, prompt)
            except json.JSONDecodeError:
                feedback_json = self._parse_text_feedback(feedback_text, prompt)
            
            return {
                "status": "success",
                "feedback": feedback_json,
                "raw_response": feedback_text,
                "file_analyzed": file_path
            }
            
        except Exception as e:
            return {"error": f"Feedback generation failed: {str(e)}"}
    
    def _get_audio_duration(self, file_path: str) -> float:
        """Get audio file duration"""
        try:
            audio = AudioSegment.from_file(file_path)
            return len(audio) / 1000.0
        except Exception as e:
            print(f"Error getting audio duration: {e}")
            return 0.0
    
    def _parse_text_feedback(self, feedback_text: str, original_prompt: str) -> Dict:
        """Parse unstructured feedback text into structured format"""
        
        # Simple keyword-based parsing for fallback
        rating = 7  # Default rating
        if "excellent" in feedback_text.lower() or "amazing" in feedback_text.lower():
            rating = 9
        elif "good" in feedback_text.lower() or "nice" in feedback_text.lower():
            rating = 8
        elif "poor" in feedback_text.lower() or "bad" in feedback_text.lower():
            rating = 4
        elif "terrible" in feedback_text.lower():
            rating = 2
        
        # Extract suggestions (simple pattern matching)
        suggestions = []
        if "volume" in feedback_text.lower():
            suggestions.append({
                "action": "volume_adjust",
                "parameters": {"gain_db": 1.0},
                "reason": "Volume adjustment needed based on feedback"
            })
        if "fade" in feedback_text.lower() or "transition" in feedback_text.lower():
            suggestions.append({
                "action": "crossfade",
                "parameters": {"duration_ms": 4000},
                "reason": "Improve transitions based on feedback"
            })
        
        return {
            "overall_rating": rating,
            "matches_request": "yes" in feedback_text.lower() or "match" in feedback_text.lower(),
            "feedback": feedback_text,
            "specific_issues": [],
            "suggestions": suggestions,
            "energy_flow": "Analysis not available in text mode",
            "transition_quality": "Analysis not available in text mode",
            "technical_issues": [],
            "creative_suggestions": []
        }
    
    def apply_feedback_suggestions(self, mix_file: str, feedback: Dict, output_file: str) -> Dict:
        """Apply feedback suggestions to improve the mix"""
        try:
            # Load the mix
            audio = AudioSegment.from_file(mix_file)
            
            # Apply suggestions
            suggestions = feedback.get('suggestions', [])
            applied_changes = []
            
            for suggestion in suggestions:
                action = suggestion.get('action', '')
                params = suggestion.get('parameters', {})
                
                if action == "volume_adjust":
                    gain_db = params.get('gain_db', 0)
                    audio = audio + gain_db
                    applied_changes.append(f"Applied volume adjustment: {gain_db}dB")
                
                elif action == "trim":
                    start_ms = params.get('start_ms', 0)
                    end_ms = params.get('end_ms', len(audio))
                    audio = audio[start_ms:end_ms]
                    applied_changes.append(f"Trimmed audio: {start_ms}ms to {end_ms}ms")
                
                elif action == "fade_adjustment":
                    fade_in = params.get('fade_in_ms', 0)
                    fade_out = params.get('fade_out_ms', 0)
                    if fade_in > 0:
                        audio = audio.fade_in(fade_in)
                    if fade_out > 0:
                        audio = audio.fade_out(fade_out)
                    applied_changes.append(f"Applied fades: in={fade_in}ms, out={fade_out}ms")
            
            # Normalize after changes
            audio = normalize(audio)
            
            # Export improved mix
            audio.export(output_file, format="mp3", bitrate="320k")
            
            return {
                "status": "success",
                "output_file": output_file,
                "applied_changes": applied_changes,
                "duration_ms": len(audio)
            }
            
        except Exception as e:
            return {"error": f"Failed to apply feedback: {str(e)}"}
    
    def iterative_improvement_cycle(self, initial_mix: str, prompt: str, 
                                  mix_metadata: Dict, max_iterations: int = 3) -> Dict:
        """Run multiple feedback and improvement cycles"""
        
        current_mix = initial_mix
        iteration_history = []
        
        for iteration in range(max_iterations):
            print(f"Feedback iteration {iteration + 1}/{max_iterations}")
            
            # Get feedback
            feedback_result = self.get_mix_feedback(current_mix, prompt, mix_metadata)
            
            if "error" in feedback_result:
                break
            
            feedback = feedback_result['feedback']
            
            # Ensure overall_rating is an integer
            try:
                rating = int(feedback.get('overall_rating', 0))
            except (ValueError, TypeError):
                rating = 0
            
            iteration_data = {
                "iteration": iteration + 1,
                "feedback": feedback,
                "rating": rating
            }
            
            # Check if we're satisfied with the rating
            if rating >= 8:
                iteration_data['status'] = 'satisfied'
                iteration_history.append(iteration_data)
                break
            
            # Apply improvements
            improved_mix = os.path.join(Config.TEMP_DIR, f"mix_improved_v{iteration + 1}.mp3")
            improvement_result = self.apply_feedback_suggestions(current_mix, feedback, improved_mix)
            
            if "error" in improvement_result:
                iteration_data['status'] = 'improvement_failed'
                iteration_data['error'] = improvement_result['error']
            else:
                iteration_data['status'] = 'improved'
                iteration_data['improvements'] = improvement_result['applied_changes']
                current_mix = improved_mix
            
            iteration_history.append(iteration_data)
        
        # Get final rating safely
        final_rating = 0
        if iteration_history:
            try:
                final_rating = int(iteration_history[-1]['feedback'].get('overall_rating', 0))
            except (ValueError, TypeError):
                final_rating = iteration_history[-1].get('rating', 0)
        
        return {
            "status": "completed",
            "final_mix": current_mix,
            "iterations": len(iteration_history),
            "iteration_history": iteration_history,
            "final_rating": final_rating
        }

# Tool function for LLM integration
def iterative_feedback_tool(file_path: str, prompt: str, mix_metadata: Optional[Dict] = None) -> Dict:
    """Tool function for getting mix feedback"""
    tool = IterativeFeedbackTool()
    return tool.get_mix_feedback(file_path, prompt, mix_metadata)

def iterative_improvement_tool(file_path: str, prompt: str, mix_metadata: Dict, max_iterations: int = 3) -> Dict:
    """Tool function for iterative mix improvement"""
    Config.ensure_directories()
    tool = IterativeFeedbackTool()
    return tool.iterative_improvement_cycle(file_path, prompt, mix_metadata, max_iterations)