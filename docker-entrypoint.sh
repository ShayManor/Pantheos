#!/bin/sh
# Prepare the DB (create tables + seed if empty), then run the given command.
set -e
python docker_bootstrap.py
exec "$@"
