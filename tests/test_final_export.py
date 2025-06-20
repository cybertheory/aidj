import pytest
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tools.final_export import FinalMixExportTool, final_mix_export_tool, create_mix_package_tool


class TestFinalMixExportTool:
    
    @pytest.fixture
    def tool(self):
        return FinalMixExportTool()
    
    @pytest.fixture
    def mock_audio_segment(self):
        """Create a mock AudioSegment for testing"""
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=180000)  # 3 minutes
        mock_audio.max_dBFS = -3.0
        mock_audio.dBFS = -12.0
        mock_audio.__add__ = Mock(return_value=mock_audio)
        mock_audio.fade_in.return_value = mock_audio
        mock_audio.fade_out.return_value = mock_audio
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        mock_audio.export = Mock()
        return mock_audio
    
    @pytest.fixture
    def sample_metadata(self):
        return {
            "title": "Test Mix",
            "artist": "AI Mixer",
            "genre": "Electronic",
            "bpm": 125,
            "vibe": "Energetic",
            "tracks_used": 3,
            "mix_style": "seamless",
            "pydub_code": "# Test code"
        }
    
    @patch('tools.final_export.Config.ensure_directories')
    @patch('os.path.exists', return_value=True)
    @patch('os.path.getsize', return_value=10485760)  # 10MB
    def test_export_final_mix_success(self, mock_getsize, mock_exists, mock_ensure_dirs, 
                                      tool, mock_audio_segment, sample_metadata):
        """Test successful final mix export"""
        with patch('tools.final_export.AudioSegment.from_file', return_value=mock_audio_segment), \
             patch.object(tool, '_apply_final_mastering', return_value=mock_audio_segment), \
             patch.object(tool, '_add_metadata_tags'), \
             patch.object(tool, '_create_mix_report', return_value="/path/to/report.json"), \
             patch.object(tool, '_save_pydub_script', return_value="/path/to/script.py"):
            
            result = tool.export_final_mix("input.mp3", "Test Mix", sample_metadata)
            
            assert result["status"] == "success"
            assert "export_path" in result
            assert "report_path" in result
            assert "script_path" in result
            assert result["file_size_mb"] == 10.0
            assert result["duration_seconds"] == 180.0
            assert result["format"] == "mp3"
            assert result["bitrate"] == "320k"
    
    def test_export_final_mix_file_not_found(self, tool):
        """Test export when source file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            result = tool.export_final_mix("nonexistent.mp3", "Test", {})
            
            assert "error" in result
            assert "not found" in result["error"]
    
    def test_apply_final_mastering(self, tool, mock_audio_segment):
        """Test final mastering application"""
        with patch('tools.final_export.normalize', return_value=mock_audio_segment), \
             patch('tools.final_export.compress_dynamic_range', return_value=mock_audio_segment):
            
            result = tool._apply_final_mastering(mock_audio_segment, {})
            
            assert result is not None
    
    @patch('tools.final_export.MP3')
    def test_add_metadata_tags(self, mock_mp3, tool, sample_metadata):
        """Test metadata tag addition"""
        mock_audio_file = Mock()
        mock_audio_file.tags = Mock()
        mock_mp3.return_value = mock_audio_file
        
        # Test successful tag addition
        tool._add_metadata_tags("test.mp3", "Test Mix", sample_metadata)
        
        mock_audio_file.tags.add.assert_called()
        mock_audio_file.save.assert_called_once()
    
    @patch('builtins.open', create=True)
    @patch('json.dump')
    @patch('os.stat')
    def test_create_mix_report(self, mock_stat, mock_json_dump, mock_open, tool, sample_metadata):
        """Test mix report creation"""
        mock_stat.return_value.st_size = 10485760
        
        result = tool._create_mix_report("/path/to/mix.mp3", "Test Mix", sample_metadata)
        
        assert result.endswith("_report.json")
        mock_open.assert_called()
        mock_json_dump.assert_called()
    
    @patch('builtins.open', create=True)
    @patch('os.chmod')
    def test_save_pydub_script(self, mock_chmod, mock_open, tool, sample_metadata):
        """Test PyDub script saving"""
        result = tool._save_pydub_script("/path/to/mix.mp3", sample_metadata)
        
        assert result.endswith("_script.py")
        mock_open.assert_called()
        mock_chmod.assert_called()
    
    @patch('os.makedirs')
    @patch('shutil.copy2')
    @patch('os.listdir', return_value=['mix.mp3', 'report.json', 'script.py', 'README.md'])
    def test_create_mix_package(self, mock_listdir, mock_copy, mock_makedirs, tool):
        """Test mix package creation"""
        export_result = {
            "status": "success",
            "export_path": "/path/to/mix.mp3",
            "report_path": "/path/to/report.json",
            "script_path": "/path/to/script.py",
            "metadata": {"title": "Test Mix"}
        }
        
        with patch.object(tool, '_create_package_readme'):
            result = tool.create_mix_package(export_result)
            
            assert result["status"] == "success"
            assert "package_path" in result
            assert "files_included" in result
            mock_makedirs.assert_called()
            mock_copy.assert_called()
    
    def test_create_mix_package_invalid_result(self, tool):
        """Test package creation with invalid export result"""
        result = tool.create_mix_package({"status": "error"})
        
        assert "error" in result


class TestFinalExportToolFunctions:
    
    @patch('tools.final_export.Config.ensure_directories')
    def test_final_mix_export_tool_function(self, mock_ensure_dirs):
        """Test the final mix export tool function"""
        with patch('tools.final_export.FinalMixExportTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.export_final_mix.return_value = {"status": "success"}
            mock_tool_class.return_value = mock_tool
            
            result = final_mix_export_tool("input.mp3", "Test Mix", {"genre": "Electronic"})
            
            assert result["status"] == "success"
            mock_tool.export_final_mix.assert_called_once()
    
    def test_create_mix_package_tool_function(self):
        """Test the create mix package tool function"""
        with patch('tools.final_export.FinalMixExportTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.create_mix_package.return_value = {"status": "success"}
            mock_tool_class.return_value = mock_tool
            
            export_result = {"status": "success", "export_path": "/path/to/mix.mp3"}
            result = create_mix_package_tool(export_result)
            
            assert result["status"] == "success"
            mock_tool.create_mix_package.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])