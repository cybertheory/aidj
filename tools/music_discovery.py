import requests
import os
from typing import List, Dict, Optional
from urllib.parse import urlencode
import json
from config import Config

class MusicDiscoveryTool:
    def __init__(self):
        self.jamendo_client_id = Config.JAMENDO_CLIENT_ID
        self.freesound_api_key = Config.FREESOUND_API_KEY
        
    def search_jamendo(self, query: str, duration_min: int = 60, duration_max: int = 300, limit: int = 10) -> List[Dict]:
        """Search Jamendo API for royalty-free music"""
        base_url = "https://api.jamendo.com/v3.0/tracks/"
        
        params = {
            'client_id': self.jamendo_client_id,
            'format': 'json',
            'limit': limit,
            'search': query,
            'include': 'musicinfo',
            'audioformat': 'mp3',
            'audiodlformat': 'mp32',
            'tags': 'instrumental',  # Focus on instrumental tracks for mixing
        }
        
        try:
            response = requests.get(base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for track in data.get('results', []):
                duration = track.get('duration', 0)
                if duration_min <= duration <= duration_max:
                    tracks.append({
                        'id': track['id'],
                        'name': track['name'],
                        'artist': track['artist_name'],
                        'duration': duration,
                        'download_url': track.get('audio', ''),
                        'genre': track.get('musicinfo', {}).get('tags', {}).get('genres', []),
                        'bpm': track.get('musicinfo', {}).get('bpm', 0),
                        'source': 'jamendo'
                    })
            
            return tracks
        except Exception as e:
            print(f"Error searching Jamendo: {e}")
            return []
    
    def search_freesound(self, query: str, duration_min: int = 60, duration_max: int = 300, limit: int = 10) -> List[Dict]:
        """Search Freesound API for royalty-free audio"""
        base_url = "https://freesound.org/apiv2/search/text/"
        
        headers = {
            'Authorization': f'Token {self.freesound_api_key}'
        }
        
        params = {
            'query': f'{query} music instrumental',
            'filter': f'duration:[{duration_min} TO {duration_max}] type:mp3',
            'fields': 'id,name,username,duration,download,previews,tags,analysis',
            'page_size': limit
        }
        
        try:
            response = requests.get(base_url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for sound in data.get('results', []):
                tracks.append({
                    'id': sound['id'],
                    'name': sound['name'],
                    'artist': sound['username'],
                    'duration': sound['duration'],
                    'download_url': sound['previews']['preview-hq-mp3'],
                    'tags': sound.get('tags', []),
                    'source': 'freesound'
                })
            
            return tracks
        except Exception as e:
            print(f"Error searching Freesound: {e}")
            return []
    
    def download_track(self, track: Dict, filename: Optional[str] = None) -> str:
        """Download a track to the music directory"""
        if not filename:
            safe_name = "".join(c for c in f"{track['artist']}_{track['name']}" if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_name}_{track['id']}.mp3"
        
        file_path = os.path.join(Config.MUSIC_DIR, filename)
        
        try:
            response = requests.get(track['download_url'], stream=True)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            print(f"Downloaded: {filename}")
            return file_path
        except Exception as e:
            print(f"Error downloading {filename}: {e}")
            return ""
    
    def discover_and_download(self, query: str, duration_min: int = 60, duration_max: int = 300, max_tracks: int = 5) -> List[str]:
        """Main tool function: discover and download tracks"""
        Config.ensure_directories()
        
        # Search both APIs
        jamendo_tracks = self.search_jamendo(query, duration_min, duration_max, max_tracks)
        freesound_tracks = self.search_freesound(query, duration_min, duration_max, max_tracks)
        
        # Combine and limit results
        all_tracks = (jamendo_tracks + freesound_tracks)[:max_tracks]
        
        # Download tracks
        downloaded_files = []
        for track in all_tracks:
            file_path = self.download_track(track)
            if file_path:
                downloaded_files.append(file_path)
        
        return downloaded_files

# Tool function for LLM integration
def music_discovery_tool(query: str, duration_min: int = 60, duration_max: int = 300, max_tracks: int = 5) -> Dict:
    """Tool function for music discovery"""
    tool = MusicDiscoveryTool()
    files = tool.discover_and_download(query, duration_min, duration_max, max_tracks)
    
    return {
        "status": "success" if files else "no_results",
        "downloaded_files": files,
        "count": len(files),
        "query": query
    }