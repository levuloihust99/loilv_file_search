import os
import json
import copy
import logging
import argparse

from typing import Text, Optional, List, Union

from .utils import (
    check_for_ignore,
    search_pattern_in_file,
    format_print_path,
    MatchingMode,
)

logger = logging.getLogger(__name__)


def scan_files(
    root_path: Text,
    search_pattern: Union[Text, List[Text]],
    ignore_pattern: Optional[Union[Text, List[Text]]] = None,
    include_pattern: Optional[Union[Text, List[Text]]] = None,
    ignore_file_pattern: Optional[Union[Text, List[Text]]] = None,
    include_file_pattern: Optional[Union[Text, List[Text]]] = None,
    matching_mode: MatchingMode = MatchingMode.INCLUDE_OVERRIDES_IGNORE,
) -> List[Text]:
    logger.info("Scanning...")
    root_path_dir = os.path.basename(root_path)
    is_ignore = check_for_ignore(
        root_path_dir, ignore_pattern, include_pattern, matching_mode
    )
    if is_ignore:
        return
    stack = [root_path]
    queue = []
    max_line_len = 125
    printing_prefix = "\r" + " " * max_line_len + "\r"
    while stack:
        path = stack.pop()
        print(printing_prefix + format_print_path(path, max_line_len), end="")

        if os.path.isdir(path):
            subpaths = os.listdir(path)
            for f in subpaths:
                resolved_include_pattern = include_pattern
                resolved_ignore_pattern = ignore_pattern

                f_path = os.path.join(path, f)
                if os.path.isfile(f_path):
                    resolved_include_pattern = include_file_pattern or include_pattern
                    resolved_ignore_pattern = ignore_file_pattern or ignore_pattern

                is_ignore = check_for_ignore(
                    f,
                    ignore_pattern=resolved_ignore_pattern,
                    include_pattern=resolved_include_pattern,
                    matching_mode=matching_mode,
                )
                if is_ignore is True:
                    continue
                stack.append(os.path.join(path, f))
        else:
            is_matching = True
            if search_pattern:
                is_matching = search_pattern_in_file(path, search_pattern)

            if is_matching is True:
                queue.append(path)

    print(printing_prefix)
    logger.info("Done scanning files")
    logger.info("Search results")
    print("-" * max_line_len)
    for idx, f in enumerate(queue):
        print("#{} - {}".format(idx, f))

    return queue


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", "-i", default=os.getcwd())
    parser.add_argument(
        "--ignore_pattern",
        "-g",
        nargs="+",
        default=None,
        help=(
            "Ignore patterns for any folders/files during traversing. "
            "If a folder matches this pattern, all its subdirectories/files are ignored immediately (no further search)."
        ),
    )
    parser.add_argument(
        "--include_pattern",
        "-c",
        nargs="+",
        default=None,
        help=(
            "Include patterns for any folders/files during traversing. "
            "If a folder matches this pattern, the search will go deeper into its files/subdirectories."
        ),
    )
    parser.add_argument(
        "--include_file_pattern",
        nargs="+",
        default=None,
        help="Include pattern for files only. Does not apply to directories.",
    )
    parser.add_argument(
        "--ignore_file_pattern",
        nargs="+",
        default=None,
        help="Ignore pattern for files only. Does not apply to directories.",
    )
    parser.add_argument(
        "--search_pattern",
        "-s",
        nargs="+",
        default=None,
        help="Search for patterns in file content. Only apply for text files. Binary files are skipped.",
    )
    parser.add_argument(
        "--matching_mode",
        choices=[
            MatchingMode.INCLUDE_OVERRIDES_IGNORE,
            MatchingMode.IGNORE_OVERRIDES_INCLUDE,
            MatchingMode.INCLUDE_AND_IGNORE_BOTH_SATISFIED,
        ],
        default="include_overrides_ignore",
        help="Specify how to check if a file is matched when both include and ignore patterns are present.",
    )
    parser.add_argument("--pattern_file", "-p", default=None)
    args = parser.parse_args()

    params = {}
    if args.pattern_file:
        with open(args.pattern_file, "r") as reader:
            pattern_rule = json.load(reader)
        params["search_pattern"] = pattern_rule.get("search_pattern")
        params["ignore_pattern"] = pattern_rule.get("ignore_pattern")
        params["include_pattern"] = pattern_rule.get("include_pattern")
        params["ignore_file_pattern"] = pattern_rule.get("ignore_file_pattern")
        params["include_file_pattern"] = pattern_rule.get("include_file_pattern")

    args_json = copy.deepcopy(args.__dict__)
    for k, v in args_json.items():
        if k in {
            "search_pattern",
            "ignore_pattern",
            "include_pattern",
            "ignore_file_pattern",
            "include_file_pattern",
        }:
            params[k] = v

    scan_files(
        root_path=args.input_path,
        search_pattern=params["search_pattern"],
        ignore_pattern=params["ignore_pattern"],
        include_pattern=params["include_pattern"],
        ignore_file_pattern=params["ignore_file_pattern"],
        include_file_pattern=params["include_file_pattern"],
        matching_mode=args.matching_mode,
    )


if __name__ == "__main__":
    main()
