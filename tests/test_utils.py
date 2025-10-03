import numpy as np
from passive_radar.tools import utils

def test_db_and_normalize():
    arr = np.array([1.0, 10.0, 100.0])
    db_vals = utils.db(arr)
    assert db_vals.shape == arr.shape

    norm = utils.normalize(arr)
    assert np.all(norm >= 0) and np.all(norm <= 1)
