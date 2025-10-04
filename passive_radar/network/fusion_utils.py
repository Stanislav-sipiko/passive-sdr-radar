"""
Utilities for multilateration and fusion.
"""

import numpy as np


def fuse_tracks_lsq(reports):
    """Fuse tracks from multiple units using weighted least squares by SNR."""
    if not reports:
        return []

    positions = []
    weights = []

    for r in reports:
        for t in r.get("tracks", []):
            positions.append(np.array(t["position"]))
            weights.append(t.get("snr", 1.0))

    if len(positions) < 2:
        return reports

    positions = np.array(positions)
    weights = np.array(weights)
    w = weights / weights.sum()
    fused_position = np.sum(positions * w[:, None], axis=0)

    return [{
        "id": "fused_1",
        "position": fused_position.tolist(),
        "confidence": float(weights.mean())
    }]
