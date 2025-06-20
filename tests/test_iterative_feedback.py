import pytest
import json
from unittest.mock import Mock, patch, MagicMock, mock_open

from tools.iterative_feedback import IterativeFeedbackTool, iterative_feedback_tool, iterative_improvement_tool


class TestIterativeFeedbackTool:
    
    @pytest.fixture
    def tool(self):
        with patch('openai.OpenAI'):
            return IterativeFeedbackTool()
    
    @pytest.fixture
    def mock_feedback_response(self):
        """Mock GPT-4 feedback response"""
        return {
            "overall_rating": 7,
            "matches_request": True,
            "feedback": "Good mix overall, but transitions could be smoother",
            "specific_issues": [
                {"timestamp_ms": 60000, "issue": "Abrupt transition", "severity": "medium"}
            ],
            "suggestions": [
                {"action": "crossfade", "parameters": {"duration_ms": 4000}, "reason": "Smoother transitions"}
            ],
            "energy_flow": "Good energy progression",
            "transition_quality": "Needs improvement",
            "technical_issues": ["Volume inconsistency"],
            "creative_suggestions": ["Add subtle reverb"]
        }
    
    @patch('base64.b64encode')
    @patch('builtins.open', new_callable=mock_open, read_data=b'fake_audio_data')
    def test_encode_audio_to_base64(self, mock_file, mock_b64encode, tool):
        """Test audio file encoding to base64"""
        mock_b64encode.return_value = b'ZmFrZV9hdWRpb19kYXRh'
        
        result = tool.encode_audio_to_base64("test.mp3")
        
        assert result == "ZmFrZV9hdWRpb19kYXRh"
        mock_file.assert_called_once_with("test.mp3", "rb")
        mock_b64encode.assert_called_once_with(b'fake_audio_data')
    
    @patch('os.path.exists', return_value=False)
    def test_get_mix_feedback_file_not_found(self, mock_exists, tool):
        """Test feedback when file doesn't exist"""
        result = tool.get_mix_feedback("nonexistent.mp3", "Test prompt")
        
        assert "error" in result
        assert "not found" in result["error"]
    
    @patch('os.path.exists', return_value=True)
    def test_get_mix_feedback_success(self, mock_exists, tool, mock_feedback_response):
        """Test successful feedback generation"""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(mock_feedback_response)
        
        with patch.object(tool.client.chat.completions, 'create', return_value=mock_response), \
             patch.object(tool, '_get_audio_duration', return_value=180.0):
            
            result = tool.get_mix_feedback("test.mp3", "Create a chill lofi mix", {"bpm": 120})
            
            assert result["status"] == "success"
            assert result["feedback"]["overall_rating"] == 7
            assert result["feedback"]["matches_request"] == True
            assert len(result["feedback"]["suggestions"]) == 1
            assert "file_analyzed" in result
    
    @patch('os.path.exists', return_value=True)
    def test_get_mix_feedback_json_parse_error(self, mock_exists, tool):
        """Test feedback when JSON parsing fails"""
        # Mock OpenAI response with invalid JSON
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "This is not valid JSON feedback"
        
        with patch.object(tool.client.chat.completions, 'create', return_value=mock_response), \
             patch.object(tool, '_get_audio_duration', return_value=180.0), \
             patch.object(tool, '_parse_text_feedback', return_value={"overall_rating": 5}) as mock_parse:
            
            result = tool.get_mix_feedback("test.mp3", "Test prompt")
            
            assert result["status"] == "success"
            assert result["feedback"]["overall_rating"] == 5
            mock_parse.assert_called_once()
    
    @patch('os.path.exists', return_value=True)
    def test_get_mix_feedback_api_error(self, mock_exists, tool):
        """Test feedback when OpenAI API fails"""
        with patch.object(tool.client.chat.completions, 'create', side_effect=Exception("API Error")):
            result = tool.get_mix_feedback("test.mp3", "Test prompt")
            
            assert "error" in result
            assert "Feedback generation failed" in result["error"]
    
    def test_get_audio_duration(self, tool):
        """Test audio duration calculation"""
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=120000)  # 2 minutes in ms
        
        with patch('tools.iterative_feedback.AudioSegment.from_file', return_value=mock_audio):
            result = tool._get_audio_duration("test.mp3")
            
            assert result == 120.0
    
    def test_get_audio_duration_error(self, tool):
        """Test audio duration calculation with error"""
        with patch('tools.iterative_feedback.AudioSegment.from_file', side_effect=Exception("Load failed")):
            result = tool._get_audio_duration("test.mp3")
            
            assert result == 0.0
    
    def test_parse_text_feedback(self, tool):
        """Test text feedback parsing"""
        feedback_text = "This is an excellent mix with good transitions but the volume needs adjustment"
        
        result = tool._parse_text_feedback(feedback_text, "Create a chill mix")
        
        assert result["overall_rating"] == 9  # Should detect "excellent"
        assert result["feedback"] == feedback_text
        assert len(result["suggestions"]) > 0  # Should suggest volume adjustment
    
    def test_apply_feedback_suggestions(self, tool):
        """Test applying feedback suggestions"""
        mock_audio = Mock()
        mock_audio.__len__ = Mock(return_value=180000)
        mock_audio.__add__ = Mock(return_value=mock_audio)
        mock_audio.__getitem__ = Mock(return_value=mock_audio)
        mock_audio.fade_in.return_value = mock_audio
        mock_audio.fade_out.return_value = mock_audio
        mock_audio.export = Mock()
        
        feedback = {
            "suggestions": [
                {"action": "volume_adjust", "parameters": {"gain_db": 2.0}},
                {"action": "trim", "parameters": {"start_ms": 5000, "end_ms": 175000}},
                {"action": "fade_adjustment", "parameters": {"fade_in_ms": 1000, "fade_out_ms": 2000}}
            ]
        }
        
        with patch('tools.iterative_feedback.AudioSegment.from_file', return_value=mock_audio), \
             patch('tools.iterative_feedback.normalize', return_value=mock_audio):
            
            result = tool.apply_feedback_suggestions("input.mp3", feedback, "output.mp3")
            
            assert result["status"] == "success"
            assert result["output_file"] == "output.mp3"
            assert len(result["applied_changes"]) == 3
            mock_audio.export.assert_called_once()
    
    def test_apply_feedback_suggestions_error(self, tool):
        """Test applying feedback suggestions with error"""
        with patch('tools.iterative_feedback.AudioSegment.from_file', side_effect=Exception("Load failed")):
            result = tool.apply_feedback_suggestions("input.mp3", {}, "output.mp3")
            
            assert "error" in result
            assert "Failed to apply feedback" in result["error"]
    
    @patch('tools.iterative_feedback.Config')
    def test_iterative_improvement_cycle(self, mock_config, tool):
        """Test the iterative improvement cycle"""
        mock_config.TEMP_DIR = "/tmp"
        
        # Mock feedback responses with improving ratings
        feedback_responses = [
            {"status": "success", "feedback": {"overall_rating": 6, "suggestions": []}},
            {"status": "success", "feedback": {"overall_rating": 8, "suggestions": []}},  # Satisfactory rating
        ]
        
        improvement_responses = [
            {"status": "success", "applied_changes": ["Volume adjusted"], "output_file": "/tmp/mix_improved_v1.mp3"}
        ]
        
        with patch.object(tool, 'get_mix_feedback', side_effect=feedback_responses), \
             patch.object(tool, 'apply_feedback_suggestions', side_effect=improvement_responses):
            
            result = tool.iterative_improvement_cycle(
                "initial_mix.mp3", 
                "Create a chill mix", 
                {"genre": "lofi"}, 
                max_iterations=3
            )
            
            assert result["status"] == "completed"
            assert result["iterations"] == 2
            assert result["final_rating"] == 8
            assert len(result["iteration_history"]) == 2
            assert result["iteration_history"][1]["status"] == "satisfied"


