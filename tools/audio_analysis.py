import librosa
import numpy as np
from typing import Dict, List, Optional
import json
import os
from pydub import AudioSegment
from config import Config

class AudioAnalysisTool:
    def __init__(self):
        self.sample_rate = Config.DEFAULT_SAMPLE_RATE
    
    def analyze_file(self, file_path: str) -> Dict:
        """Comprehensive audio analysis using librosa"""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        try:
            # Load audio file
            y, sr = librosa.load(file_path, sr=self.sample_rate)
            
            # Basic info
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Tempo and beat analysis
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Spectral features
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
            zero_crossing_rate = librosa.feature.zero_crossing_rate(y)[0]
            
            # MFCC features for timbre analysis
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Chroma features for key detection
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Energy and dynamics
            rms_energy = librosa.feature.rms(y=y)[0]
            
            # Key detection (simplified)
            chroma_mean = np.mean(chroma, axis=1)
            key_index = np.argmax(chroma_mean)
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            estimated_key = keys[key_index]
            
            # Mood/energy estimation
            energy_mean = np.mean(rms_energy)
            brightness = np.mean(spectral_centroids)
            
            # Classify energy level
            if energy_mean > 0.1:
                energy_level = "high"
            elif energy_mean > 0.05:
                energy_level = "medium"
            else:
                energy_level = "low"
            
            # Classify mood based on spectral features
            if brightness > 3000 and energy_mean > 0.08:
                mood = "energetic"
            elif brightness < 1500 and energy_mean < 0.06:
                mood = "calm"
            elif tempo > 120:
                mood = "upbeat"
            else:
                mood = "ambient"
            
            # Segment analysis for mixing points
            segments = self._find_mixing_points(y, sr, beats)
            
            analysis_result = {
                "file_path": file_path,
                "duration": float(duration),
                "tempo": float(tempo),
                "estimated_key": estimated_key,
                "energy_level": energy_level,
                "mood": mood,
                "brightness": float(brightness),
                "energy_mean": float(energy_mean),
                "segments": segments,
                "mixing_metadata": {
                    "intro_end": segments.get("intro_end", 10.0),
                    "outro_start": segments.get("outro_start", duration - 15.0),
                    "best_mix_in": segments.get("best_mix_in", 30.0),
                    "best_mix_out": segments.get("best_mix_out", duration - 30.0)
                }
            }
            
            return analysis_result
            
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _find_mixing_points(self, y: np.ndarray, sr: int, beats: np.ndarray) -> Dict:
        """Find optimal mixing points in the track"""
        duration = len(y) / sr
        
        # Convert beat frames to time
        beat_times = librosa.frames_to_time(beats, sr=sr)
        
        # Find intro/outro based on energy
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        rms_times = librosa.frames_to_time(range(len(rms)), sr=sr, hop_length=512)
        
        # Smooth RMS for better detection
        from scipy.ndimage import uniform_filter1d
        rms_smooth = uniform_filter1d(rms, size=10)
        
        # Find intro end (where energy stabilizes)
        energy_threshold = np.mean(rms_smooth) * 0.7
        intro_end = 10.0  # Default
        for i, energy in enumerate(rms_smooth):
            if energy > energy_threshold and rms_times[i] > 5.0:
                intro_end = rms_times[i]
                break
        
        # Find outro start (where energy drops)
        outro_start = duration - 15.0  # Default
        for i in range(len(rms_smooth) - 1, 0, -1):
            if rms_smooth[i] < energy_threshold and rms_times[i] < duration - 5.0:
                outro_start = rms_times[i]
                break
        
        return {
            "intro_end": min(intro_end, 20.0),
            "outro_start": max(outro_start, duration - 30.0),
            "best_mix_in": min(intro_end + 10.0, duration * 0.3),
            "best_mix_out": max(outro_start - 10.0, duration * 0.7),
            "beat_times": beat_times.tolist()[:20]  # First 20 beats for sync
        }
    
    def batch_analyze(self, file_paths: List[str]) -> List[Dict]:
        """Analyze multiple files"""
        results = []
        for file_path in file_paths:
            print(f"Analyzing: {os.path.basename(file_path)}")
            analysis = self.analyze_file(file_path)
            results.append(analysis)
        return results

# Tool function for LLM integration
def audio_analysis_tool(file_path: str) -> Dict:
    """Tool function for audio analysis"""
    tool = AudioAnalysisTool()
    return tool.analyze_file(file_path)

def batch_audio_analysis_tool(file_paths: List[str]) -> Dict:
    """Tool function for batch audio analysis"""
    tool = AudioAnalysisTool()
    results = tool.batch_analyze(file_paths)
    return {
        "status": "success",
        "analyses": results,
        "count": len(results)
    }