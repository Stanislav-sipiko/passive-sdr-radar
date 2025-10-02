#!/usr/bin/env python3
"""
kraken_reader.py
Чтение и калибровка IQ данных с KrakenSDR.
Что делает скрипт:
Загружает несколько IQ-файлов (по одному на канал, например ch0.iq, ch1.iq, …).
Объединяет их в один numpy-массив с формой (channels, samples).
Выполняет DC-offset removal и normalization.
Делает межканальную фазовую калибровку (по известному опорному сигналу или кросс-корреляцией).
Выводит откалиброванные данные для дальнейшей обработки (CAF, MTI и т.п.).
Как использовать

Загрузи IQ-файлы в папку dataset/:
dataset/
  ch0.iq
  ch1.iq
  ch2.iq
  ch3.iq
  ch4.iq
Запусти:
python kraken_reader.py dataset/ --out calibrated.npy
Получишь файл:
calibrated.npy
В других скриптах загружай:
import numpy as np
data = np.load("calibrated.npy")  # shape: (channels, samples)
print(data.shape)
"""

import numpy as np
import glob
import os

class KrakenReader:
    def __init__(self, iq_dir: str, sample_rate: float = 2.4e6, dtype=np.complex64):
        """
        :param iq_dir: путь к папке с IQ файлами (ch0.iq, ch1.iq, …)
        :param sample_rate: частота дискретизации (Гц)
        :param dtype: формат данных (по умолчанию complex64)
        """
        self.iq_dir = iq_dir
        self.sample_rate = sample_rate
        self.dtype = dtype
        self.channels = []
        self.data = None

    def _read_iq_file(self, filename: str) -> np.ndarray:
        """Читает один IQ-файл в numpy массив complex64"""
        raw = np.fromfile(filename, dtype=np.complex64)
        return raw

    def load_channels(self):
        """Загружает все каналы (файлы вида chX.iq)"""
        files = sorted(glob.glob(os.path.join(self.iq_dir, "ch*.iq")))
        if not files:
            raise FileNotFoundError(f"No IQ files found in {self.iq_dir}")

        self.channels = files
        arrays = []

        for f in files:
            print(f"[INFO] Loading {f}")
            arr = self._read_iq_file(f)
            arrays.append(arr)

        # Обрезаем до одинаковой длины
        min_len = min(len(a) for a in arrays)
        arrays = [a[:min_len] for a in arrays]

        self.data = np.vstack(arrays)  # shape: (channels, samples)
        print(f"[INFO] Loaded shape = {self.data.shape}")
        return self.data

    def remove_dc(self):
        """Удаление DC смещения"""
        if self.data is None:
            raise RuntimeError("Data not loaded")
        self.data = self.data - np.mean(self.data, axis=1, keepdims=True)
        return self.data

    def normalize(self):
        """Нормализация амплитуды по каналам"""
        if self.data is None:
            raise RuntimeError("Data not loaded")
        rms = np.sqrt(np.mean(np.abs(self.data) ** 2, axis=1, keepdims=True))
        self.data = self.data / rms
        return self.data

    def calibrate_phase(self, ref_channel=0):
        """
        Межканальная фазовая калибровка.
        Считаем относительные фазовые сдвиги по кросс-корреляции.
        """
        if self.data is None:
            raise RuntimeError("Data not loaded")

        ref = self.data[ref_channel]
        for ch in range(self.data.shape[0]):
            if ch == ref_channel:
                continue
            # оценим среднюю фазу по корреляции
            phase_offset = np.angle(np.vdot(ref, self.data[ch]))
            self.data[ch] *= np.exp(-1j * phase_offset)
            print(f"[CALIB] Channel {ch} phase corrected by {phase_offset:.4f} rad")

        return self.data

    def save_npy(self, out_file="calibrated_iq.npy"):
        """Сохраняет результат в .npy"""
        if self.data is None:
            raise RuntimeError("Data not loaded")
        np.save(out_file, self.data)
        print(f"[SAVE] Data saved to {out_file}, shape={self.data.shape}")
        return out_file

    def get_data(self):
        """Возвращает откалиброванные данные"""
        return self.data


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KrakenSDR IQ Reader + Calibration")
    parser.add_argument("iq_dir", help="Directory with ch0.iq, ch1.iq, ...")
    parser.add_argument("--out", default="calibrated_iq.npy", help="Output .npy file")
    args = parser.parse_args()

    kr = KrakenReader(args.iq_dir)
    kr.load_channels()
    kr.remove_dc()
    kr.normalize()
    kr.calibrate_phase(ref_channel=0)
    kr.save_npy(args.out)

    data = kr.get_data()
    print(f"[DONE] Data shape = {data.shape}, dtype = {data.dtype}")
