#!/usr/bin/env python3

from os import path

def get_db_file(config):
    """
    Gets the name of DB file
    """
    return path.join(config.input_dir, "resize_all.db")

def add_to_db_file(config, file_name, state = ""):
    """
    Adds an entry into the DB file
    """
    if config.dry_run:
        return

    db_file = get_db_file(config)
    with open(db_file, "a") as file:
        log_line = (file_name + " " + state).strip()
        file.write(log_line + "\n")

def in_db_file(config, file_name):
    """
    Checks if an entry is in the DB file
    """
    db_file = get_db_file(config)

    if not path.isfile(db_file):
        return False

    file_name = file_name.strip().lower()

    with open(db_file, "r") as file:
        for line in file:
            line = line.strip().lower()

            if line.startswith(file_name + " ok"):
                return True

        return False

def reset_db_file(config):
    """
    Resets the DB file
    """
    if config.dry_run:
        return

    db_file = get_db_file(config)
    with open(db_file, "w") as file:
        file.write("")
