#!/bin/sh
# Periodic IndexNow dispatch for AIpedia (supervisord program aipedia-indexnow).
# Sends only pending/retry outbox events that are due; never queues --all.
# flock -n: a run is skipped while another dispatch (scheduled or manual) holds
# the lock, so runs never overlap. The key is read by Django from the program
# environment and is never printed. Manual runs must use the same lock:
#   flock -n /srv/aipedia/data/indexnow-dispatch.lock <python> manage.py indexnow_dispatch --send
set -u

interval=${AIPEDIA_INDEXNOW_INTERVAL_SECONDS:-300}
lock=/srv/aipedia/data/indexnow-dispatch.lock
while :; do
  if flock -n "$lock" /srv/aipedia/venv/bin/python /srv/aipedia/app/manage.py indexnow_dispatch --send --batch 1000; then
    :
  else
    echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) dispatch skipped or failed (exit $?)"
  fi
  sleep "$interval"
done