class TestIterativeFeedbackToolFunctions:
    
    def test_iterative_feedback_tool_function(self):
        """Test the iterative feedback tool function"""
        with patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.get_mix_feedback.return_value = {"status": "success", "feedback": {"overall_rating": 8}}
            mock_tool_class.return_value = mock_tool
            
            result = iterative_feedback_tool("test.mp3", "Create a chill mix", {"genre": "lofi"})
            
            assert result["status"] == "success"
            assert result["feedback"]["overall_rating"] == 8
            mock_tool.get_mix_feedback.assert_called_once()
    
    @patch('tools.iterative_feedback.Config.ensure_directories')
    def test_iterative_improvement_tool_function(self, mock_ensure_dirs):
        """Test the iterative improvement tool function"""
        with patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_tool_class:
            mock_tool = Mock()
            mock_tool.iterative_improvement_cycle.return_value = {
                "status": "completed",
                "final_rating": 9,
                "iterations": 2
            }
            mock_tool_class.return_value = mock_tool
            
            result = iterative_improvement_tool(
                "test.mp3", 
                "Create energetic mix", 
                {"genre": "electronic"}, 
                max_iterations=3
            )
            
            assert result["status"] == "completed"
            assert result["final_rating"] == 9
            assert result["iterations"] == 2
            mock_tool.iterative_improvement_cycle.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])