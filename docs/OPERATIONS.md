# AIpedia Operations

## Cold start

The AIpedia process group is isolated in `/srv/aipedia/supervisord.conf`; it must not be added to the StratForge Supervisor configuration. The container owner must configure its runtime entrypoint to run exactly:

```sh
/srv/aipedia/bin/aipedia-supervisor-entrypoint
```

The entrypoint sources the protected AIpedia environment, refuses to launch a duplicate Supervisor, and runs the dedicated Supervisor in the foreground. It starts the application, Cloudflare Tunnel, and backup loop. This is an administrator change outside the SSH container; it has not been applied or reboot-tested by AIpedia.

## Backups

`backup-aipedia` uses SQLite's backup API, checks `PRAGMA integrity_check`, then atomically publishes a snapshot in `/srv/aipedia/backups`. The dedicated Supervisor runs it once per 24 hours and retains only `aipedia-scheduled-*.sqlite3` snapshots older than 14 days.

Those snapshots remain on the server volume. Configure an encrypted off-host destination and a tested restore procedure before treating this as disaster recovery.
