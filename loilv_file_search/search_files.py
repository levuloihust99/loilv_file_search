import os
import json
import logging
import argparse
from typing import Text, Optional, List, Union

from .utils import check_for_ignore, search_pattern_in_file, format_print_path

logger = logging.getLogger(__name__)


def scan_files(
    root_path: Text,
    search_pattern: Union[Text, List[Text]],
    ignore_pattern: Optional[Union[Text, List[Text]]] = None,
    include_pattern: Optional[Union[Text, List[Text]]] = None,
    include_over_ignore: bool = True,
):
    logger.info("Scanning...")
    root_path_dir = os.path.basename(root_path)
    is_ignore = check_for_ignore(
        root_path_dir, ignore_pattern, include_pattern, include_over_ignore
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
                is_ignore = check_for_ignore(
                    f, ignore_pattern, include_pattern, include_over_ignore
                )
                if is_ignore is True:
                    continue
                stack.append(os.path.join(path, f))
        else:
            found = search_pattern_in_file(path, search_pattern)
            if found is True:
                queue.append(path)

    print(printing_prefix)
    logger.info("Done scanning files")
    logger.info("Search results")
    print("-" * max_line_len)
    for idx, f in enumerate(queue):
        print("#{} - {}".format(idx, f))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", "-i", default=os.getcwd())
    parser.add_argument("--ignore_pattern", "-g", nargs="+", default=None)
    parser.add_argument("--include_pattern", "-c", nargs="+", default=None)
    parser.add_argument("--search_pattern", "-s", nargs="+", default=None)
    parser.add_argument("--include_over_ignore", "-y", default=True, type=eval)
    parser.add_argument("--pattern_file", "-p", default=None)
    args = parser.parse_args()

    if args.search_pattern is None:
        logger.warning("You didn't pass the 'search_pattern' param. This is noop.")
    if args.pattern_file:
        with open(args.pattern_file, "r") as reader:
            pattern_rule = json.load(reader)
        search_pattern = pattern_rule.get("search_pattern", None)
        if search_pattern:
            args.search_pattern = search_pattern
        ignore_pattern = pattern_rule.get("ignore_pattern", None)
        if ignore_pattern:
            args.ignore_pattern = ignore_pattern
        include_pattern = pattern_rule.get("include_pattern", None)
        if include_pattern:
            args.include_pattern = include_pattern

    scan_files(
        root_path=args.input_path,
        search_pattern=args.search_pattern,
        ignore_pattern=args.ignore_pattern,
        include_pattern=args.include_pattern,
        include_over_ignore=args.include_over_ignore,
    )


if __name__ == "__main__":
    main()
