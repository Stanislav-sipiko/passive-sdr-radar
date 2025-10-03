import numpy as np
from passive_radar.preprocess import filters

def test_normalize():
    arr = np.array([1, 2, 3], dtype=float)
    out = filters.normalize(arr)
    assert np.isclose(np.linalg.norm(out), 1.0)
