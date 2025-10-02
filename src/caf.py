#!/usr/bin/env python3
"""
caf.py
Вычисление CAF (Cross-Ambiguity Function) для пассивного радара.
Сохраняет CAF-матрицу и Range-Doppler карту для последующей обработки.
Запуск:
python caf.py --ref ref.npy --echo echo.npy --sr 2400000 --out results
"""

import numpy as np
from numpy.fft import fft, ifft, fftshift


class CAFProcessor:
    def __init__(self, sample_rate: float, block_size: int = 2**14):
        """
        :param sample_rate: частота дискретизации (Гц)
        :param block_size: размер блока для FFT
        """
        self.sample_rate = sample_rate
        self.block_size = block_size

    def compute_caf_block(self, ref: np.ndarray, echo: np.ndarray):
        """
        Вычисляет CAF для одного блока данных.
        :param ref: опорный сигнал (np.ndarray complex)
        :param echo: эхо сигнал (np.ndarray complex)
        :return: CAF карта (np.ndarray complex)
        """
        if len(ref) != len(echo):
            min_len = min(len(ref), len(echo))
            ref = ref[:min_len]
            echo = echo[:min_len]

        # FFT обоих сигналов
        REF = fft(ref, n=self.block_size)
        ECHO = fft(echo, n=self.block_size)

        # CAF = IFFT(Ref * conj(Echo))
        CAF = ifft(REF * np.conj(ECHO))

        # Перенос в центр (симметричные задержки)
        CAF = fftshift(CAF)

        return CAF

    def compute_caf_stream(self, ref: np.ndarray, echo: np.ndarray):
        """
        CAF для длинного потока (разбиение на блоки).
        :param ref: длинный опорный сигнал
        :param echo: длинный эхо сигнал
        :return: матрица CAF (time x delay)
        """
        block_size = self.block_size
        n_blocks = min(len(ref), len(echo)) // block_size

        caf_matrix = []
        for i in range(n_blocks):
            r_block = ref[i*block_size:(i+1)*block_size]
            e_block = echo[i*block_size:(i+1)*block_size]
            caf_block = self.compute_caf_block(r_block, e_block)
            caf_matrix.append(np.abs(caf_block))

        return np.array(caf_matrix)

    def doppler_processing(self, caf_matrix: np.ndarray):
        """
        Доплеровская обработка: FFT вдоль времени.
        :param caf_matrix: CAF (time x delay)
        :return: Range-Doppler Map
        """
        RDmap = fftshift(fft(caf_matrix, axis=0), axes=0)
        return np.abs(RDmap)


if __name__ == "__main__":
    import argparse
    import matplotlib.pyplot as plt
    import os

    parser = argparse.ArgumentParser(description="Compute CAF from IQ signals")
    parser.add_argument("--ref", required=True, help="Path to reference .npy")
    parser.add_argument("--echo", required=True, help="Path to echo .npy")
    parser.add_argument("--sr", type=float, default=2.4e6, help="Sample rate")
    parser.add_argument("--out", default="results", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Загружаем данные
    ref = np.load(args.ref)
    echo = np.load(args.echo)

    caf = CAFProcessor(sample_rate=args.sr, block_size=2**14)
    caf_matrix = caf.compute_caf_stream(ref, echo)

    # Доплер карта
    rdmap = caf.doppler_processing(caf_matrix)

    # Сохраняем данные
    np.save(os.path.join(args.out, "caf_matrix.npy"), caf_matrix)
    np.save(os.path.join(args.out, "rdmap.npy"), rdmap)

    # Визуализация
    plt.figure(figsize=(10, 6))
    plt.imshow(
        20*np.log10(rdmap + 1e-6),
        aspect="auto",
        origin="lower",
        extent=[-caf.block_size/2, caf.block_size/2, -caf.block_size/2, caf.block_size/2],
        cmap="viridis"
    )
    plt.colorbar(label="dB")
    plt.title("Range-Doppler Map (CAF)")
    plt.xlabel("Delay bins")
    plt.ylabel("Doppler bins")
    plt.savefig(os.path.join(args.out, "rdmap.png"))
    plt.show()
