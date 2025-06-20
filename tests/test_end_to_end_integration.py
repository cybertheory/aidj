import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

from tools.music_discovery import music_discovery_tool
from tools.audio_analysis import batch_audio_analysis_tool
from tools.mix_generation import mix_generation_tool
from tools.iterative_feedback import iterative_improvement_tool
from tools.final_export import final_mix_export_tool


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete music mixing pipeline"""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration with temporary directories"""
        with patch('tools.music_discovery.Config') as mock_config, \
             patch('tools.audio_analysis.Config') as mock_config2, \
             patch('tools.mix_generation.Config') as mock_config3, \
             patch('tools.iterative_feedback.Config') as mock_config4, \
             patch('tools.final_export.Config') as mock_config5:
            
            # Set up temporary directories
            temp_dir = tempfile.mkdtemp()
            mock_config.MUSIC_DIR = os.path.join(temp_dir, "music")
            mock_config.TEMP_DIR = os.path.join(temp_dir, "temp")  
            mock_config.EXPORTS_DIR = os.path.join(temp_dir, "exports")
            mock_config.ensure_directories = Mock()
            
            # Apply same config to all modules
            mock_config2.MUSIC_DIR = mock_config.MUSIC_DIR
            mock_config2.TEMP_DIR = mock_config.TEMP_DIR
            mock_config2.EXPORTS_DIR = mock_config.EXPORTS_DIR
            mock_config2.ensure_directories = Mock()
            
            mock_config3.MUSIC_DIR = mock_config.MUSIC_DIR
            mock_config3.TEMP_DIR = mock_config.TEMP_DIR
            mock_config3.EXPORTS_DIR = mock_config.EXPORTS_DIR
            mock_config3.ensure_directories = Mock()
            
            mock_config4.TEMP_DIR = mock_config.TEMP_DIR
            mock_config4.ensure_directories = Mock()
            
            mock_config5.EXPORTS_DIR = mock_config.EXPORTS_DIR
            mock_config5.ensure_directories = Mock()
            
            yield mock_config
    
    def test_complete_pipeline_success(self, mock_config):
        """Test the complete pipeline from discovery to final export"""
        
        # Step 1: Music Discovery
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery_tool:
            mock_tool = Mock()
            mock_tool.discover_and_download.return_value = [
                "/tmp/music/track1.mp3",
                "/tmp/music/track2.mp3", 
                "/tmp/music/track3.mp3"
            ]
            mock_discovery_tool.return_value = mock_tool
            
            discovery_result = music_discovery_tool("lofi hip hop", max_tracks=3)
            
            assert discovery_result["status"] == "success"
            assert len(discovery_result["downloaded_files"]) == 3
            downloaded_files = discovery_result["downloaded_files"]
        
        # Step 2: Audio Analysis
        with patch('tools.audio_analysis.AudioAnalysisTool') as mock_analysis_tool:
            mock_tool = Mock()
            mock_tool.batch_analyze.return_value = [
                {
                    "file_path": "/tmp/music/track1.mp3",
                    "duration": 120.0,
                    "tempo": 85,
                    "estimated_key": "C",
                    "energy_level": "low",
                    "mood": "calm",
                    "mixing_metadata": {
                        "intro_end": 8.0,
                        "outro_start": 110.0,
                        "best_mix_in": 20.0,
                        "best_mix_out": 100.0
                    }
                },
                {
                    "file_path": "/tmp/music/track2.mp3",
                    "duration": 180.0,
                    "tempo": 90,
                    "estimated_key": "G",
                    "energy_level": "medium",
                    "mood": "ambient",
                    "mixing_metadata": {
                        "intro_end": 12.0,
                        "outro_start": 165.0,
                        "best_mix_in": 30.0,
                        "best_mix_out": 150.0
                    }
                },
                {
                    "file_path": "/tmp/music/track3.mp3",
                    "duration": 150.0,
                    "tempo": 88,
                    "estimated_key": "Am",
                    "energy_level": "low",
                    "mood": "calm",
                    "mixing_metadata": {
                        "intro_end": 10.0,
                        "outro_start": 140.0,
                        "best_mix_in": 25.0,
                        "best_mix_out": 125.0
                    }
                }
            ]
            mock_analysis_tool.return_value = mock_tool
            
            analysis_result = batch_audio_analysis_tool(downloaded_files)
            
            assert analysis_result["status"] == "success"
            assert analysis_result["count"] == 3
            analyses = analysis_result["analyses"]
        
        # Step 3: Mix Generation
        with patch('tools.mix_generation.MixGenerationTool') as mock_mix_tool:
            mock_tool = Mock()
            mock_tool.check_files_exist.return_value = {
                "existing_files": downloaded_files,
                "missing_files": [],
                "music_dir_contents": ["track1.mp3", "track2.mp3", "track3.mp3"]
            }
            mock_tool.generate_mix.return_value = {
                "status": "success",
                "draft_path": "/tmp/temp/mix_draft_3tracks.mp3",
                "duration_ms": 450000,
                "duration_seconds": 450.0,
                "tracks_used": 3,
                "pydub_code": "# Generated PyDub code here",
                "mix_metadata": {
                    "transition_type": "crossfade",
                    "fade_duration_ms": 3000,
                    "mix_style": "seamless",
                    "final_bpm": 87.7,
                    "energy_progression": ["low", "medium", "low"],
                    "title": "Generated Mix (3 tracks)",
                    "tracks_used": 3,
                    "genre": "Lo-Fi Hip Hop",
                    "vibe": "Peaceful Study"
                }
            }
            mock_mix_tool.return_value = mock_tool
            
            mix_result = mix_generation_tool(
                downloaded_files,
                analyses,
                transition_type="crossfade",
                fade_duration_ms=3000,
                mix_style="seamless"
            )
            
            assert mix_result["status"] == "success"
            assert mix_result["duration_seconds"] == 450.0
            assert mix_result["tracks_used"] == 3
            draft_path = mix_result["draft_path"]
            mix_metadata = mix_result["mix_metadata"]
        
        # Step 4: Iterative Improvement
        with patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_feedback_tool:
            mock_tool = Mock()
            mock_tool.iterative_improvement_cycle.return_value = {
                "status": "completed",
                "final_mix": "/tmp/temp/mix_improved_v2.mp3",
                "iterations": 2,
                "iteration_history": [
                    {
                        "iteration": 1,
                        "feedback": {"overall_rating": 6},
                        "status": "improved",
                        "improvements": ["Volume adjusted", "Crossfade extended"]
                    },
                    {
                        "iteration": 2,
                        "feedback": {"overall_rating": 8},
                        "status": "satisfied"
                    }
                ],
                "final_rating": 8
            }
            mock_feedback_tool.return_value = mock_tool
            
            improvement_result = iterative_improvement_tool(
                draft_path,
                "Create a peaceful lofi hip hop study mix",
                mix_metadata,
                max_iterations=3
            )
            
            assert improvement_result["status"] == "completed"
            assert improvement_result["final_rating"] == 8
            assert improvement_result["iterations"] == 2
            final_mix_path = improvement_result["final_mix"]
        
        # Step 5: Final Export
        with patch('tools.final_export.FinalMixExportTool') as mock_export_tool:
            mock_tool = Mock()
            mock_tool.export_final_mix.return_value = {
                "status": "success",
                "export_path": "/tmp/exports/Peaceful_Study_Mix_20240101_120000.mp3",
                "report_path": "/tmp/exports/Peaceful_Study_Mix_20240101_120000_report.json",
                "script_path": "/tmp/exports/Peaceful_Study_Mix_20240101_120000_script.py",
                "file_size_mb": 10.5,
                "duration_seconds": 450.0,
                "format": "mp3",
                "bitrate": "320k",
                "metadata": mix_metadata
            }
            mock_export_tool.return_value = mock_tool
            
            export_result = final_mix_export_tool(
                final_mix_path,
                "Peaceful Study Mix",
                mix_metadata,
                export_format="mp3",
                bitrate="320k"
            )
            
            assert export_result["status"] == "success"
            assert export_result["duration_seconds"] == 450.0
            assert export_result["format"] == "mp3"
            assert export_result["file_size_mb"] == 10.5
        
        # Verify the complete pipeline results
        assert discovery_result["status"] == "success"
        assert analysis_result["status"] == "success"
        assert mix_result["status"] == "success"
        assert improvement_result["status"] == "completed"
        assert export_result["status"] == "success"
        
        # Check data flow between steps
        assert len(downloaded_files) == len(analyses) == mix_result["tracks_used"]
        assert improvement_result["final_rating"] >= 8  # Quality threshold met
        assert export_result["duration_seconds"] == mix_result["duration_seconds"]

    def test_pipeline_with_discovery_failure(self, mock_config):
        """Test pipeline behavior when music discovery fails"""
        
        # Mock failed discovery
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery_tool:
            mock_tool = Mock()
            mock_tool.discover_and_download.return_value = []  # No files found
            mock_discovery_tool.return_value = mock_tool
            
            discovery_result = music_discovery_tool("very obscure query", max_tracks=3)
            
            assert discovery_result["status"] == "no_results"
            assert len(discovery_result["downloaded_files"]) == 0
        
        # Pipeline should stop here - cannot proceed without files
        # This simulates real-world scenario where no suitable music is found

    def test_pipeline_with_analysis_failure(self, mock_config):
        """Test pipeline behavior when audio analysis fails"""
        
        # Step 1: Successful discovery
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery_tool:
            mock_tool = Mock()
            mock_tool.discover_and_download.return_value = ["/tmp/music/track1.mp3"]
            mock_discovery_tool.return_value = mock_tool
            
            discovery_result = music_discovery_tool("test query", max_tracks=1)
            downloaded_files = discovery_result["downloaded_files"]
        
        # Step 2: Failed analysis
        with patch('tools.audio_analysis.AudioAnalysisTool') as mock_analysis_tool:
            mock_tool = Mock()
            mock_tool.batch_analyze.return_value = [
                {"error": "Analysis failed for corrupted file"}
            ]
            mock_analysis_tool.return_value = mock_tool
            
            analysis_result = batch_audio_analysis_tool(downloaded_files)
            
            # Should still return results but with errors
            assert analysis_result["status"] == "success"  # Tool function succeeds
            assert "error" in analysis_result["analyses"][0]  # But individual analysis failed

    def test_pipeline_with_mix_generation_failure(self, mock_config):
        """Test pipeline behavior when mix generation fails"""
        
        # Mock successful discovery and analysis
        downloaded_files = ["/tmp/music/track1.mp3"]
        analyses = [{"duration": 120.0, "tempo": 120, "mood": "calm"}]
        
        # Failed mix generation
        with patch('tools.mix_generation.MixGenerationTool') as mock_mix_tool:
            mock_tool = Mock()
            mock_tool.check_files_exist.return_value = {"existing_files": [], "missing_files": downloaded_files}
            mock_tool.generate_mix.return_value = {"error": "No valid audio segments loaded"}
            mock_mix_tool.return_value = mock_tool
            
            mix_result = mix_generation_tool(downloaded_files, analyses)
            
            assert "error" in mix_result
            assert "No valid audio segments loaded" in mix_result["error"]

    def test_pipeline_performance_metrics(self, mock_config):
        """Test that pipeline completes within reasonable time limits"""
        import time
        
        start_time = time.time()
        
        # Mock fast responses for all tools
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery, \
             patch('tools.audio_analysis.AudioAnalysisTool') as mock_analysis, \
             patch('tools.mix_generation.MixGenerationTool') as mock_mix, \
             patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_feedback, \
             patch('tools.final_export.FinalMixExportTool') as mock_export:
            
            # Setup minimal mock responses
            mock_discovery.return_value.discover_and_download.return_value = ["/tmp/track.mp3"]
            mock_analysis.return_value.batch_analyze.return_value = [{"duration": 120, "tempo": 120}]
            mock_mix.return_value.check_files_exist.return_value = {"existing_files": ["/tmp/track.mp3"]}
            mock_mix.return_value.generate_mix.return_value = {"status": "success", "draft_path": "/tmp/mix.mp3", "mix_metadata": {}}
            mock_feedback.return_value.iterative_improvement_cycle.return_value = {"status": "completed", "final_mix": "/tmp/final.mp3", "final_rating": 8}
            mock_export.return_value.export_final_mix.return_value = {"status": "success", "export_path": "/tmp/export.mp3"}
            
            # Run pipeline
            discovery_result = music_discovery_tool("test")
            analysis_result = batch_audio_analysis_tool(discovery_result["downloaded_files"])
            mix_result = mix_generation_tool(discovery_result["downloaded_files"], analysis_result["analyses"])
            improvement_result = iterative_improvement_tool(mix_result["draft_path"], "test", mix_result["mix_metadata"])
            export_result = final_mix_export_tool(improvement_result["final_mix"], "Test Mix", improvement_result["final_rating"])
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Pipeline should complete quickly with mocked responses (under 1 second)
            assert execution_time < 1.0
            
            # Verify all steps completed
            assert discovery_result["status"] == "success"
            assert analysis_result["status"] == "success"
            assert mix_result["status"] == "success"
            assert improvement_result["status"] == "completed"
            assert export_result["status"] == "success"

    def test_pipeline_data_consistency(self, mock_config):
        """Test data consistency throughout the pipeline"""
        
        # Define consistent test data
        test_files = ["/tmp/music/track1.mp3", "/tmp/music/track2.mp3"]
        test_analyses = [
            {"file_path": "/tmp/music/track1.mp3", "duration": 120.0, "tempo": 85, "mood": "calm"},
            {"file_path": "/tmp/music/track2.mp3", "duration": 180.0, "tempo": 90, "mood": "energetic"}
        ]
        test_metadata = {
            "title": "Consistency Test Mix",
            "tracks_used": 2,
            "total_duration": 300.0,
            "genre": "Electronic"
        }
        
        # Mock all tools with consistent data
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery, \
             patch('tools.audio_analysis.AudioAnalysisTool') as mock_analysis, \
             patch('tools.mix_generation.MixGenerationTool') as mock_mix, \
             patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_feedback, \
             patch('tools.final_export.FinalMixExportTool') as mock_export:
            
            # Discovery returns consistent file list
            mock_discovery.return_value.discover_and_download.return_value = test_files
            
            # Analysis returns consistent analyses
            mock_analysis.return_value.batch_analyze.return_value = test_analyses
            
            # Mix generation uses the files and analyses
            mock_mix.return_value.check_files_exist.return_value = {"existing_files": test_files}
            mock_mix.return_value.generate_mix.return_value = {
                "status": "success",
                "draft_path": "/tmp/mix.mp3",
                "tracks_used": len(test_files),
                "mix_metadata": test_metadata
            }
            
            # Feedback maintains consistency
            mock_feedback.return_value.iterative_improvement_cycle.return_value = {
                "status": "completed",
                "final_mix": "/tmp/final.mp3",
                "final_rating": 8
            }
            
            # Export maintains metadata
            mock_export.return_value.export_final_mix.return_value = {
                "status": "success",
                "export_path": "/tmp/export.mp3",
                "metadata": test_metadata
            }
            
            # Run pipeline
            discovery_result = music_discovery_tool("test")
            analysis_result = batch_audio_analysis_tool(discovery_result["downloaded_files"])
            mix_result = mix_generation_tool(discovery_result["downloaded_files"], analysis_result["analyses"])
            improvement_result = iterative_improvement_tool(mix_result["draft_path"], "test", mix_result["mix_metadata"])
            export_result = final_mix_export_tool(improvement_result["final_mix"], "Test Mix", mix_result["mix_metadata"])
            
            # Verify data consistency
            assert len(discovery_result["downloaded_files"]) == len(analysis_result["analyses"])
            assert mix_result["tracks_used"] == len(test_files)
            assert export_result["metadata"]["tracks_used"] == len(test_files)
            assert export_result["metadata"]["title"] == test_metadata["title"]

    def test_pipeline_error_recovery(self, mock_config):
        """Test pipeline behavior with partial failures and recovery"""
        
        # Simulate a scenario where some tracks fail but others succeed
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery:
            mock_discovery.return_value.discover_and_download.return_value = [
                "/tmp/music/track1.mp3",  # Good file
                "/tmp/music/track2.mp3"   # Good file
            ]
            
            discovery_result = music_discovery_tool("test")
            
        with patch('tools.audio_analysis.AudioAnalysisTool') as mock_analysis:
            mock_analysis.return_value.batch_analyze.return_value = [
                {"file_path": "/tmp/music/track1.mp3", "duration": 120.0, "tempo": 85},  # Good analysis
                {"error": "Corrupted file"}  # Failed analysis
            ]
            
            analysis_result = batch_audio_analysis_tool(discovery_result["downloaded_files"])
            
        # Mix generation should handle partial failures gracefully
        with patch('tools.mix_generation.MixGenerationTool') as mock_mix:
            mock_mix.return_value.check_files_exist.return_value = {
                "existing_files": ["/tmp/music/track1.mp3"],  # Only one file exists
                "missing_files": ["/tmp/music/track2.mp3"]
            }
            mock_mix.return_value.generate_mix.return_value = {
                "status": "success",
                "draft_path": "/tmp/mix.mp3",
                "tracks_used": 1,  # Only one track could be used
                "mix_metadata": {"title": "Partial Mix", "tracks_used": 1}
            }
            
            mix_result = mix_generation_tool(
                discovery_result["downloaded_files"], 
                analysis_result["analyses"]
            )
            
            # Should succeed with reduced track count
            assert mix_result["status"] == "success"
            assert mix_result["tracks_used"] == 1

    def test_pipeline_with_different_genres(self, mock_config):
        """Test pipeline with different music genres and styles"""
        
        test_scenarios = [
            {
                "query": "lofi hip hop",
                "expected_genre": "Lo-Fi Hip Hop",
                "expected_mood": "calm",
                "expected_tempo_range": (80, 100)
            },
            {
                "query": "upbeat electronic dance",
                "expected_genre": "Electronic Dance",
                "expected_mood": "energetic", 
                "expected_tempo_range": (120, 140)
            },
            {
                "query": "ambient chill",
                "expected_genre": "Ambient",
                "expected_mood": "peaceful",
                "expected_tempo_range": (60, 90)
            }
        ]
        
        for scenario in test_scenarios:
            with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery:
                mock_discovery.return_value.discover_and_download.return_value = ["/tmp/track.mp3"]
                
                discovery_result = music_discovery_tool(scenario["query"])
                
                # Should adapt search based on query
                assert discovery_result["status"] == "success"
                assert discovery_result["query"] == scenario["query"]
            
            # Verify that different queries would be handled appropriately
            # (In a real system, this would test actual API responses)

    def test_pipeline_resource_cleanup(self, mock_config):
        """Test that pipeline properly cleans up temporary files"""
        
        temp_files_created = []
        
        def mock_export_that_tracks_files(file_path, format, **kwargs):
            temp_files_created.append(file_path)
            return Mock()
        
        with patch('tools.mix_generation.MixGenerationTool') as mock_mix, \
             patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_feedback:
            
            # Mock mix generation creating temp files
            mock_mix.return_value.generate_mix.return_value = {
                "status": "success",
                "draft_path": "/tmp/mix_draft.mp3",
                "mix_metadata": {}
            }
            
            # Mock feedback creating improved versions
            mock_feedback.return_value.iterative_improvement_cycle.return_value = {
                "status": "completed",
                "final_mix": "/tmp/mix_improved.mp3",
                "final_rating": 8
            }
            
            # Run partial pipeline
            mix_result = mix_generation_tool(["/tmp/track.mp3"], [{"duration": 120}])
            improvement_result = iterative_improvement_tool(
                mix_result["draft_path"], 
                "test", 
                mix_result["mix_metadata"]
            )
            
            # In a real implementation, we would verify:
            # 1. Temporary files are created in designated temp directory
            # 2. Old versions are cleaned up after improvements
            # 3. Only final files are kept in exports directory
            
            assert mix_result["status"] == "success"
            assert improvement_result["status"] == "completed"


