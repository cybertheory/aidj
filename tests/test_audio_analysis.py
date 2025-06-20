import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock

from tools.audio_analysis import AudioAnalysisTool, audio_analysis_tool, batch_audio_analysis_tool


class TestAudioAnalysisTool:
    
    @pytest.fixture
    def tool(self):
        return AudioAnalysisTool()
    
    @pytest.fixture
    def mock_audio_data(self):
        """Create mock audio data for testing"""
        # Create fake audio data (1 second at 44100 Hz)
        return np.random.random(44100).astype(np.float32)
    
    @pytest.fixture
    def mock_librosa_analysis(self):
        """Mock librosa analysis results"""
        return {
            'tempo': 120.0,
            'beats': np.array([0, 1, 2, 3, 4, 5]),
            'spectral_centroids': np.array([2000.0, 2100.0, 1900.0]),
            'spectral_rolloff': np.array([4000.0, 4200.0, 3800.0]),
            'zero_crossing_rate': np.array([0.1, 0.12, 0.09]),
            'mfccs': np.random.random((13, 100)),
            'chroma': np.random.random((12, 100)),
            'rms_energy': np.array([0.08, 0.09, 0.07])
        }
    
    @patch('os.path.exists', return_value=True)
    @patch('librosa.load')
    @patch('librosa.get_duration')
    @patch('librosa.beat.beat_track')
    @patch('librosa.feature.spectral_centroid')
    @patch('librosa.feature.spectral_rolloff')
    @patch('librosa.feature.zero_crossing_rate')
    @patch('librosa.feature.mfcc')
    @patch('librosa.feature.chroma_stft')
    @patch('librosa.feature.rms')
    def test_analyze_file_success(self, mock_rms, mock_chroma, mock_mfcc, mock_zcr, 
                                  mock_rolloff, mock_centroid, mock_beat_track, 
                                  mock_duration, mock_load, mock_exists, 
                                  tool, mock_audio_data, mock_librosa_analysis):
        """Test successful audio file analysis"""
        # Setup mocks
        mock_load.return_value = (mock_audio_data, 44100)
        mock_duration.return_value = 120.0
        mock_beat_track.return_value = (mock_librosa_analysis['tempo'], mock_librosa_analysis['beats'])
        mock_centroid.return_value = [mock_librosa_analysis['spectral_centroids']]
        mock_rolloff.return_value = [mock_librosa_analysis['spectral_rolloff']]
        mock_zcr.return_value = [mock_librosa_analysis['zero_crossing_rate']]
        mock_mfcc.return_value = mock_librosa_analysis['mfccs']
        mock_chroma.return_value = mock_librosa_analysis['chroma']
        mock_rms.return_value = [mock_librosa_analysis['rms_energy']]
        
        with patch.object(tool, '_find_mixing_points', return_value={
            'intro_end': 10.0,
            'outro_start': 110.0,
            'best_mix_in': 30.0,
            'best_mix_out': 90.0
        }):
            result = tool.analyze_file("test.mp3")
            
            assert "error" not in result
            assert result["duration"] == 120.0
            assert result["tempo"] == 120.0
            assert "estimated_key" in result
            assert "energy_level" in result
            assert "mood" in result
            assert "mixing_metadata" in result
            assert "segments" in result
    
    def test_analyze_file_not_found(self, tool):
        """Test analysis when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = tool.analyze_file("nonexistent.mp3")
            
            assert "error" in result
            assert "not found" in result["error"]
    
    @patch('librosa.load', side_effect=Exception("Load failed"))
    @patch('os.path.exists', return_value=True)
    def test_analyze_file_librosa_error(self, mock_exists, mock_load, tool):
        """Test analysis when librosa fails"""
        result = tool.analyze_file("test.mp3")
        
        assert "error" in result
        assert "Analysis failed" in result["error"]
    
    def test_find_mixing_points(self, tool, mock_audio_data):
        """Test mixing point detection"""
        beats = np.array([0, 1, 2, 3, 4, 5])
        
        with patch('librosa.frames_to_time') as mock_frames_to_time, \
             patch('librosa.feature.rms') as mock_rms, \
             patch('scipy.ndimage.uniform_filter1d') as mock_filter:
            
            # Setup mocks
            mock_frames_to_time.side_effect = lambda x, **kwargs: np.array(x) * 0.023  # Approximate frame to time
            mock_rms.return_value = [np.array([0.05, 0.08, 0.09, 0.08, 0.06, 0.04])]
            mock_filter.return_value = np.array([0.05, 0.08, 0.09, 0.08, 0.06, 0.04])
            
            result = tool._find_mixing_points(mock_audio_data, 44100, beats)
            
            assert "intro_end" in result
            assert "outro_start" in result
            assert "best_mix_in" in result
            assert "best_mix_out" in result
            assert "beat_times" in result
    
    def test_batch_analyze(self, tool):
        """Test batch analysis of multiple files"""
        with patch.object(tool, 'analyze_file') as mock_analyze:
            mock_analyze.side_effect = [
                {"duration": 120.0, "tempo": 120.0},
                {"duration": 180.0, "tempo": 125.0},
                {"error": "Analysis failed"}
            ]
            
            result = tool.batch_analyze(["file1.mp3", "file2.mp3", "file3.mp3"])
            
            assert len(result) == 3
            assert result[0]["duration"] == 120.0
            assert result[1]["duration"] == 180.0
            assert "error" in result[2]


class TestAudioAnalysisToolFunctions:
    
    def test_audio_analysis_tool_function(self):
        """Test the audio analysis tool function"""
        with patch('tools.audio_analysis.AudioAnalysisTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.analyze_file.return_value = {"duration": 120.0, "tempo": 120.0}
            mock_tool_class.return_value = mock_tool
            
            result = audio_analysis_tool("test.mp3")
            
            assert result["duration"] == 120.0
            mock_tool.analyze_file.assert_called_once_with("test.mp3")
    
    def test_batch_audio_analysis_tool_function(self):
        """Test the batch audio analysis tool function"""
        with patch('tools.audio_analysis.AudioAnalysisTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.batch_analyze.return_value = [
                {"duration": 120.0}, 
                {"duration": 180.0}
            ]
            mock_tool_class.return_value = mock_tool
            
            result = batch_audio_analysis_tool(["file1.mp3", "file2.mp3"])
            
            assert result["status"] == "success"
            assert result["count"] == 2
            assert len(result["analyses"]) == 2
            mock_tool.batch_analyze.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])