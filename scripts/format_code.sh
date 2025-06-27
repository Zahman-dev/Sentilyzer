#!/bin/bash

# Exit on error
set -e

# Get the project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Formatting Python code..."

# Run isort to sort imports
echo "Running isort..."
isort "$PROJECT_ROOT"

# Run our custom line length fixer
echo "Running line length fixer..."
python3 "$PROJECT_ROOT/scripts/fix_line_length.py" "$PROJECT_ROOT"

echo "Code formatting complete!"
