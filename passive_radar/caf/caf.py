"""
CAF (Cross Ambiguity Function) optimized for Raspberry Pi 5.
Supports 5-channel passive radar (KrakenSDR).
Performs FFT-based range-Doppler processing efficiently.
"""

import numpy as np
import logging

try:
    import pyfftw
    USE_FFTW = True
except ImportError:
    USE_FFTW = False

logger = logging.getLogger(__name__)


class CAFProcessor:
    """
    Optimized Cross Ambiguity Function processor.

    Parameters:
    ----------
    fs : float
        Sampling frequency [Hz]
    nfft : int
        FFT size for Doppler processing
    overlap : float
        Overlap between consecutive blocks (0–1)
    """

    def __init__(self, fs: float = 1e6, nfft: int = 2048, overlap: float = 0.5):
        self.fs = fs
        self.nfft = nfft
        self.overlap = overlap
        self._fft_cache = {}

        if USE_FFTW:
            logger.info("Using pyFFTW for optimized FFTs.")
        else:
            logger.info("Using NumPy FFT (install pyfftw for more speed).")

    def _fft(self, x):
        """Cached FFT with optional FFTW acceleration."""
        n = len(x)
        if USE_FFTW:
            if n not in self._fft_cache:
                a = pyfftw.empty_aligned(n, dtype='complex64')
                self._fft_cache[n] = a
            a = self._fft_cache[n]
            np.copyto(a, x)
            return pyfftw.interfaces.numpy_fft.fft(a)
        return np.fft.fft(x)

    def _ifft(self, X):
        """IFFT with same optimization."""
        n = len(X)
        if USE_FFTW:
            if n not in self._fft_cache:
                a = pyfftw.empty_aligned(n, dtype='complex64')
                self._fft_cache[n] = a
            a = self._fft_cache[n]
            np.copyto(a, X)
            return pyfftw.interfaces.numpy_fft.ifft(a)
        return np.fft.ifft(X)

    def compute_caf(self, ref: np.ndarray, surv: np.ndarray, doppler_bins: int = 256):
        """
        Compute range-Doppler map (CAF) using FFT-based correlation.

        Parameters:
        -----------
        ref : np.ndarray
            Reference signal (complex64)
        surv : np.ndarray
            Surveillance signal (complex64)
        doppler_bins : int
            Number of Doppler bins

        Returns:
        --------
        caf_map : np.ndarray
            2D Range-Doppler map (magnitude)
        """
        if len(ref) != len(surv):
            min_len = min(len(ref), len(surv))
            ref, surv = ref[:min_len], surv[:min_len]

        n = len(ref)
        seg_len = int(self.nfft * (1 - self.overlap))
        num_segments = max(1, (n - self.nfft) // seg_len + 1)

        caf_map = np.zeros((num_segments, doppler_bins), dtype=np.float32)

        # Precompute reference FFT for each Doppler shift
        ref_fft = self._fft(ref[:self.nfft])
        ref_conj = np.conj(ref_fft)

        for i in range(num_segments):
            start = i * seg_len
            end = start + self.nfft
            seg_surv = surv[start:end]

            if len(seg_surv) < self.nfft:
                break

            # FFT cross-correlation
            surv_fft = self._fft(seg_surv)
            cross_spec = surv_fft * ref_conj
            corr = self._ifft(cross_spec)
            power = np.abs(corr)

            # Doppler FFT (across segments)
            doppler_spectrum = np.fft.fftshift(np.fft.fft(power, doppler_bins))
            caf_map[i, :] = np.abs(doppler_spectrum)

        return caf_map / np.max(caf_map + 1e-12)

    def process_multi(self, refs: list, surfs: list):
        """
        Process multiple channels (e.g., 5 for KrakenSDR).

        Returns averaged CAF map.
        """
        assert len(refs) == len(surfs), "Mismatched channel counts"
        maps = []
        for r, s in zip(refs, surfs):
            maps.append(self.compute_caf(r, s))
        return np.mean(maps, axis=0)


if __name__ == "__main__":
    import time

    fs = 1e6
    N = 8192
    ref = np.exp(1j * 2 * np.pi * 0.05 * np.arange(N))
    surv = np.roll(ref, 200) * np.exp(1j * 2 * np.pi * 0.01 * np.arange(N))

    caf = CAFProcessor(fs=fs, nfft=2048)
    t0 = time.time()
    result = caf.compute_caf(ref, surv)
    print(f"CAF computed: {result.shape}, time={time.time()-t0:.3f}s")
