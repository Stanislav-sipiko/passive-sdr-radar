# preprocess/filters.py
"""
Filtering and preprocessing utilities for passive radar.
Includes MTI filtering, FIR high-pass filtering, and normalization.
MTI (Moving Target Indicator) – вычитание последовательных кадров.
FIR highpass – проектирование фильтра через scipy.signal.firwin.
normalize – нормализация амплитуды данных.
Универсально: поддержка работы и с 1D массивами, и с 2D (например, спектрограммы).
рабочие фильтры:
mti_filter → подавляет стационарные цели.
fir_highpass → убирает низкочастотный шум/дрифт.
normalize → нормализация мощности.
"""

import numpy as np
from scipy.signal import lfilter, firwin


def mti_filter(data: np.ndarray, delay: int = 1) -> np.ndarray:
    """
    Apply a simple MTI (Moving Target Indicator) filter.
    Subtracts a delayed version of the signal to suppress stationary clutter.

    Parameters
    ----------
    data : np.ndarray
        Input IQ or magnitude data (1D or 2D).
    delay : int
        Number of samples/rows to delay.

    Returns
    -------
    np.ndarray
        MTI-filtered data.
    """
    if data.ndim == 1:
        out = np.zeros_like(data)
        out[delay:] = data[delay:] - data[:-delay]
    else:  # e.g. 2D: (time, freq)
        out = np.zeros_like(data)
        out[delay:, :] = data[delay:, :] - data[:-delay, :]
    return out


def fir_highpass(data: np.ndarray, cutoff: float, fs: float, order: int = 101) -> np.ndarray:
    """
    Apply a FIR high-pass filter to suppress low-frequency clutter.

    Parameters
    ----------
    data : np.ndarray
        Input data (1D or 2D).
    cutoff : float
        Cutoff frequency in Hz.
    fs : float
        Sampling frequency in Hz.
    order : int
        Number of filter taps.

    Returns
    -------
    np.ndarray
        Filtered data.
    """
    # Design filter
    taps = firwin(order, cutoff / (fs / 2), pass_zero=False)
    
    if data.ndim == 1:
        return lfilter(taps, 1.0, data)
    else:  # Apply filter along first axis (time)
        filtered = np.zeros_like(data)
        for i in range(data.shape[1]):
            filtered[:, i] = lfilter(taps, 1.0, data[:, i])
        return filtered


def normalize(data: np.ndarray, eps: float = 1e-9) -> np.ndarray:
    """
    Normalize data to unit power.

    Parameters
    ----------
    data : np.ndarray
        Input signal.
    eps : float
        Small constant to avoid division by zero.

    Returns
    -------
    np.ndarray
        Normalized signal.
    """
    power = np.sqrt(np.mean(np.abs(data) ** 2) + eps)
    return data / power


if __name__ == "__main__":
    # Quick self-test
    t = np.linspace(0, 1, 1000, endpoint=False)
    x = np.sin(2 * np.pi * 5 * t) + 0.5 * np.sin(2 * np.pi * 50 * t)

    print("Running MTI...")
    x_mti = mti_filter(x)

    print("Running highpass...")
    x_hp = fir_highpass(x, cutoff=20, fs=1000)

    print("Running normalize...")
    x_norm = normalize(x_hp)

    print("Done. Shapes:", x.shape, x_mti.shape, x_hp.shape, x_norm.shape)
