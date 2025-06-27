#!/usr/bin/env python3
"""Script to fix line length issues in Python files."""

import os
import sys
from typing import List, Tuple


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in the given directory and its subdirectories."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def fix_line_length(file_path: str, max_length: int = 90) -> Tuple[bool, List[str]]:
    """Fix lines that exceed the maximum length in a Python file.

    Returns:
        Tuple[bool, List[str]]: (whether file was modified, list of fixed lines)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    fixed_lines = []
    for line in lines:
        # Skip lines that are within the limit
        if len(line.rstrip()) <= max_length:
            fixed_lines.append(line)
            continue

        # Don't break long string literals or URLs
        stripped = line.strip()
        if (
            (stripped.startswith('"') and stripped.endswith('"'))
            or (stripped.startswith("'") and stripped.endswith("'"))
            or "http://" in line
            or "https://" in line
        ):
            fixed_lines.append(line)
            continue

        # Try to break the line at a sensible point
        words = line.split()
        current_line = words[0]
        for word in words[1:]:
            if len(current_line + " " + word) <= max_length:
                current_line += " " + word
            else:
                fixed_lines.append(current_line + "\n")
                current_line = "    " + word  # Add indentation for continuation
                modified = True
        fixed_lines.append(current_line + "\n")

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

    return modified, fixed_lines


def main():
    """Main function to fix line length issues in Python files."""
    if len(sys.argv) < 2:
        print("Usage: fix_line_length.py <directory>")
        sys.exit(1)

    directory = sys.argv[1]
    max_length = int(sys.argv[2]) if len(sys.argv) > 2 else 90

    python_files = find_python_files(directory)
    modified_files = []

    for file_path in python_files:
        modified, _ = fix_line_length(file_path, max_length)
        if modified:
            modified_files.append(file_path)
            print(f"Fixed line length issues in {file_path}")

    if modified_files:
        print(f"\nModified {len(modified_files)} files:")
        for file in modified_files:
            print(f"  - {file}")
    else:
        print("\nNo files needed modification.")


if __name__ == "__main__":
    main()
