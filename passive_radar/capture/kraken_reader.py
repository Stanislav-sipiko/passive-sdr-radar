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

import numpy as np
import socket
import struct
import logging
from pathlib import Path
from typing import Generator, Optional

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ==========================================================
# FILE MODE
# ==========================================================
def read_iq_file(file_path: str, chunk_size: int = 4096) -> Generator[np.ndarray, None, None]:
    """
    Читает IQ данные из бинарного файла (float32 interleaved I/Q).

    Args:
        file_path: путь к .bin файлу.
        chunk_size: количество сэмплов (пар I/Q) за один шаг.

    Yields:
        np.ndarray complex64 — блок IQ данных.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Файл не найден: {file_path}")

    logger.info(f"[FILE] Чтение IQ из {file_path}")

    with open(file_path, "rb") as f:
        while True:
            data = np.frombuffer(f.read(chunk_size * 2 * 4), dtype=np.float32)
            if len(data) == 0:
                break
            iq = data[::2] + 1j * data[1::2]
            yield iq


# ==========================================================
# UDP MODE
# ==========================================================
class UDPReader:
    """
    UDP-приёмник для потока IQ-данных.

    Формат пакета:
      [I(float32), Q(float32), I(float32), Q(float32), ...]

    Можно использовать KrakenSDR DAQ → UDP Stream.

    Пример:
      reader = UDPReader("0.0.0.0", 5000)
      for iq_block in reader.read_stream():
          process(iq_block)
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 5000, buffer_size: int = 8192):
        self.host = host
        self.port = port
        self.buffer_size = buffer_size
        self.sock: Optional[socket.socket] = None

    def start(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.host, self.port))
        logger.info(f"[UDP] Слушаем {self.host}:{self.port}")

    def read_stream(self) -> Generator[np.ndarray, None, None]:
        """
        Потоковый генератор IQ данных.
        Возвращает np.ndarray complex64.
        """
        if self.sock is None:
            self.start()

        while True:
            packet, _ = self.sock.recvfrom(self.buffer_size)
            if not packet:
                continue
            num_floats = len(packet) // 4
            iq_raw = struct.unpack(f"{num_floats}f", packet)
            iq = np.array(iq_raw[::2]) + 1j * np.array(iq_raw[1::2])
            yield iq

    def close(self):
        if self.sock:
            self.sock.close()
            logger.info("[UDP] Соединение закрыто")


# ==========================================================
# UNIFIED INTERFACE
# ==========================================================
def get_iq_source(mode: str = "file", **kwargs):
    """
    Универсальный интерфейс получения IQ-потока.

    Args:
        mode: "file" или "udp".
        kwargs: параметры для режима.
          file → file_path, chunk_size
          udp  → host, port, buffer_size

    Returns:
        генератор блоков IQ (np.ndarray complex64)
    """
    if mode == "file":
        return read_iq_file(kwargs["file_path"], kwargs.get("chunk_size", 4096))
    elif mode == "udp":
        reader = UDPReader(kwargs.get("host", "0.0.0.0"), kwargs.get("port", 5000))
        return reader.read_stream()
    else:
        raise ValueError(f"Неизвестный режим: {mode}")


# ==========================================================
# SELF TEST
# ==========================================================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="KrakenSDR IQ reader")
    parser.add_argument("--mode", choices=["file", "udp"], default="file", help="режим чтения")
    parser.add_argument("--file", type=str, help="путь к .bin файлу")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()

    if args.mode == "file":
        for block in read_iq_file(args.file, chunk_size=2048):
            logger.info(f"Чтено {len(block)} IQ-сэмплов")
    else:
        reader = UDPReader(args.host, args.port)
        for block in reader.read_stream():
            logger.info(f"Получено {len(block)} IQ-сэмплов")
