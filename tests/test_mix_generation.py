import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pydub import AudioSegment
import numpy as np

from tools.mix_generation import MixGenerationTool, mix_generation_tool


class TestMixGenerationTool:
    
    @pytest.fixture
    def tool(self):
        return MixGenerationTool()
    
    @pytest.fixture
    def mock_audio_segment(self):
        """Create a mock AudioSegment for testing"""
        mock_audio = Mock(spec=AudioSegment)
        mock_audio.__len__ = Mock(return_value=120000)  # 2 minutes
        mock_audio.set_frame_rate.return_value = mock_audio
        mock_audio.set_channels.return_value = mock_audio
        mock_audio.fade_in.return_value = mock_audio
        mock_audio.fade_out.return_value = mock_audio
        mock_audio.overlay.return_value = mock_audio
        mock_audio.__add__ = Mock(return_value=mock_audio)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        mock_audio.export = Mock()
        mock_audio.raw_data = b"fake_audio_data"
        mock_audio.frame_rate = 44100
        mock_audio._spawn.return_value = mock_audio
        return mock_audio
    
    @pytest.fixture
    def sample_analyses(self):
        return [
            {
                "tempo": 120,
                "mood": "calm",
                "energy_mean": 0.5,
                "mixing_metadata": {
                    "best_mix_in": 10.0,
                    "best_mix_out": 100.0
                }
            },
            {
                "tempo": 125,
                "mood": "energetic", 
                "energy_mean": 0.8,
                "mixing_metadata": {
                    "best_mix_in": 15.0,
                    "best_mix_out": 110.0
                }
            }
        ]
    
    def test_load_audio_segment_success(self, tool, mock_audio_segment):
        """Test successful audio loading"""
        with patch('os.path.exists', return_value=True), \
             patch('tools.mix_generation.AudioSegment.from_file', return_value=mock_audio_segment):
            
            result = tool.load_audio_segment("test.mp3")
            
            assert result is not None
            mock_audio_segment.set_frame_rate.assert_called_once()
            mock_audio_segment.set_channels.assert_called_once()
    
    def test_load_audio_segment_file_not_found(self, tool):
        """Test audio loading when file doesn't exist"""
        with patch('os.path.exists', return_value=False), \
             patch('os.listdir', return_value=[]):
            
            result = tool.load_audio_segment("nonexistent.mp3")
            
            assert result is None
    
    def test_apply_fade(self, tool, mock_audio_segment):
        """Test fade application"""
        result = tool.apply_fade(mock_audio_segment, fade_in_ms=1000, fade_out_ms=2000)
        
        mock_audio_segment.fade_in.assert_called_once_with(1000)
        mock_audio_segment.fade_out.assert_called_once_with(2000)
    
    def test_crossfade_tracks(self, tool, mock_audio_segment):
        """Test crossfading between tracks"""
        track1 = mock_audio_segment
        track2 = mock_audio_segment
        
        result = tool.crossfade_tracks(track1, track2, crossfade_duration_ms=3000)
        
        track1.fade_out.assert_called()
        track2.fade_in.assert_called()
        track1.overlay.assert_called()
    
    def test_beat_match_tracks(self, tool, mock_audio_segment):
        """Test beat matching functionality"""
        track1 = mock_audio_segment
        track2 = mock_audio_segment
        
        result1, result2 = tool.beat_match_tracks(track1, track2, 120.0, 125.0, 122.5)
        
        assert result1 is not None
        assert result2 is not None
    
    def test_apply_eq_filter(self, tool, mock_audio_segment):
        """Test EQ filter application"""
        mock_audio_segment.low_pass_filter.return_value = mock_audio_segment
        mock_audio_segment.high_pass_filter.return_value = mock_audio_segment
        mock_audio_segment.__sub__ = Mock(return_value=mock_audio_segment)
        
        # Test bass boost
        result = tool.apply_eq_filter(mock_audio_segment, "bass_boost")
        mock_audio_segment.low_pass_filter.assert_called_with(200)
        
        # Test treble boost
        result = tool.apply_eq_filter(mock_audio_segment, "treble_boost")
        mock_audio_segment.high_pass_filter.assert_called_with(3000)
        
        # Test warm
        result = tool.apply_eq_filter(mock_audio_segment, "warm")
        mock_audio_segment.low_pass_filter.assert_called_with(8000)
    
    @patch('tools.mix_generation.Config.ensure_directories')
    @patch('tools.mix_generation.normalize')
    @patch('tools.mix_generation.compress_dynamic_range')
    def test_generate_mix_success(self, mock_compress, mock_normalize, mock_ensure_dirs, 
                                  tool, mock_audio_segment, sample_analyses):
        """Test successful mix generation"""
        mock_normalize.return_value = mock_audio_segment
        mock_compress.return_value = mock_audio_segment
        
        with patch.object(tool, 'load_audio_segment', return_value=mock_audio_segment), \
             patch.object(tool, '_create_seamless_mix', return_value=mock_audio_segment), \
             patch('tempfile.gettempdir', return_value='/tmp'):
            
            file_paths = ["track1.mp3", "track2.mp3"]
            result = tool.generate_mix(file_paths, sample_analyses)
            
            assert result["status"] == "success"
            assert "draft_path" in result
            assert result["tracks_used"] == 2
            assert "pydub_code" in result
            assert "mix_metadata" in result
    
    def test_generate_mix_no_files(self, tool):
        """Test mix generation with no files provided"""
        result = tool.generate_mix([], [])
        
        assert "error" in result
        assert result["error"] == "No files provided"
    
    def test_create_seamless_mix(self, tool, mock_audio_segment, sample_analyses):
        """Test seamless mix creation"""
        segments = [
            {"audio": mock_audio_segment, "analysis": sample_analyses[0], "file_path": "track1.mp3"},
            {"audio": mock_audio_segment, "analysis": sample_analyses[1], "file_path": "track2.mp3"}
        ]
        
        with patch.object(tool, 'crossfade_tracks', return_value=mock_audio_segment):
            result = tool._create_seamless_mix(segments, "crossfade", 3000)
            
            assert result is not None
    
    def test_create_energetic_mix(self, tool, mock_audio_segment, sample_analyses):
        """Test energetic mix creation"""
        segments = [
            {"audio": mock_audio_segment, "analysis": sample_analyses[0], "file_path": "track1.mp3"},
            {"audio": mock_audio_segment, "analysis": sample_analyses[1], "file_path": "track2.mp3"}
        ]
        
        with patch.object(tool, 'crossfade_tracks', return_value=mock_audio_segment):
            result = tool._create_energetic_mix(segments, "crossfade", 1500)
            
            assert result is not None
    
    def test_estimate_mix_bpm(self, tool, sample_analyses):
        """Test BPM estimation"""
        segments = [
            {"analysis": sample_analyses[0]},
            {"analysis": sample_analyses[1]}
        ]
        
        result = tool._estimate_mix_bpm(segments)
        
        assert result == 122.5  # Average of 120 and 125
    
    def test_generate_pydub_code(self, tool, sample_analyses):
        """Test PyDub code generation"""
        segments = [
            {"file_path": "track1.mp3", "analysis": sample_analyses[0]},
            {"file_path": "track2.mp3", "analysis": sample_analyses[1]}
        ]
        
        result = tool._generate_pydub_code(segments, "crossfade", 3000, "seamless")
        
        assert "AudioSegment" in result
        assert "track_0" in result
        assert "track_1" in result
        assert "crossfade" in result.lower() or "overlay" in result


class TestMixGenerationToolFunction:
    
    @patch('tools.mix_generation.Config.ensure_directories')
    def test_mix_generation_tool_function(self, mock_ensure_dirs):
        """Test the main tool function"""
        with patch('tools.mix_generation.MixGenerationTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.check_files_exist.return_value = {
                "existing_files": ["track1.mp3"],
                "missing_files": [],
                "music_dir_contents": ["track1.mp3"]
            }
            mock_tool.generate_mix.return_value = {"status": "success"}
            mock_tool_class.return_value = mock_tool
            
            result = mix_generation_tool(
                ["track1.mp3"], 
                [{"tempo": 120}], 
                "crossfade", 
                3000, 
                "seamless"
            )
            
            assert result["status"] == "success"
            mock_tool.check_files_exist.assert_called_once()
            mock_tool.generate_mix.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])