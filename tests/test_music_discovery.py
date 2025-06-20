import pytest
import requests
from unittest.mock import Mock, patch, MagicMock, mock_open

from tools.music_discovery import MusicDiscoveryTool, music_discovery_tool


class TestMusicDiscoveryTool:
    
    @pytest.fixture
    def tool(self):
        return MusicDiscoveryTool()
    
    @pytest.fixture
    def mock_jamendo_response(self):
        """Mock Jamendo API response"""
        return {
            "results": [
                {
                    "id": "123456",
                    "name": "Chill Beats",
                    "artist_name": "Cool Artist",
                    "duration": 180,
                    "audio": "https://example.com/track1.mp3",
                    "musicinfo": {
                        "tags": {"genres": ["electronic", "chill"]},
                        "bpm": 120
                    }
                },
                {
                    "id": "789012",
                    "name": "Ambient Flow",
                    "artist_name": "Zen Master",
                    "duration": 240,
                    "audio": "https://example.com/track2.mp3",
                    "musicinfo": {
                        "tags": {"genres": ["ambient"]},
                        "bpm": 95
                    }
                }
            ]
        }
    
    @pytest.fixture
    def mock_freesound_response(self):
        """Mock Freesound API response"""
        return {
            "results": [
                {
                    "id": 456789,
                    "name": "Lo-Fi Loop",
                    "username": "Producer123",
                    "duration": 120.5,
                    "previews": {
                        "preview-hq-mp3": "https://example.com/lofi.mp3"
                    },
                    "tags": ["lofi", "hip-hop", "instrumental"]
                }
            ]
        }
    
    @patch('requests.get')
    def test_search_jamendo_success(self, mock_get, tool, mock_jamendo_response):
        """Test successful Jamendo search"""
        mock_response = Mock()
        mock_response.json.return_value = mock_jamendo_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = tool.search_jamendo("chill beats", duration_min=60, duration_max=300, limit=10)
        
        assert len(result) == 2
        assert result[0]["name"] == "Chill Beats"
        assert result[0]["artist"] == "Cool Artist"
        assert result[0]["duration"] == 180
        assert result[0]["source"] == "jamendo"
        assert result[1]["bpm"] == 95
    
    @patch('requests.get')
    def test_search_jamendo_api_error(self, mock_get, tool):
        """Test Jamendo search with API error"""
        mock_get.side_effect = requests.RequestException("API Error")
        
        result = tool.search_jamendo("test query")
        
        assert result == []
    
    @patch('requests.get')
    def test_search_jamendo_duration_filter(self, mock_get, tool, mock_jamendo_response):
        """Test Jamendo search with duration filtering"""
        # Modify response to have tracks outside duration range
        mock_jamendo_response["results"][0]["duration"] = 30  # Too short
        mock_jamendo_response["results"][1]["duration"] = 400  # Too long
        
        mock_response = Mock()
        mock_response.json.return_value = mock_jamendo_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = tool.search_jamendo("test", duration_min=60, duration_max=300)
        
        assert len(result) == 0  # Both tracks filtered out
    
    @patch('requests.get')
    def test_search_freesound_success(self, mock_get, tool, mock_freesound_response):
        """Test successful Freesound search"""
        mock_response = Mock()
        mock_response.json.return_value = mock_freesound_response
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        result = tool.search_freesound("lofi", duration_min=60, duration_max=300, limit=10)
        
        assert len(result) == 1
        assert result[0]["name"] == "Lo-Fi Loop"
        assert result[0]["artist"] == "Producer123"
        assert result[0]["source"] == "freesound"
        assert "lofi" in result[0]["tags"]
        
        # Check that Authorization header was set
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'headers' in call_args.kwargs
        assert 'Authorization' in call_args.kwargs['headers']
    
    @patch('requests.get')
    def test_search_freesound_api_error(self, mock_get, tool):
        """Test Freesound search with API error"""
        mock_get.side_effect = requests.RequestException("API Error")
        
        result = tool.search_freesound("test query")
        
        assert result == []
    
    @patch('requests.get')
    @patch('builtins.open', new_callable=mock_open)
    @patch('tools.music_discovery.Config')
    def test_download_track_success(self, mock_config, mock_file, mock_get, tool):
        """Test successful track download"""
        mock_config.MUSIC_DIR = "/tmp/music"
        
        # Mock successful download response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'fake_audio_data_chunk1', b'fake_audio_data_chunk2']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        track = {
            "id": "123",
            "name": "Test Track",
            "artist": "Test Artist",
            "download_url": "https://example.com/track.mp3"
        }
        
        with patch('os.path.join', return_value="/tmp/music/Test_Artist_Test_Track_123.mp3"):
            result = tool.download_track(track)
            
            assert result == "/tmp/music/Test_Artist_Test_Track_123.mp3"
            mock_get.assert_called_once_with("https://example.com/track.mp3", stream=True)
            mock_file.assert_called_once()
    
    @patch('requests.get')
    def test_download_track_error(self, mock_get, tool):
        """Test track download with error"""
        mock_get.side_effect = requests.RequestException("Download failed")
        
        track = {
            "id": "123",
            "name": "Test Track", 
            "artist": "Test Artist",
            "download_url": "https://example.com/track.mp3"
        }
        
        result = tool.download_track(track)
        
        assert result == ""
    
    @patch('tools.music_discovery.Config.ensure_directories')
    def test_discover_and_download(self, mock_ensure_dirs, tool):
        """Test the main discover and download workflow"""
        mock_jamendo_tracks = [
            {"id": "1", "name": "Track1", "artist": "Artist1", "download_url": "http://example.com/1.mp3"}
        ]
        mock_freesound_tracks = [
            {"id": "2", "name": "Track2", "artist": "Artist2", "download_url": "http://example.com/2.mp3"}
        ]
        
        with patch.object(tool, 'search_jamendo', return_value=mock_jamendo_tracks), \
             patch.object(tool, 'search_freesound', return_value=mock_freesound_tracks), \
             patch.object(tool, 'download_track', side_effect=["/path/track1.mp3", "/path/track2.mp3"]):
            
            result = tool.discover_and_download("chill beats", max_tracks=5)
            
            assert len(result) == 2
            assert "/path/track1.mp3" in result
            assert "/path/track2.mp3" in result


class TestMusicDiscoveryToolFunction:
    
    @patch('tools.music_discovery.MusicDiscoveryTool')
    def test_music_discovery_tool_function_success(self, mock_tool_class):
        """Test the music discovery tool function with successful results"""
        mock_tool = Mock()
        mock_tool.discover_and_download.return_value = ["/path/track1.mp3", "/path/track2.mp3"]
        mock_tool_class.return_value = mock_tool
        
        result = music_discovery_tool("lofi beats", duration_min=60, duration_max=300, max_tracks=3)
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["downloaded_files"]) == 2
        assert result["query"] == "lofi beats"
        mock_tool.discover_and_download.assert_called_once_with("lofi beats", 60, 300, 3)
    
    @patch('tools.music_discovery.MusicDiscoveryTool')
    def test_music_discovery_tool_function_no_results(self, mock_tool_class):
        """Test the music discovery tool function with no results"""
        mock_tool = Mock()
        mock_tool.discover_and_download.return_value = []
        mock_tool_class.return_value = mock_tool
        
        result = music_discovery_tool("obscure query")
        
        assert result["status"] == "no_results"
        assert result["count"] == 0
        assert result["downloaded_files"] == []


if __name__ == "__main__":
    pytest.main([__file__])