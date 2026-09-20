#!/bin/sh
set -eu

interval=${AIPEDIA_BACKUP_INTERVAL_SECONDS:-86400}
while :; do
  /srv/aipedia/bin/backup-aipedia
  sleep "$interval"
done
