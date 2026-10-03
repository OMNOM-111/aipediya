"""Snapshot-relative fact validity; stale values carry no numeric penalty."""
import datetime

def fact_state(checked,cutoff,thresholds,invalidated=False):
    if invalidated:return 'unconfirmed'
    if not checked or str(checked) in ('NaT','nan','None'):return 'unknown'
    day=datetime.date.fromisoformat(str(checked)[:10])
    cut=datetime.date.fromisoformat(str(cutoff)[:10])
    days=(cut-day).days
    return 'fresh' if days<=thresholds['fresh'] else ('stale' if days<=thresholds['stale'] else 'expired')

def valid(checked,cutoff,thresholds):
    return fact_state(checked,cutoff,thresholds) in ('fresh','stale')

def permission_valid(extra,cutoff):
    if extra.get('invalidated') or extra.get('permission_revoked') or extra.get('licence_revoked'):
        return False
    expires=extra.get('permission_expires') or extra.get('permission_expiry_date')
    return not expires or str(expires)[:10]>=str(cutoff)[:10]
