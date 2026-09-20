#!/bin/sh
set -eu

: "${TUNNEL_TOKEN_FILE:=/srv/aipedia/private/aipediya-production.token}"
exec /usr/local/bin/cloudflared tunnel --no-autoupdate run --token-file "$TUNNEL_TOKEN_FILE"
