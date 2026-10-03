"""Deterministic threshold-zone rerun and badge decision helpers."""
import math

def mcse(probability,draws):return math.sqrt(probability*(1-probability)/draws)

def resolve_threshold(run,draws,max_draws=12000,band=2.0):
    result=run(draws)
    probabilities=result[3]
    highest=float(max(probabilities,default=0))
    if abs(highest-0.5)<band*mcse(highest,draws):
        draws=max_draws
        result=run(draws)  # run initializes default_rng with the same seed
    return result,draws

def badge_passes(probability,error,eligible=True):
    return bool(eligible and probability>=0.5 and abs(probability-0.5)>=2*error)
