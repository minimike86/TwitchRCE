#!/bin/bash

# Directories to include in coverage
DIRECTORIES="aws tests twitchrce"

# Run coverage for the specified directories
echo "Running coverage for directories: $DIRECTORIES"

poetry run coverage run --source="$DIRECTORIES" -m pytest
poetry run coverage report
