#!/usr/bin/env python3
"""
FFmpeg binary path discovery for WSL/Linux.
Discovers and returns paths to ffmpeg and ffprobe binaries.
Assumes virtual environment is already active and binaries are available.
"""

import os
import shutil


def get_ffmpeg_path():
    """
    Returns the path to ffmpeg binary.
    - Checks system PATH first
    - Falls back to locally managed binaries in venv/bin/
    - Assumes binaries are available (downloaded by setup.sh)
    """
    # 1. Check if ffmpeg is in PATH
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # 2. Check in virtual environment's bin directory (./venv/bin/)
    venv_bin = os.path.join(os.getcwd(), 'venv', 'bin')

    # Check for direct binary
    ffmpeg_in_venv = os.path.join(venv_bin, 'ffmpeg')
    if os.path.isfile(ffmpeg_in_venv) and os.access(ffmpeg_in_venv, os.X_OK):
        return ffmpeg_in_venv

    # If not found, raise an error - binaries should be available via setup.sh
    raise FileNotFoundError(
        "ffmpeg binary not found. Please run setup.sh to install dependencies."
    )


def get_ffprobe_path():
    """
    Returns the path to ffprobe binary.
    - Checks system PATH first
    - Falls back to locally managed binaries in venv/bin/
    - Assumes binaries are available (downloaded by setup.sh)
    """
    # 1. Check if ffprobe is in PATH
    ffprobe_in_path = shutil.which('ffprobe')
    if ffprobe_in_path:
        return ffprobe_in_path

    # 2. Check in virtual environment's bin directory (./venv/bin/)
    venv_bin = os.path.join(os.getcwd(), 'venv', 'bin')

    # Check for direct binary
    ffprobe_in_venv = os.path.join(venv_bin, 'ffprobe')
    if os.path.isfile(ffprobe_in_venv) and os.access(ffprobe_in_venv, os.X_OK):
        return ffprobe_in_venv

    # If not found, raise an error - binaries should be available via setup.sh
    raise FileNotFoundError(
        "ffprobe binary not found. Please run setup.sh to install dependencies."
    )


def setup_ffmpeg():
    """
    Ensures ffmpeg is available and configures ffmpeg-python to use it.
    Call this at the start of the application before any ffmpeg operations.

    Returns the path to the ffmpeg binary being used.
    """
    ffmpeg_path = get_ffmpeg_path()
    ffprobe_path = get_ffprobe_path()

    # Configure ffmpeg-python to use our binaries
    import ffmpeg

    ffmpeg._run.FFMPEG_BINARY = ffmpeg_path
    if ffprobe_path:
        ffmpeg._run.FFPROBE_BINARY = ffprobe_path

    return ffmpeg_path
