#!/usr/bin/env python3

from os import path
import os
import sys

def printlog(config, text):
    """
    Prints a text removing all occurrences of the input_path
    """
    terminated_input_dir = config.input_dir + os.sep
    input_path_cleaned = text.replace(terminated_input_dir, "")
    print(input_path_cleaned, file=sys.stdout)
    sys.stdout.flush()

    colour_cleaned = text.replace("", "")
    file = get_log_file(config)
    print(colour_cleaned, file=file)
    file.flush()

def get_log_file(config):
    """
    Gets the name of log file
    """
    global log_file

    if log_file is None:
        log_file_path = path.join(config.input_dir, "resize_all.log")
        log_file = open(log_file_path, "a")
        print("_ " * 40, file = log_file)

    return log_file

def to_windows_path(p):
    if sys.platform.startswith("cygwin") or sys.platform.startswith("msys"):
        # Convert /cygdrive/c/... to C:\...
        drive = p[10].upper()  # after /cygdrive/
        rest = p[11:].replace("/", "\\")
        return f"{drive}:{rest}"
    else:
        return os.path.abspath(p)

log_file = None
