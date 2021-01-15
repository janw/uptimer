#!/bin/sh
# Entrypoint
#
# Runs pre-flight logic before launching into uptimer
#
set -e

# When the instance is launched as a postgres writer, it is assumed to have
# permissions to update the schema. Thus run migrations before launch.
case "$WRITER_PLUGIN" in
    *postgres*)
        dbmate --wait --no-dump-schema up
esac


exec python -m uptimer
