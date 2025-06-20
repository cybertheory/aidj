import os
import json
from datetime import datetime
from typing import Dict, Optional
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, TCON, COMM
from config import Config

class FinalMixExportTool:
    def __init__(self):
        self.exports_dir = Config.EXPORTS_DIR
        
    def export_final_mix(self, file_path: str, title: str, metadata: Dict, 
                        export_format: str = "mp3", bitrate: str = "320k") -> Dict:
        """Export final mix with metadata and proper file organization"""
        
        if not os.path.exists(file_path):
            return {"error": f"Source file not found: {file_path}"}
        
        try:
            Config.ensure_directories()
            
            # Generate export filename
            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_filename = f"{safe_title}_{timestamp}.{export_format}"
            export_path = os.path.join(self.exports_dir, export_filename)
            
            # Load and process audio
            audio = AudioSegment.from_file(file_path)
            
            # Apply final mastering touches
            audio = self._apply_final_mastering(audio, metadata)
            
            # Export audio file
            export_params = {
                "format": export_format,
                "bitrate": bitrate
            }
            
            if export_format == "wav":
                export_params = {"format": "wav"}
            
            audio.export(export_path, **export_params)
            
            # Add metadata tags
            self._add_metadata_tags(export_path, title, metadata)
            
            # Create mix report
            report_path = self._create_mix_report(export_path, title, metadata)
            
            # Create PyDub script
            script_path = self._save_pydub_script(export_path, metadata)
            
            return {
                "status": "success",
                "export_path": export_path,
                "report_path": report_path,
                "script_path": script_path,
                "file_size_mb": os.path.getsize(export_path) / (1024 * 1024),
                "duration_seconds": len(audio) / 1000,
                "format": export_format,
                "bitrate": bitrate,
                "metadata": metadata
            }
            
        except Exception as e:
            return {"error": f"Export failed: {str(e)}"}
    
    def _apply_final_mastering(self, audio: AudioSegment, metadata: Dict) -> AudioSegment:
        """Apply final mastering processing"""
        
        # Normalize
        audio = normalize(audio)
        
        # Light compression for consistency
        audio = compress_dynamic_range(audio, threshold=-20.0, ratio=2.0)
        
        # Ensure proper levels (target around -1dB peak)
        current_peak = audio.max_dBFS
        if current_peak > -1.0:
            adjustment = -1.0 - current_peak
            audio = audio + adjustment
        
        # Add subtle fade in/out if not present
        if len(audio) > 10000:  # Only for mixes longer than 10 seconds
            # Check if fades are already present
            start_level = audio[:1000].dBFS
            end_level = audio[-1000:].dBFS
            
            if start_level > audio.dBFS - 6:  # No significant fade in
                audio = audio.fade_in(500)
            
            if end_level > audio.dBFS - 6:  # No significant fade out
                audio = audio.fade_out(1000)
        
        return audio
    
    def _add_metadata_tags(self, file_path: str, title: str, metadata: Dict):
        """Add ID3 tags to the exported MP3 file"""
        try:
            if not file_path.endswith('.mp3'):
                return
            
            audio_file = MP3(file_path, ID3=ID3)
            
            # Add ID3 tag if it doesn't exist
            try:
                audio_file.add_tags()
            except:
                pass  # Tags already exist
            
            # Set basic metadata
            audio_file.tags.add(TIT2(encoding=3, text=title))
            audio_file.tags.add(TPE1(encoding=3, text=metadata.get('artist', 'AI Music Mixer')))
            audio_file.tags.add(TALB(encoding=3, text=metadata.get('album', 'AI Generated Mix')))
            audio_file.tags.add(TDRC(encoding=3, text=str(datetime.now().year)))
            audio_file.tags.add(TCON(encoding=3, text=metadata.get('genre', 'Electronic')))
            
            # Add detailed mix information as comment
            mix_info = {
                'bpm': metadata.get('bpm', 0),
                'vibe': metadata.get('vibe', ''),
                'tracks_used': metadata.get('tracks_used', 0),
                'mix_style': metadata.get('mix_style', ''),
                'generated_by': 'AI Music Mixer v1.0'
            }
            
            comment_text = json.dumps(mix_info, indent=2)
            audio_file.tags.add(COMM(encoding=3, lang='eng', desc='Mix Info', text=comment_text))
            
            audio_file.save()
            
        except Exception as e:
            print(f"Warning: Could not add metadata tags: {e}")
    
    def _create_mix_report(self, export_path: str, title: str, metadata: Dict) -> str:
        """Create a detailed mix report"""
        report_filename = os.path.splitext(os.path.basename(export_path))[0] + "_report.json"
        report_path = os.path.join(self.exports_dir, report_filename)
        
        # Get file stats
        file_stats = os.stat(export_path)
        
        report_data = {
            "mix_title": title,
            "export_timestamp": datetime.now().isoformat(),
            "file_info": {
                "path": export_path,
                "size_bytes": file_stats.st_size,
                "size_mb": round(file_stats.st_size / (1024 * 1024), 2)
            },
            "mix_metadata": metadata,
            "generation_info": {
                "tool_version": "AI Music Mixer v1.0",
                "python_version": "3.8+",
                "dependencies": ["pydub", "librosa", "openai"]
            },
            "audio_specs": {
                "format": "MP3",
                "bitrate": "320kbps",
                "sample_rate": "44.1kHz",
                "channels": "Stereo"
            }
        }
        
        try:
            with open(report_path, 'w') as f:
                json.dump(report_data, f, indent=2)
            return report_path
        except Exception as e:
            print(f"Warning: Could not create mix report: {e}")
            return ""
    
    def _save_pydub_script(self, export_path: str, metadata: Dict) -> str:
        """Save the PyDub script used to generate the mix"""
        script_filename = os.path.splitext(os.path.basename(export_path))[0] + "_script.py"
        script_path = os.path.join(self.exports_dir, script_filename)
        
        pydub_code = metadata.get('pydub_code', '# PyDub code not available')
        
        # Add header to the script
        script_content = f'''#!/usr/bin/env python3
"""
AI Music Mixer - Generated PyDub Script
Mix: {metadata.get('title', 'Untitled')}
Generated: {datetime.now().isoformat()}
"""

{pydub_code}
'''
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            return script_path
        except Exception as e:
            print(f"Warning: Could not save PyDub script: {e}")
            return ""
    
    def create_mix_package(self, export_result: Dict, include_source_files: bool = False) -> Dict:
        """Create a complete mix package with all files"""
        if export_result.get('status') != 'success':
            return {"error": "Invalid export result"}
        
        try:
            export_path = export_result['export_path']
            base_name = os.path.splitext(os.path.basename(export_path))[0]
            package_dir = os.path.join(self.exports_dir, f"{base_name}_package")
            
            os.makedirs(package_dir, exist_ok=True)
            
            # Copy main files to package
            import shutil
            
            # Copy the mix file
            mix_file = os.path.join(package_dir, os.path.basename(export_path))
            shutil.copy2(export_path, mix_file)
            
            # Copy report and script
            if export_result.get('report_path'):
                shutil.copy2(export_result['report_path'], package_dir)
            
            if export_result.get('script_path'):
                shutil.copy2(export_result['script_path'], package_dir)
            
            # Create README
            readme_path = os.path.join(package_dir, "README.md")
            self._create_package_readme(readme_path, export_result)
            
            # Optionally include source files
            if include_source_files:
                source_dir = os.path.join(package_dir, "source_tracks")
                os.makedirs(source_dir, exist_ok=True)
                # Note: Would need to track source files through the pipeline
            
            return {
                "status": "success",
                "package_path": package_dir,
                "files_included": os.listdir(package_dir)
            }
            
        except Exception as e:
            return {"error": f"Package creation failed: {str(e)}"}
    
    def _create_package_readme(self, readme_path: str, export_result: Dict):
        """Create README file for the mix package"""
        metadata = export_result.get('metadata', {})
        
        readme_content = f"""# AI Generated Music Mix

## Mix Information
- **Title**: {metadata.get('title', 'Untitled Mix')}
- **Duration**: {export_result.get('duration_seconds', 0):.1f} seconds
- **BPM**: {metadata.get('bpm', 'Unknown')}
- **Genre**: {metadata.get('genre', 'Electronic')}
- **Vibe**: {metadata.get('vibe', 'Unknown')}

## Technical Details
- **Format**: {export_result.get('format', 'MP3').upper()}
- **Bitrate**: {export_result.get('bitrate', '320k')}
- **File Size**: {export_result.get('file_size_mb', 0):.1f} MB

## Generation Details
- **Tracks Used**: {metadata.get('tracks_used', 'Unknown')}
- **Mix Style**: {metadata.get('mix_style', 'Unknown')}
- **Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Files Included
- `{os.path.basename(export_result['export_path'])}` - The final mix
- `*_report.json` - Detailed generation report
- `*_script.py` - PyDub script to reproduce the mix
- `README.md` - This file

## About AI Music Mixer
This mix was generated using AI Music Mixer, an open-source tool that:
1. Discovers royalty-free music from APIs
2. Analyzes audio characteristics
3. Generates seamless mixes using PyDub
4. Iteratively improves based on AI feedback

## Usage Rights
This mix uses royalty-free source material. Please verify licensing for commercial use.

---
Generated by AI Music Mixer v1.0
"""
        
        try:
            with open(readme_path, 'w') as f:
                f.write(readme_content)
        except Exception as e:
            print(f"Warning: Could not create README: {e}")

# Tool function for LLM integration
def final_mix_export_tool(file_path: str, title: str, metadata: Dict, 
                         export_format: str = "mp3", bitrate: str = "320k") -> Dict:
    """Tool function for final mix export"""
    Config.ensure_directories()
    tool = FinalMixExportTool()
    return tool.export_final_mix(file_path, title, metadata, export_format, bitrate)

def create_mix_package_tool(export_result: Dict, include_source_files: bool = False) -> Dict:
    """Tool function for creating complete mix package"""
    tool = FinalMixExportTool()
    return tool.create_mix_package(export_result, include_source_files)