#!/bin/bash
set -e

# shellcheck disable=SC1091
. configuration.env

export READER_PLUGIN=readers.probes.http

exec python -um uptimer
