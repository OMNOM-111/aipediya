#!/bin/sh
set -eu

umask 077
IFS= read -r token
case "$token" in
  eyJ*) ;;
  *) exit 40 ;;
esac

install -d -o aipedia -g aipedia -m 700 /srv/aipedia/private
printf '%s' "$token" > /srv/aipedia/private/aipediya-production.token
chown aipedia:aipedia /srv/aipedia/private/aipediya-production.token
chmod 600 /srv/aipedia/private/aipediya-production.token
test -s /srv/aipedia/private/aipediya-production.token
