# AI Music Mixer 🎵

An intelligent music mixing tool that uses AI to discover, analyze, and blend royalty-free music into seamless mixes. Perfect for content creators, DJs, and music enthusiasts who want to create professional-quality mixes without manual effort.

## Features

- 🤖 **AI-Powered**: Uses GPT-4 to understand your mix requirements and make creative decisions
- 🎵 **Music Discovery**: Automatically finds royalty-free tracks from multiple sources
- 🔊 **Audio Analysis**: Analyzes tempo, key, mood, and optimal mixing points
- 🎛️ **Smart Mixing**: Creates seamless transitions with crossfading and beat matching
- 🔄 **Iterative Improvement**: Gets AI feedback and automatically improves mixes
- 📦 **Complete Export**: Generates final mix with metadata, reports, and reproducible code

## Quick Start

### Installation

```bash
git clone https://github.com/yourusername/ai-music-mixer.git
cd ai-music-mixer
chmod +x setup.sh
./setup.sh
```

### Configuration

1. Edit `.env` file and add your OpenAI API key:
```
OPENAI_API_KEY=your_openai_api_key_here
```

2. Optionally add music service API keys for more sources:
```
JAMENDO_CLIENT_ID=your_jamendo_client_id
FREESOUND_API_KEY=your_freesound_api_key
```

### Usage

#### Command Line

```bash
# Create a mix from a description
python cli.py "Create a dreamy ambient mix for sunset meditation"

# Specify duration
python cli.py "Upbeat electronic workout mix" --duration 10

# Interactive mode
python cli.py --interactive

# Get suggestions
python cli.py --suggest --mood "chill" --genre "lofi"
```

#### Python API

```python
from agent.orchestrator import create_music_mix

result = create_music_mix(
    prompt="Create a progressive house mix with building energy",
    max_duration_minutes=8
)

if result['status'] == 'completed':
    print("Mix created successfully!")
```

## How It Works

1. **Understanding**: AI analyzes your prompt to understand mood, genre, energy, and style requirements

2. **Discovery**: Searches royalty-free music APIs for suitable tracks based on your requirements

3. **Analysis**: Uses librosa and custom algorithms to analyze:
   - Tempo and beat structure
   - Musical key and harmony
   - Energy levels and mood
   - Optimal mixing points

4. **Generation**: Creates initial mix using PyDub with:
   - Smart track ordering
   - Crossfading and beat matching
   - EQ adjustments
   - Volume normalization

5. **Improvement**: AI reviews the mix and applies improvements:
   - Analyzes transition quality
   - Adjusts timing and levels
   - Refines overall flow

6. **Export**: Produces final package with:
   - High-quality MP3/WAV file
   - Detailed metadata
   - Generation report
   - Reproducible PyDub script

## Architecture

```
ai-music-mixer/
├── agent/
│   └── orchestrator.py      # Main AI orchestration
├── tools/
│   ├── music_discovery.py   # Music search and download
│   ├── audio_analysis.py    # Audio feature extraction
│   ├── mix_generation.py    # PyDub mixing engine
│   ├── iterative_feedback.py # AI feedback system
│   └── final_export.py      # Export and packaging
├── config.py               # Configuration management
├── cli.py                  # Command line interface
└── main.py                 # Entry point
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` - Required for AI functionality
- `JAMENDO_CLIENT_ID` - Optional, for Jamendo music source
- `FREESOUND_API_KEY` - Optional, for Freesound effects
- `MUSIC_DIR` - Directory for downloaded music (default: ./music_files)
- `EXPORTS_DIR` - Directory for final exports (default: ./exports)
- `TEMP_DIR` - Temporary files directory (default: ./temp)

### Audio Settings

Default settings in `config.py`:
- Sample Rate: 44.1kHz
- Channels: Stereo
- Export Format: MP3 320kbps
- Analysis Window: 2048 samples

## Examples

### Workout Mix
```bash
python cli.py "Create an intense 45-minute workout mix starting with warm-up beats, building to high-energy electronic, and ending with cool-down ambient"
```

### Study Session
```bash
python cli.py "Peaceful lo-fi hip hop mix for 2-hour study session with consistent energy and no jarring transitions"
```

### Party Mix
```bash
python cli.py "Upbeat dance mix for house party - progressive energy, crowd favorites, seamless mixing" --duration 30
```

## API Reference

### Main Functions

#### `create_music_mix(prompt, max_duration_minutes)`
Creates a complete mix from a text description.

#### `MusicMixerOrchestrator.get_mix_suggestions(mood, genre, duration)`
Generates creative mix prompt suggestions.

### Tool Functions

- `music_discovery_tool()` - Search and download music
- `audio_analysis_tool()` - Analyze single audio file
- `batch_audio_analysis_tool()` - Analyze multiple files
- `mix_generation_tool()` - Generate mix with PyDub
- `iterative_feedback_tool()` - Get AI feedback
- `final_mix_export_tool()` - Export with metadata

## Troubleshooting

### Common Issues

1. **"No OpenAI API key"**
   - Add your API key to `.env` file
   - Ensure you have credits in your OpenAI account

2. **"No music found"**
   - Try different search terms
   - Add music service API keys for more sources
   - Check internet connection

3. **"Audio analysis failed"**
   - Ensure audio files are valid
   - Install additional audio codecs if needed
   - Check file permissions

4. **"Mix generation failed"**
   - Verify PyDub installation
   - Check available disk space
   - Ensure temp directory is writable

### Dependencies

If you encounter issues with audio processing:

```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libsndfile1

# macOS
brew install ffmpeg libsndfile

# Windows
# Download ffmpeg and add to PATH
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- OpenAI for GPT-4 API
- PyDub for audio processing
- Librosa for audio analysis
- Jamendo and Freesound for royalty-free music

## Support

- 📧 Email: support@example.com
- 🐛 Issues: GitHub Issues
- 💬 Discussions: GitHub Discussions
- 📖 Wiki: GitHub Wiki

---

**Happy Mixing! 🎵**# aidj
