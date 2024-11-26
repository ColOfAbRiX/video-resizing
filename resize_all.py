#!/usr/bin/env python3

import argparse
import glob
import multiprocessing
import os
import platform
import re
import shutil
import time
from os import path

try:
    import ffmpeg
except ImportError:
    print("Required package python-ffmpeg not installed. Use `python3 -m pip install python-ffmpeg` to use this script.")
    exit(1)

try:
    from colored import fg, attr
    __colored__ = True
except ImportError:
    __colored__ = False
    print("Python colored package not installed. Use `python3 -m pip install colored` to get coloured output.")
    def fg(dummy):
        return ""
    def attr(dummy):
        return ""


def get_video_bitrate(video_file):
    """
    Finds the bitrate of a video file
    """
    video_info = ffmpeg.probe(video_file)
    video_stream = next(stream for stream in video_info["streams"] if stream["codec_type"] == "video")
    return int(video_stream["bit_rate"])

def copy_video(input_file, output_file):
    """
    Copies a video
    """
    shutil.copy2(input_file, output_file)

def process_video_file(input_file, output_file):
    """
    Resizes a video by reducing the bitrate
    """
    print_rel(fg("cyan") + f"COMPRESSING '{input_file}' INTO '{output_file}'" + attr("reset"))
    print("Started at: " + time.strftime("%Y-%m-%d %H:%M") + "\n")

    working_dir = path.dirname(output_file)
    current_dir = os.curdir

    video_bitrate = get_video_bitrate(input_file)
    if config.check_bitrate and video_bitrate < 10485760:
        print(fg("yellow") + "Input bitrate is already small" + attr("reset"))

        print("Copying original video...")
        copy_video(input_file, output_file)

        print("Done.\n")
        return "BITRATE"

    try:
        if not config.dry_run:
            os.makedirs(working_dir, exist_ok=True)
            os.chdir(working_dir)

        ffmpeg_presets[config.ffmpeg_preset](input_file, output_file)
    except Exception as ex:
        print_rel(fg("red") + "ERROR: {}".format(str(ex)) + attr("reset"))
        print("Done.\n")
        return "ERROR"
    finally:
        os.chdir(current_dir)

    try:
        print("Copying attributes...")
        create_time = creation_date(input_file)
        mod_time = path.getmtime(input_file)
        if not config.dry_run:
            os.utime(output_file, (create_time, mod_time))
    except:
        print(fg("red") + "COULD NOT copy attributes" + attr("reset"))

    try:
        print("Checking size...")

        input_size = path.getsize(input_file)
        if not config.dry_run:
            output_size = path.getsize(output_file)

            if config.check_output_size and float(output_size) > float(input_size) * 0.75:
                print(fg("yellow") + "Output file size is not smaller than input file size" + attr("reset"))

                print("Copying original video...")
                copy_video(input_file, output_file)

                print("Done.\n")
                return "SIZE"
    except:
        print(fg("red") + "COULD NOT check size" + attr("reset"))

    print("Done.\n")
    return ""

