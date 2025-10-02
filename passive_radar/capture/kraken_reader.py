def load_iq(path):
    """Загрузка IQ данных (заглушка)"""
    print(f"[kraken_reader] Loading IQ from {path}")
    return [0.0] * 100

def chunk_iq(iq, chunk_size=1024):
    return [iq[i:i+chunk_size] for i in range(0, len(iq), chunk_size)]

def calibrate(iq):
    return iq
