#!/bin/sh
# Dependencies post script
#
# The script is used to clean up after installing dependencies in the container image
#
set -e
echo "Running post-script"

# Remove build dependencies
apt purge --yes build-essential

# Clean up
apt clean
