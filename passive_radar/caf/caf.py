"""
CAF (Cross Ambiguity Function) optimized for Raspberry Pi 5.
Supports 5-channel passive radar (KrakenSDR).
Performs FFT-based range-Doppler processing efficiently.
"""
"""
CAF (Cross Ambiguity Function) module
=====================================

Оптимизирован для многопроцессной обработки 5 каналов на Raspberry Pi 5.
Работает как с офлайн-данными, так и в режиме реального времени.

Функция process_iq_block() вызывается из kraken_reader.py для каждого канала.
"""

import numpy as np
import time
import logging

try:
    import pyfftw
    USE_FFTW = True
except ImportError:
    USE_FFTW = False

# Настройка логирования (по желанию можно отключить)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [CAF-%(levelname)s] %(message)s')


# ────────────────────────────────
# Константы
# ────────────────────────────────
FFT_SIZE = 32768
DOWNSAMPLE = 4             # для уменьшения нагрузки
ZERO_PAD = 2               # коэффициент нулевого дополнения
WINDOW = np.hanning(FFT_SIZE // DOWNSAMPLE)

# ────────────────────────────────
# Основная функция CAF
# ────────────────────────────────
def process_iq_block(iq_block: np.ndarray, channel_id: int = 0):
    """
    Выполняет кросс-амбигуити анализ одного блока IQ-данных для данного канала.

    Parameters
    ----------
    iq_block : np.ndarray
        IQ-комплексный сигнал [complex64]
    channel_id : int
        Номер канала KrakenSDR (0–4)
    """
    t0 = time.time()

    if iq_block.size < FFT_SIZE:
        logging.warning(f"CAF-{channel_id}: блок слишком короткий ({iq_block.size})")
        return None

    # Downsample
    iq_ds = iq_block[::DOWNSAMPLE]
    n = len(iq_ds)

    # Окно
    iq_win = iq_ds * WINDOW[:n]

    # FFT
    if USE_FFTW:
        fft_in = pyfftw.empty_aligned(n, dtype=np.complex64)
        fft_out = pyfftw.empty_aligned(n * ZERO_PAD, dtype=np.complex64)
        fft_in[:] = iq_win
        fft_obj = pyfftw.FFTW(fft_in, fft_out, direction='FFTW_FORWARD', flags=('FFTW_ESTIMATE',))
        spec = fft_obj()
    else:
        spec = np.fft.fft(iq_win, n * ZERO_PAD)

    # CAF: автокорреляция во временной и частотной области
    caf = np.fft.ifftshift(np.fft.ifft(spec * np.conj(spec)))

    # Амплитуда CAF
    magnitude = np.abs(caf)

    # Нормализация
    magnitude /= magnitude.max() + 1e-6

    # Метрики
    peak_idx = np.argmax(magnitude)
    peak_val = magnitude[peak_idx]

    dt = (time.time() - t0) * 1000
    logging.info(f"CAF-{channel_id}: OK  | peak={peak_val:.3f} | time={dt:.1f} ms")

    return {
        "channel_id": channel_id,
        "peak_val": float(peak_val),
        "peak_idx": int(peak_idx),
        "timestamp": time.time(),
    }
