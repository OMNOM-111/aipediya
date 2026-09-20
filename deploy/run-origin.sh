#!/bin/sh
set -eu
set -a
. /srv/aipedia/config/aipedia.env
set +a
cd /srv/aipedia/current
exec /srv/aipedia/current/.venv/bin/python tools/serve.py --port 18810
