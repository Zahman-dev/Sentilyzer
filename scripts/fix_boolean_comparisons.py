#!/usr/bin/env python3
"""Script to fix boolean comparison issues in Python files."""

import os
import re
from typing import List, Tuple


def find_python_files(directory: str) -> List[str]:
    """Find all Python files in the given directory and its subdirectories."""
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def fix_boolean_comparisons(file_path: str) -> Tuple[bool, List[str]]:
    """Fix boolean comparison issues in a Python file.

    Returns:
        Tuple[bool, List[str]]: (whether file was modified, list of fixed lines)
    """
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    modified = False
    fixed_lines = []

    for line in lines:
        # Fix comparison to True
        line = re.sub(
            r"([^a-zA-Z0-9_])(==\s*True|True\s*==)([^a-zA-Z0-9_])", r"\1is True\3", line
        )
        line = re.sub(
            r"([^a-zA-Z0-9_])(!=\s*True|True\s*!=)([^a-zA-Z0-9_])",
            r"\1is not True\3",
            line,
        )

        # Fix comparison to False
        line = re.sub(
            r"([^a-zA-Z0-9_])(==\s*False|False\s*==)([^a-zA-Z0-9_])",
            r"\1is False\3",
            line,
        )
        line = re.sub(
            r"([^a-zA-Z0-9_])(!=\s*False|False\s*!=)([^a-zA-Z0-9_])",
            r"\1is not False\3",
            line,
        )

        # Fix SQLAlchemy boolean comparisons
        line = re.sub(
            r"([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\s*==\s*True", r"\1.is_(True)", line
        )
        line = re.sub(
            r"([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\s*==\s*False", r"\1.is_(False)", line
        )
        line = re.sub(
            r"([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\s*!=\s*True", r"\1.is_not(True)", line
        )
        line = re.sub(
            r"([a-zA-Z0-9_]+\.[a-zA-Z0-9_]+)\s*!=\s*False", r"\1.is_not(False)", line
        )

        if line != lines[len(fixed_lines)]:
            modified = True

        fixed_lines.append(line)

    if modified:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(fixed_lines)

    return modified, fixed_lines


def main():
    """Main function."""
    # Get the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Find all Python files
    python_files = find_python_files(project_root)

    # Fix boolean comparisons in each file
    for file_path in python_files:
        try:
            modified, _ = fix_boolean_comparisons(file_path)
            if modified:
                print(f"Fixed boolean comparisons in {file_path}")
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")


if __name__ == "__main__":
    main()
