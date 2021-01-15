#!/bin/bash
set -e

# shellcheck disable=SC1091
. configuration.env

export READER_PLUGIN=readers.probes.http
export WRITER_PLUGIN=writers.kafka

exec python -um uptimer
