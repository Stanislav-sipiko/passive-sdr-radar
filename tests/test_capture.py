import numpy as np
from passive_radar.capture import kraken_reader

def test_chunk_iq():
    # Заглушка IQ массива
    iq = np.arange(100) + 1j * np.arange(100)
    chunks = list(kraken_reader.chunk_iq(iq, chunk_size=10))
    assert len(chunks) == 10
    assert all(isinstance(c, np.ndarray) for c in chunks)
