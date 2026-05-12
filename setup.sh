#!/bin/bash
set -e

echo "=== Video Resizing Project Setup ==="
echo ""

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found. Please install Python 3 first."
    exit 1
fi

echo "Using Python: $(python3 --version)"
echo ""

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Verify we're in the virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "✓ Virtual environment activated"
echo ""

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install ffmpeg-python imageio-ffmpeg

echo ""
echo "✓ All dependencies installed"
echo ""

# Verify installation
echo "Verifying installation..."
python3 -c "import ffmpeg; print('✓ ffmpeg-python: OK')"

echo ""
echo "=== Setup Complete! ==="
echo ""
echo "To use the project, run:"
echo "  source venv/bin/activate"
echo "  python resize_all.py -i /path/to/videos"
echo ""
