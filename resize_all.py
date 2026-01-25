#!/usr/bin/env python3

from ffmpeglayer import *
from filenameprofiles import filename_presets
from logfile import *
from myio import *
from os import path
import argparse
import multiprocessing
import os
import platform
import shutil
import time
import traceback

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

def copy_video(input_file, output_file):
    """
    Copies a video
    """
    global config

    if not config.dry_run:
        output_dir = path.dirname(output_file)
        os.makedirs(output_dir, exist_ok=True)
        shutil.copy2(input_file, output_file)

def process_video_file(input_file, output_file):
    """
    Resizes a video by reducing the bitrate
    """
    printlog(config, fg("cyan") + f"COMPRESSING '{input_file}' INTO '{output_file}'" + attr("reset"))
    printlog(config, "Started at: " + time.strftime("%Y-%m-%d %H:%M") + "\n")

    working_dir = path.dirname(output_file)
    current_dir = os.curdir

    video_bitrate = get_video_bitrate(input_file)
    # if config.check_bitrate and video_bitrate < 10485760:
    #     printlog(config, fg("yellow") + "Input bitrate is already small" + attr("reset"))

    #     printlog(config, "Copying original video...")
    #     copy_video(input_file, output_file)

    #     printlog(config, "Done.\n")
    #     return "OK BITRATE"

    try:
        if not config.dry_run:
            os.makedirs(working_dir, exist_ok=True)
            os.chdir(working_dir)

        extra_args = {
            "rotation": 0
        }

        if config.rotate is not None:
            extra_args["rotation"] = config.rotate

        ffmpeg_presets[config.ffmpeg_preset](config, input_file, output_file, extra_args)

    except Exception as ex:
        error = traceback.format_exc()
        printlog(config, fg("red") + "ERROR: {}".format(error) + attr("reset"))
        printlog(config, "Done.\n")
        return "ERROR"
    finally:
        os.chdir(current_dir)

    try:
        printlog(config, "Copying attributes...")
        create_time = creation_date(input_file)
        mod_time = path.getmtime(input_file)
        if not config.dry_run:
            os.utime(output_file, (create_time, mod_time))
    except:
        printlog(config, fg("red") + "COULD NOT copy attributes" + attr("reset"))

    try:
        printlog(config, "Checking size...")

        input_size = path.getsize(input_file)
        if not config.dry_run:
            output_size = path.getsize(output_file)

            if config.check_output_size and float(output_size) > float(input_size) * 0.75:
                printlog(config, fg("yellow") + "Output file size is not smaller than input file size" + attr("reset"))

                printlog(config, "Copying original video...")
                copy_video(input_file, output_file)

                printlog(config, "Done.\n")
                return "OK SIZE"
    except:
        printlog(config, fg("red") + "COULD NOT check size" + attr("reset"))

    printlog(config, "Done.\n")
    return "OK"

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
            file_name = filename_presets[config.filename_preset](config.prefix + file_name + config.postfix)
            output_file = path.join(processed_root_path, current_dir, file_name) + output_extension

            if not file_extension.lower() in video_extensions or file_name.startswith(config.processed_dir):
                continue

            if in_db_file(config, input_file):
                printlog(config, f"File '{input_file}' already processed, skipping.\n")
                continue

            try:
                state = process_video_file(input_file, output_file)
                add_to_db_file(config, input_file, state)
            except Exception as ex:
                error = traceback.format_exc()
                printlog(config,
                    fg("red") + f"Error encountered processing '{input_file}', skipping." + attr("reset") + "\n    ERROR: " + error + "\n"
                )
                add_to_db_file(config, input_file, "ERROR")


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
        "-l", "--filename-preset",
        default="default",
        choices=filename_presets.keys(),
        help="Preset to change file names."
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
    parser.add_argument(
        "--rotate",
        default=None,
        type=int,
        choices=[0, 90, 180, 270],
        help="Rotates a video of the given degrees"
    )
    config = parser.parse_args()

    printlog(config, f"WORKING UNDER: {config.input_dir}\n")

    if config.reset_logfile:
        reset_db_file(config)

    scan_and_process_videos()
    clean_ffmpeg(config)
    add_to_db_file(config, "- " * 40)

# Constants
video_extensions = [ ".mp4", ".avi", ".mov", ".mkv" ]
output_extension = ".mp4"

if __name__ == "__main__":
    main()
