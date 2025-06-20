#!/bin/bash

# AI Music Mixer Setup Script

echo "🎵 AI Music Mixer - Setup Script"
echo "=================================="

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

# Create directories
echo "Creating directories..."
mkdir -p music_files
mkdir -p exports
mkdir -p temp

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env configuration file..."
    cat > .env << EOF
# AI Music Mixer Configuration
OPENAI_API_KEY=your_openai_api_key_here
JAMENDO_CLIENT_ID=your_jamendo_client_id_here
FREESOUND_API_KEY=your_freesound_api_key_here

# Optional: Custom directories
# MUSIC_DIR=./music_files
# EXPORTS_DIR=./exports
# TEMP_DIR=./temp
EOF
    echo "⚠️  Please edit .env file and add your API keys!"
else
    echo "✅ .env file already exists"
fi

# Make CLI executable
chmod +x cli.py

echo ""
echo "✅ Setup completed!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Optionally add Jamendo and Freesound API keys for more music sources"
echo "3. Run: python cli.py --help"
echo "4. Or try: python cli.py \"Create a chill ambient mix\""
echo ""
echo "To activate the environment later: source venv/bin/activate"