def ffmpeg_h264_bitrate_2pass(input_file, output_file):
    """
    Encodes a file using H.264 codec, fixed bitrate and 2 passes
    See https://www.mux.com/articles/change-video-bitrate-with-ffmpeg#two-pass-encoding-for-more-precise-bitrate-control
    """
    global config

    print("Running first pass...")
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

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

    print("\nRunning second pass...")
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

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h265_crf(input_file, output_file):
    """
    Encodes a file using H.265 codec and CRF
    """
    global config

    print("Running ffmpeg...")
    first_pass = {
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
        .input(input_file)
        .output(output_file, **first_pass)
        .global_args(*first_pass_global_args)
        .overwrite_output())

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h265_bitrate_2pass(input_file, output_file):
    """
    Encodes a file using H.265 codec, constant bitrate and 2 passes
    """
    global config

    print("Running first pass...")
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

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

    print("\nRunning second pass...")
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

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def ffmpeg_h265_crf_2pass(input_file, output_file):
    """
    Encodes a file using H.265 codec, CRF and 2 passes
    """
    global config

    print("Running first pass...")
    first_pass = {
        "loglevel": "error",
        "c:v": "libx265",
        "crf": config.crf,
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

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

    print("\nRunning second pass...")
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

    print_rel("Command: {}".format(' '.join(cmd.compile())))
    if not config.dry_run:
        cmd.run()

def creation_date(path_to_file):
    """
    Try to get the date that a file was created, falling back to when it was
    last modified if that isn't possible.
    See http://stackoverflow.com/a/39501288 for explanation.
    """
    if platform.system() == 'Windows':
        return os.path.getctime(path_to_file)
    else:
        stat = os.stat(path_to_file)
        try:
            return stat.st_birthtime
        except AttributeError:
            # We're probably on Linux. No easy way to get creation dates here,
            # so we'll settle for when its content was last modified.
            return stat.st_mtime

def print_rel(text):
    """
    Prints a text removing all occurrences of the input_path
    """
    global config

    terminated_input_dir = config.input_dir + os.sep
    text = text.replace(terminated_input_dir, "")

    print(text)

def scan_and_process_videos():
    """
    Finds and processes videos
    """
    global config

    processed_root_path = path.join(config.input_dir, config.processed_dir)

    for current_dir, subdirs, files in os.walk(config.input_dir):
        current_dir = current_dir.replace(config.input_dir, "")[1:]

        if current_dir.startswith(config.processed_dir):
            continue

        for file in files:
            file_name, file_extension = path.splitext(file)
            input_file = path.join(config.input_dir, current_dir, file)
            file_name = to_snake_case(config.prefix + file_name + config.postfix)
            output_file = path.join(processed_root_path, current_dir, file_name) + output_extension

            if not file_extension.lower() in video_extensions or file_name.startswith(config.processed_dir):
                continue

            if in_log_file(input_file):
                print_rel(f"File '{input_file}' already processed, skipping.\n")
                continue

            try:
                state = process_video_file(input_file, output_file)
                add_to_log_file(input_file, state)
            except Exception as ex:
                print_rel(
                    fg("red") + f"Error encountered processing '{input_file}', skipping." + attr("reset") + "\n    ERROR: " + str(ex) + "\n"
                )
                add_to_log_file(input_file, "ERROR")

def get_log_file():
    """
    Gets the name of log file
    """
    global config
    return path.join(config.input_dir, "resize_all.db")

def add_to_log_file(file_name, state = ""):
    """
    Adds an entry into the log file
    """
    global config

    if config.dry_run:
        return

    log_file = get_log_file()
    with open(log_file, "a") as file:
        log_line = (file_name + " " + state).strip()
        file.write(log_line + "\n")

def in_log_file(file_name):
    """
    Checks if an entry is in the log file
    """
    log_file = get_log_file()

    if not path.isfile(log_file):
        return False

    with open(log_file, "r") as file:
        for line in file:
            if len(line) == 0:
                break
            if file_name.strip().lower() == line.strip().lower():
                return True
        return False

def reset_log_file():
    """
    Resets the log file
    """
    log_file = get_log_file()
    with open(log_file, "w") as file:
        file.write("")

def to_snake_case(text):
    return '_'.join(
        re.sub('([A-Z][a-z]+)', r' \1',
        re.sub('([A-Z]+)', r' \1',
        text.replace('-', ' '))).split()).lower()

def clean_ffmpeg():
    global config

    all_to_clean = [ "*.cutree", "*.log" ]

    processed_root_path = path.join(config.input_dir, config.processed_dir)
    print("Cleaning up after ffmpeg")
    for to_clean in all_to_clean:
        for file in glob.glob(path.join(processed_root_path, "**", to_clean), recursive=True):
            if file.strip() != "":
                os.remove(file)

def main():
    """
    Main
    """
    global config

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i", "--input-dir",
        default=".",
        type=lambda x: path.abspath(x),
        help="Input working directory."
    )
    parser.add_argument(
        "-n", "--dry-run",
        default=False,
        action="store_true",
        help="Doesn't actually run ffmpeg."
    )
    parser.add_argument(
        "-p", "--processed-dir",
        default="processed",
        help="Directory where to place the processed files."
    )
    parser.add_argument(
        "-r", "--reset-logfile",
        default=False,
        action="store_true",
        help="Resets the logfile at startup."
    )
    parser.add_argument(
        "-f", "--ffmpeg-preset",
        default="h265_crf_2pass",
        choices=ffmpeg_presets.keys(),
        help="Ffmpeg encoding preset to use."
    )
    parser.add_argument(
        "--prefix",
        default="",
        help="Prefix to add to every file."
    )
    parser.add_argument(
        "--postfix",
        default="",
        help="Postfix to add to every file."
    )
    parser.add_argument(
        "--check-bitrate",
        default=True,
        action="store_false",
        help="Enable/disable the bitrate check."
    )
    parser.add_argument(
        "--check-output-size",
        default=True,
        action="store_false",
        help="Enable/disable the output file size check."
    )
    parser.add_argument(
        "--crf",
        default=24,
        type=int,
        help="Default CRF value for profiles that use it."
    )
    parser.add_argument(
        "--bitrate",
        default="10M",
        help="Default Bitrate value for profiles that use it."
    )
    parser.add_argument(
        "--cpu-count",
        default=int(float(multiprocessing.cpu_count()) * 0.75),
        type=int,
        help="Default Bitrate value for profiles that use it."
    )
    config = parser.parse_args()

    print(f"WORKING UNDER: {config.input_dir}\n")

    if config.reset_logfile:
        reset_log_file()

    scan_and_process_videos()
    clean_ffmpeg()

# Constants
video_extensions = [ ".mp4", ".avi", ".mov" ]
output_extension = ".mp4"
ffmpeg_presets = {
    "h264_bitrate_2pass": ffmpeg_h264_bitrate_2pass,
    "h265_bitrate_2pass": ffmpeg_h265_bitrate_2pass,
    "h265_crf_2pass": ffmpeg_h265_crf_2pass,
    "h265_crf": ffmpeg_h265_crf,
}

if __name__ == "__main__":
    main()
