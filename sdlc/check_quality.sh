#!/bin/bash

# Run isort on the aws and twitchrce directories
echo "Running isort..."
# shellcheck disable=SC2035
poetry run isort **/*.py --color

# Run black on the aws and twitchrce directories
echo "Running black..."
poetry run black "aws" "tests" "twitchrce"