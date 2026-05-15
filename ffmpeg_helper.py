#!/usr/bin/env python3
"""
Automatic ffmpeg binary management for WSL/Linux.
Downloads and manages FFmpeg binaries if not found in PATH.
Assumes virtual environment is already active.
"""

import os
import shutil
import sys
import tarfile
import tempfile
import urllib.request


def get_ffmpeg_path():
    """
    Returns the path to ffmpeg binary.
    - Checks system PATH first
    - Falls back to locally managed binaries in venv/bin/
    - Downloads if necessary
    """
    # 1. Check if ffmpeg is in PATH
    ffmpeg_in_path = shutil.which('ffmpeg')
    if ffmpeg_in_path:
        return ffmpeg_in_path

    # 2. Check in virtual environment's bin directory (./venv/bin/)
    venv_bin = os.path.join(os.getcwd(), 'venv', 'bin')
    ffmpeg_in_venv = os.path.join(venv_bin, 'ffmpeg')
    if os.path.isfile(ffmpeg_in_venv) and os.access(ffmpeg_in_venv, os.X_OK):
        return ffmpeg_in_venv

    # 3. Download if not found (Linux/WSL only)
    # Download and return the path
    ffmpeg_path, _ = _download_ffmpeg_linux(venv_bin)
    return ffmpeg_path


def get_ffprobe_path():
    """
    Returns the path to ffprobe binary.
    - Checks system PATH first
    - Falls back to locally managed binaries in venv/bin/
    - Downloads if necessary
    """
    # 1. Check if ffprobe is in PATH
    ffprobe_in_path = shutil.which('ffprobe')
    if ffprobe_in_path:
        return ffprobe_in_path

    # 2. Check in virtual environment's bin directory (./venv/bin/)
    venv_bin = os.path.join(os.getcwd(), 'venv', 'bin')
    ffprobe_in_venv = os.path.join(venv_bin, 'ffprobe')
    if os.path.isfile(ffprobe_in_venv) and os.access(ffprobe_in_venv, os.X_OK):
        return ffprobe_in_venv

    # 3. Download if not found (Linux/WSL only)
    # Download and return the path
    _, ffprobe_path = _download_ffmpeg_linux(venv_bin)
    return ffprobe_path


def _download_ffmpeg_linux(destination_dir):
    """
    Download FFmpeg static build for Linux from GitHub.
    Uses BtbN's FFmpeg builds.
    """
    # Create destination directory if it doesn't exist
    os.makedirs(destination_dir, exist_ok=True)

    # URL for latest FFmpeg static build (Linux, 64-bit, GPL)
    url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz"

    print("Downloading FFmpeg from GitHub...")

    # Download to temporary file
    with urllib.request.urlopen(url) as response, \
         tempfile.NamedTemporaryFile(suffix='.tar.xz', delete=False) as tmp_file:
        shutil.copyfileobj(response, tmp_file)
        tmp_path = tmp_file.name

    print("Download complete, extracting...")

    try:
        # Extract the tarball
        with tarfile.open(tmp_path, 'r:xz') as tar:
            # Find the top-level directory in the tarball
            members = tar.getmembers()
            if not members:
                raise RuntimeError("Downloaded archive is empty")

            # Find the first directory entry (top-level directory)
            top_dir = None
            for member in members:
                if member.isdir():
                    # Remove trailing slash if present
                    dir_name = member.name.rstrip('/')
                    # This should be a top-level directory (no internal slashes)
                    if '/' not in dir_name:
                        top_dir = dir_name
                        break

            if top_dir is None:
                # Fallback: use the first member's directory path
                first_member = members[0]
                dir_name = os.path.dirname(first_member.name)
                # Remove any leading ./ or similar
                while dir_name.startswith('./') or dir_name.startswith('.\\'):
                    dir_name = dir_name[2:]
                top_dir = dir_name

            # Extract all files
            tar.extractall(path=destination_dir)

        print("Extraction complete.")

        # Construct paths to the binaries (they are in the bin/ subdirectory)
        extracted_dir = os.path.join(destination_dir, top_dir)
        ffmpeg_path = os.path.join(extracted_dir, 'bin', 'ffmpeg')
        ffprobe_path = os.path.join(extracted_dir, 'bin', 'ffprobe')

        # Make binaries executable
        os.chmod(ffmpeg_path, 0o755)
        os.chmod(ffprobe_path, 0o755)

        print("FFmpeg binaries ready.")
        return ffmpeg_path, ffprobe_path
    finally:
        # Clean up temporary file
        os.unlink(tmp_path)


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
