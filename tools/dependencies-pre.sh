#!/bin/sh
# Dependencies pre script
#
# The script is used to install necessary system-level dependencies before attempting
# to install python packages, such as postgres client library and build tools.
#
set -e
echo "Running pre-script"

# Runtime
apt update --yes
apt install --no-install-recommends --yes \
    build-essential libpq-dev postgresql-client tini
