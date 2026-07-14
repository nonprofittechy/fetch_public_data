#!/bin/sh
set -eu

# A newly attached Fly volume is root-owned. Make the database directory
# writable, then drop privileges before starting the web process.
mkdir -p /data
chown -R 1000:1000 /data
exec gosu 1000:1000 "$@"
