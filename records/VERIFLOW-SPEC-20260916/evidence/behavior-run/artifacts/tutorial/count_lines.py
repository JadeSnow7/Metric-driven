#!/usr/bin/env python3
"""Count the number of UTF-8 lines in a text file."""

import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("用法：python3 count_lines.py <文本文件>", file=sys.stderr)
        return 2

    path = sys.argv[1]
    try:
        with open(path, "r", encoding="utf-8") as source:
            line_count = sum(1 for _ in source)
    except FileNotFoundError:
        print(f"错误：找不到文件：{path}", file=sys.stderr)
        return 1
    except IsADirectoryError:
        print(f"错误：这不是普通文件：{path}", file=sys.stderr)
        return 1
    except UnicodeDecodeError:
        print(f"错误：文件不是有效的 UTF-8 文本：{path}", file=sys.stderr)
        return 1
    except OSError as error:
        print(f"错误：无法读取文件 {path}：{error}", file=sys.stderr)
        return 1

    print(line_count)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
