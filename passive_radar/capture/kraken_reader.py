"""
kraken_reader.py — модуль для приёма IQ данных от KrakenSDR.

Поддерживает два режима:
  • file — чтение заранее записанных бинарных файлов IQ
  • udp  — приём потока IQ-данных в реальном времени через UDP

Каждый IQ сэмпл представлен как пара float32 (I, Q).

Как использовать
📘 1. Чтение локального файла:
from passive_radar.capture.kraken_reader import get_iq_source

for block in get_iq_source(mode="file", file_path="data/test_iq.bin"):
    print(block[:5])

🌐 2. Чтение UDP потока:
from passive_radar.capture.kraken_reader import get_iq_source

for block in get_iq_source(mode="udp", host="0.0.0.0", port=5000):
    print(f"Получен блок: {len(block)}")
"""
import socket
import struct
import numpy as np
import time
from pathlib import Path
from typing import Optional, Callable

class KrakenReader:
    """
    Универсальный источник IQ-данных:
      - file: читает из .bin файла (запись с KrakenSDR)
      - udp: читает поток IQ в реальном времени по UDP
    Может автоматически передавать данные в CAF (Correlation and Ambiguity Function).
    """

    def __init__(
        self,
        mode: str = "file",
        source: str = "capture.bin",
        sample_rate: float = 2.4e6,
        num_channels: int = 5,
        block_size: int = 262144,
        caf_callback: Optional[Callable[[np.ndarray], None]] = None,
        udp_ip: str = "0.0.0.0",
        udp_port: int = 5000,
        dtype=np.complex64,
    ):
        assert mode in ("file", "udp"), "mode must be 'file' or 'udp'"
        self.mode = mode
        self.source = source
        self.sample_rate = sample_rate
        self.num_channels = num_channels
        self.block_size = block_size
        self.caf_callback = caf_callback
        self.udp_ip = udp_ip
        self.udp_port = udp_port
        self.dtype = dtype
        self.sock = None
        self.running = False

    def _read_block_file(self, f):
        """Считывает один блок данных из файла."""
        bytes_per_sample = np.dtype(self.dtype).itemsize
        total_samples = self.block_size * self.num_channels
        data = f.read(total_samples * bytes_per_sample)
        if not data or len(data) < total_samples * bytes_per_sample:
            return None
        iq = np.frombuffer(data, dtype=self.dtype)
        iq = iq.reshape((self.num_channels, -1))
        return iq

    def _read_block_udp(self):
        """Приём IQ-данных по UDP."""
        packet_size = self.block_size * self.num_channels * np.dtype(self.dtype).itemsize
        data, _ = self.sock.recvfrom(packet_size)
        if not data:
            return None
        iq = np.frombuffer(data, dtype=self.dtype)
        iq = iq.reshape((self.num_channels, -1))
        return iq

    def start(self):
        """Запуск чтения данных и автоматическая передача в CAF."""
        self.running = True
        print(f"[KrakenReader] Starting in '{self.mode}' mode...")

        if self.mode == "file":
            file_path = Path(self.source)
            assert file_path.exists(), f"File not found: {file_path}"
            with open(file_path, "rb") as f:
                while self.running:
                    block = self._read_block_file(f)
                    if block is None:
                        print("[KrakenReader] EOF reached.")
                        break
                    if self.caf_callback:
                        self.caf_callback(block)
        else:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.bind((self.udp_ip, self.udp_port))
            print(f"[KrakenReader] Listening UDP on {self.udp_ip}:{self.udp_port}")
            while self.running:
                try:
                    block = self._read_block_udp()
                    if block is None:
                        continue
                    if self.caf_callback:
                        self.caf_callback(block)
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"[KrakenReader] Error: {e}")
                    time.sleep(0.5)

        print("[KrakenReader] Stopped.")

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
        print("[KrakenReader] Stop signal received.")


# === Пример использования ===
if __name__ == "__main__":
    from passive_radar.caf import caf_process_block  # пример: подключаем ваш модуль CAF

    def process_block(block):
        print(f"[Reader] Got block shape={block.shape}")
        caf_process_block(block)  # передаём напрямую в CAF

    reader = KrakenReader(
        mode="udp",          # или "file"
        udp_ip="0.0.0.0",
        udp_port=5000,
        block_size=65536,
        num_channels=5,
        caf_callback=process_block,
    )

    reader.start()
