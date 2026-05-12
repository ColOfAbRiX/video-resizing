#!/usr/bin/env python3
"""
Automatic ffmpeg binary management.
Uses imageio-ffmpeg to provide ffmpeg binaries if system ffmpeg is not found.
"""

import os
import shutil
import sys

try:
    import ffmpeg
except ImportError:
    print("Required package 'ffmpeg-python' not installed. Use `pip install ffmpeg-python` to use this script.")
    sys.exit(1)


def get_ffmpeg_path():
    """
    Returns the path to ffmpeg binary.
    - Checks system PATH first
    - Falls back to imageio-ffmpeg's bundled/managed binary
    """
    # Check system PATH first
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # Fall back to imageio-ffmpeg's bundled binary
    try:
        import imageio_ffmpeg
        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()

        # Set environment variable so ffmpeg-python can find it
        os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path

        return ffmpeg_path
    except ImportError:
        print("ffmpeg not found on system and 'imageio-ffmpeg' package not installed.")
        print("Install with: pip install imageio-ffmpeg")
        sys.exit(1)


def get_ffprobe_path():
    """
    Returns the path to ffprobe binary.
    - Checks system PATH first
    - Falls back to imageio-ffmpeg's bundled/managed binary
    """
    # Check system PATH first
    system_ffprobe = shutil.which("ffprobe")
    if system_ffprobe:
        return system_ffprobe

    # Fall back to imageio-ffmpeg's bundled binary
    try:
        import imageio_ffmpeg
        # imageio-ffmpeg bundles ffprobe alongside ffmpeg
        ffmpeg_dir = os.path.dirname(imageio_ffmpeg.get_ffmpeg_exe())
        ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
        ffprobe_path = os.path.join(ffmpeg_dir, ffprobe_name)

        if os.path.exists(ffprobe_path):
            return ffprobe_path

        return None
    except ImportError:
        return None


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
