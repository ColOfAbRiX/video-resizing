#!/usr/bin/env python3

import re

def no_change(text):
    return text

def lower_snake_case(text):
    return '_'.join(
        re.sub(
            '([A-Z][a-z]+)', r' \1',
            re.sub(
                '([A-Z]+)', r' \1',
                text.replace('-', ' ')
            )
        ).split()
    ).lower()

filename_presets = {
    "default": no_change,
    "lower_snake_case": lower_snake_case,
}
