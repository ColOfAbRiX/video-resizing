#!/usr/bin/env python3

from myio import *
from os import path
import glob
import ffmpeg

def get_video_bitrate(video_file):
    """
    Finds the bitrate of a video file
    """
    import ffmpeg

    video_file = os.path.abspath(video_file)
    video_file = to_windows_path(video_file)
    try:
        video_info = ffmpeg.probe(video_file)
        video_stream = next(stream for stream in video_info["streams"] if stream["codec_type"] == "video")
        return int(video_stream.get("bit_rate", 0))
    except ffmpeg.Error as e:
        print(f"Error probing file: {video_file}")
        print("FFPROBE STDOUT:", e.stdout.decode())
        print("FFPROBE STDERR:", e.stderr.decode())
        raise

def ffmpeg_h264_crf(config, input_file, output_file, extra):
    """
    Encodes a file using H.264 codec and CRF
    """
    input_file = to_windows_path(input_file)
    output_file = to_windows_path(output_file)

    input_options = {}

    if extra["rotation"] != 0:
        input_options["display_rotation"] = extra["rotation"]

    printlog(config, "Running ffmpeg...")
    output_options = {
        "loglevel": "error",
        "c:v": "libx264",
        "crf": config.crf,
        "preset": "medium",
        "c:a": "aac",
        "b:a": "160k",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    first_pass_global_args = [
        "-stats",
        "-hide_banner",
    ]

    cmd = (ffmpeg
        .input(input_file, **input_options)
        .output(output_file, **output_options)
        .global_args(*first_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h264_bitrate_2pass(config, input_file, output_file, extra):
    """
    Encodes a file using H.264 codec, fixed bitrate and 2 passes
    See https://www.mux.com/articles/change-video-bitrate-with-ffmpeg#two-pass-encoding-for-more-precise-bitrate-control
    """
    input_file = to_windows_path(input_file)
    output_file = to_windows_path(output_file)

    input_options = {}

    if extra["rotation"] != 0:
        input_options["display_rotation"] = extra["rotation"]

    printlog(config, "Running first pass...")
    first_pass = {
        "loglevel": "error",
        "c:v": "libx264",
        "b:v": config.bitrate,
        "pass": 1,
        "f": "null",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    first_pass_global_args = [
        "-an",
        "-stats",
        "-hide_banner",
    ]
    cmd = (ffmpeg
        .input(input_file)
        .output(os.devnull, **first_pass)
        .global_args(*first_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

    printlog(config, "\nRunning second pass...")
    second_pass = {
        "loglevel": "error",
        "c:v": "libx264",
        "b:v": config.bitrate,
        "pass": 2,
        "c:a": "aac",
        "b:a": "10k",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    second_pass_global_args = [
        "-stats",
        "-hide_banner",
    ]
    cmd = (ffmpeg
        .input(input_file)
        .output(output_file , **second_pass)
        .global_args(*second_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h265_crf(config, input_file, output_file, extra):
    """
    Encodes a file using H.265 codec and CRF
    """
    input_file = to_windows_path(input_file)
    output_file = to_windows_path(output_file)

    input_options = {}

    if extra["rotation"] != 0:
        input_options["display_rotation"] = extra["rotation"]

    printlog(config, "Running ffmpeg...")
    output_options = {
        "loglevel": "error",
        "c:v": "libx265",
        "crf": config.crf,
        "preset": "medium",
        "x265-params": f"pools={config.cpu_count}",
        "c:a": "aac",
        "b:a": "160k",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    first_pass_global_args = [
        "-stats",
        "-hide_banner",
    ]

    cmd = (ffmpeg
        .input(input_file, **input_options)
        .output(output_file, **output_options)
        .global_args(*first_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h265_bitrate_2pass(config, input_file, output_file, extra):
    """
    Encodes a file using H.265 codec, constant bitrate and 2 passes
    """
    input_file = to_windows_path(input_file)
    output_file = to_windows_path(output_file)

    input_options = {}

    if extra["rotation"] != 0:
        input_options["display_rotation"] = extra["rotation"]

    printlog(config, "Running first pass...")
    first_pass = {
        "loglevel": "error",
        "c:v": "libx265",
        "b:v": config.bitrate,
        "pass": 1,
        "x265-params": f"pass=1f;pools={config.cpu_count}",
        "f": "null",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    first_pass_global_args = [
        "-an",
        "-stats",
        "-hide_banner",
    ]
    cmd = (ffmpeg
        .input(input_file)
        .output(os.devnull, **first_pass)
        .global_args(*first_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

    printlog(config, "\nRunning second pass...")
    second_pass = {
        "loglevel": "error",
        "c:v": "libx265",
        "b:v": config.bitrate,
        "pass": 2,
        "x265-params": f"pass=2f;pools={config.cpu_count}",
        "c:a": "aac",
        "b:a": "10k",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    second_pass_global_args = [
        "-stats",
        "-hide_banner",
    ]
    cmd = (ffmpeg
        .input(input_file)
        .output(output_file , **second_pass)
        .global_args(*second_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h265_crf_2pass(config, input_file, output_file, extra):
    """
    Encodes a file using H.265 codec, CRF and 2 passes
    """
    input_file = to_windows_path(input_file)
    output_file = to_windows_path(output_file)

    input_options = {}

    if extra["rotation"] != 0:
        input_options["display_rotation"] = extra["rotation"]

    printlog(config, "Running first pass...")
    first_pass = {
        "loglevel": "error",
        "c:v": "libx265",
        "crf": config.crf,
        "pass": 1,
        "x265-params": f"pass=1f;pools={config.cpu_count}",
        "f": "null",
        "movflags": "use_metadata_tags",
        "map_metadata": "0"
    }
    first_pass_global_args = [
        "-an",
        "-stats",
        "-hide_banner",
    ]
    cmd = (ffmpeg
        .input(input_file)
        .output(os.devnull, **first_pass)
        .global_args(*first_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

    printlog(config, "\nRunning second pass...")
    second_pass = {
        "loglevel": "error",
        "c:v": "libx265",
        "crf": config.crf,
        "pass": 2,
        "x265-params": f"pass=2f;pools={config.cpu_count}",
        "c:a": "aac",
        "b:a": "10k",
        "movflags": "use_metadata_tags",
        "map_metadata": "0",
    }
    second_pass_global_args = [
        "-stats",
        "-hide_banner",
    ]
    cmd = (ffmpeg
        .input(input_file)
        .output(output_file , **second_pass)
        .global_args(*second_pass_global_args)
        .overwrite_output())

    printlog(config, "Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def clean_ffmpeg(config):
    """
    Cleans up temporary ffmpeg files
    """
    all_to_clean = [ "*.cutree", "*.log" ]

    processed_root_path = path.join(config.input_dir, config.processed_dir)
    printlog(config, "Cleaning up after ffmpeg")
    for to_clean in all_to_clean:
        for file in glob.glob(path.join(processed_root_path, "**", to_clean), recursive=True):
            if file.strip() != "":
                os.remove(file)

ffmpeg_presets = {
    "h264_bitrate_2pass": ffmpeg_h264_bitrate_2pass,
    "h264_crf": ffmpeg_h264_crf,
    "h265_bitrate_2pass": ffmpeg_h265_bitrate_2pass,
    "h265_crf_2pass": ffmpeg_h265_crf_2pass,
    "h265_crf": ffmpeg_h265_crf,
}
