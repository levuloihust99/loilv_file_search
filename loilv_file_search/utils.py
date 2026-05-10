import re

from enum import Enum
from typing import Text, Optional, List, Union

# https://stackoverflow.com/questions/898669/how-can-i-detect-if-a-file-is-binary-non-text-in-python
textchars = bytearray({7, 8, 9, 10, 12, 13, 27} | set(range(0x20, 0x100)) - {0x7F})
is_binary_string = lambda bytes: bool(bytes.translate(None, textchars))


class MatchingMode(str, Enum):
    INCLUDE_OVERRIDES_IGNORE = "include_overrides_ignore"
    IGNORE_OVERRIDES_INCLUDE = "ignore_overrides_include"
    INCLUDE_AND_IGNORE_BOTH_SATISFIED = "include_and_ignore_both_satisfied"


def pattern_matching(
    pattern: Optional[Union[Text, List[Text]]], text: Text, default: bool = True
):
    if pattern is None:
        return bool(default)
    if not isinstance(pattern, list):
        pattern = [pattern]
    for patt in pattern:
        match = re.search(patt, text)
        if match is not None:
            return True
    return False


def search_pattern_in_file(file_path: Text, pattern: Union[Text, List[Text]]):
    with open(file_path, "rb") as reader:
        file_opening = reader.read(1024)
    is_binary = is_binary_string(file_opening)
    if is_binary is True:
        return False
    try:
        with open(file_path, "r") as reader:
            content = reader.read()
    except:
        return False
    found = pattern_matching(pattern, content)
    return found


def check_for_ignore(
    path_dir: Text,
    ignore_pattern: Optional[Union[Text, List[Text]]] = None,
    include_pattern: Optional[Union[Text, List[Text]]] = None,
    matching_mode: MatchingMode = MatchingMode.INCLUDE_OVERRIDES_IGNORE,
) -> bool:
    if ignore_pattern is None and include_pattern is None:
        return False

    if ignore_pattern is None:
        return not pattern_matching(include_pattern, path_dir, default=False)

    if include_pattern is None:
        return pattern_matching(ignore_pattern, path_dir, default=False)

    # both `include_pattern` and `ignore_pattern` is not None
    is_ignore = False
    if matching_mode == MatchingMode.INCLUDE_OVERRIDES_IGNORE:
        should_ignore = pattern_matching(ignore_pattern, path_dir, default=False)
        if should_ignore is True:
            is_ignore = True
            should_include = pattern_matching(include_pattern, path_dir, default=False)
            if should_include is True:
                is_ignore = False
    elif matching_mode == MatchingMode.IGNORE_OVERRIDES_INCLUDE:
        should_include = pattern_matching(include_pattern, path_dir, default=False)
        if should_include is True:
            should_ignore = pattern_matching(ignore_pattern, path_dir, default=False)
            if should_ignore is True:
                is_ignore = True
        else:
            is_ignore = True
    else:
        # both include and ignore patterns need to be satisfied
        should_ignore = pattern_matching(ignore_pattern, path_dir, default=False)
        should_include = pattern_matching(include_pattern, path_dir, default=False)
        is_ignore = (not should_include) or should_ignore

    return is_ignore


def format_print_path(path: Text, max_line_len: int = -1):
    ellipsis = "..."
    if max_line_len <= len(ellipsis):
        return path
    if len(path) <= max_line_len:
        return path
    allowed_len = max_line_len - len(ellipsis)
    formatted_print_path = ellipsis + path[-allowed_len:]
    return formatted_print_path
