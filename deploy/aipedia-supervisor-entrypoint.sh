#!/bin/sh
set -eu

config=/srv/aipedia/supervisord.conf
pidfile=/srv/aipedia/aipedia-supervisord.pid

if [ -s "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
  echo "AIpedia Supervisor is already running" >&2
  exit 0
fi

set -a
. /etc/aipedia/aipedia.env
set +a
exec /usr/bin/supervisord -n -c "$config"
