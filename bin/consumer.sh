#!/bin/bash
set -e

# shellcheck disable=SC1091
. configuration.env

export READER_PLUGIN=readers.kafka
export WRITER_PLUGIN=writers.postgres

exec python -um uptimer