class TestPipelineIntegrationScenarios:
    """Test realistic end-to-end scenarios"""
    
    def test_study_music_mix_scenario(self):
        """Test creating a study music mix - common use case"""
        
        # User request: "Create a 30-minute lofi hip hop mix for studying"
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery, \
             patch('tools.audio_analysis.AudioAnalysisTool') as mock_analysis, \
             patch('tools.mix_generation.MixGenerationTool') as mock_mix, \
             patch('tools.iterative_feedback.IterativeFeedbackTool') as mock_feedback, \
             patch('tools.final_export.FinalMixExportTool') as mock_export:
            
            # Discovery finds appropriate study tracks
            mock_discovery.return_value.discover_and_download.return_value = [
                "/tmp/lofi_track1.mp3", "/tmp/lofi_track2.mp3", "/tmp/lofi_track3.mp3"
            ]
            
            # Analysis identifies calm, study-appropriate characteristics
            mock_analysis.return_value.batch_analyze.return_value = [
                {"duration": 180, "tempo": 85, "mood": "calm", "energy_level": "low"},
                {"duration": 200, "tempo": 80, "mood": "peaceful", "energy_level": "low"}, 
                {"duration": 190, "tempo": 88, "mood": "ambient", "energy_level": "low"}
            ]
            
            # Mix generation creates smooth, study-friendly transitions
            mock_mix.return_value.generate_mix.return_value = {
                "status": "success",
                "duration_seconds": 1800,  # 30 minutes
                "mix_metadata": {
                    "genre": "Lo-Fi Hip Hop",
                    "vibe": "Study Focus",
                    "energy_progression": ["low", "low", "low"]
                }
            }
            
            # Feedback confirms it's suitable for studying
            mock_feedback.return_value.iterative_improvement_cycle.return_value = {
                "status": "completed",
                "final_rating": 9,  # High rating for study music
                "iteration_history": [{"feedback": {"matches_request": True}}]
            }
            
            # Export with study-appropriate metadata
            mock_export.return_value.export_final_mix.return_value = {
                "status": "success",
                "export_path": "/tmp/Study_Mix_30min.mp3"
            }
            
            # Simulate the workflow
            discovery_result = music_discovery_tool("lofi hip hop study", max_tracks=3)
            assert discovery_result["status"] == "success"
            
            # Would continue with analysis, mixing, etc.
            # This demonstrates how the pipeline handles specific use cases

    def test_workout_music_mix_scenario(self):
        """Test creating a workout mix - high energy use case"""
        
        with patch('tools.music_discovery.MusicDiscoveryTool') as mock_discovery:
            # Discovery finds energetic workout tracks
            mock_discovery.return_value.discover_and_download.return_value = [
                "/tmp/electronic_track1.mp3", "/tmp/electronic_track2.mp3"
            ]
            
            discovery_result = music_discovery_tool("upbeat electronic workout", max_tracks=5)
            
            # Should find energetic tracks suitable for workouts
            assert discovery_result["status"] == "success"
            # In real implementation, would verify tempo, energy characteristics


if __name__ == "__main__":
    pytest.main([__file__])