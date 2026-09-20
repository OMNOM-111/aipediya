# Search Discovery And Monetization Readiness

## Owner actions

1. Add `https://aipediya.com` as a URL-prefix property in Google Search Console, Bing Webmaster Tools, and Yandex Webmaster.
2. In each account, choose HTML meta-tag verification and copy only its token value into the matching protected environment variable: `GOOGLE_SITE_VERIFICATION`, `BING_SITE_VERIFICATION`, or `YANDEX_SITE_VERIFICATION`.
3. Restart only the dedicated AIpedia supervisor, verify the meta tag in server HTML, then complete verification in the owner account. Submit `https://aipediya.com/sitemap.xml` in each console.
4. Do not add advertising credentials until the advertising system has approved the site and the privacy contact is set.

## IndexNow

Generate a random IndexNow key, put it in `AIPEDIA_INDEXNOW_KEY`, and restart the dedicated AIpedia supervisor. The application serves the required key file at `/indexnow/<key>.txt`.

IndexNow sends nothing automatically. After a significant, reviewed publication change, submit only the changed card URLs:

```sh
sudo -n sh -c 'set -a; . /etc/aipedia/aipedia.env; set +a; /srv/aipedia/venv/bin/python /srv/aipedia/app/manage.py notify_indexnow --url https://aipediya.com/models/example?lang=ru --url https://aipediya.com/models/example?lang=en'
```

Use `--all` only after a genuine catalog-wide change.

## Advertising

Advertising remains off unless all of these are nonempty: `AIPEDIA_ADS_ENABLED=1`, `AIPEDIA_ADS_CLIENT`, and `AIPEDIA_ADS_SLOT`. `AIPEDIA_ADS_TXT` should contain only the approved vendor declaration. One labelled placement is then rendered in normal document flow; the provider script loads only after visitor consent.
