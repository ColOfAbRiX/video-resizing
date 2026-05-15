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
pip install ffmpeg-python colored

# Download and extract FFmpeg if not already present
echo "Checking for FFmpeg binaries..."
if ! which ffmpeg || ! which ffprobe; then
    # Check if binaries exist in extracted directory
    if [ ! -f "venv/bin/ffmpeg" ] || [ ! -f "venv/bin/ffprobe" ]; then
        echo "Downloading FFmpeg binaries..."

        # Download FFmpeg static build for Linux from GitHub
        curl -sLO https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz -o /tmp

        # Extract to venv/bin/
        tar -xf /tmp/ffmpeg-master-latest-linux64-gpl.tar.xz \
            -C venv/bin \
            --strip-components=2 \
            ffmpeg-master-latest-linux64-gpl/bin/ffmpeg ffmpeg-master-latest-linux64-gpl/bin/ffprobe

        echo "✓ FFmpeg binaries installed"
    fi
fi
