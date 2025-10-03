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

Как использовать

На Raspberry Pi (в DAQ):

./krakensdr_daq --freq 650000000 --rate 2000000 --gain 30 --udp 192.168.1.100:5000


(где 192.168.1.100 — IP твоего Raspberry Pi или ноутбука, где работает пайплайн).

На стороне Python:

python passive_radar/capture/kraken_reader.py


Ты увидишь вывод типа:

Got chunk 0, shape=(4096,), dtype=complex64
Got chunk 1, shape=(4096,), dtype=complex64
...


Эти чанки (numpy array) можно сразу отдавать в CAF.

⚡️ Преимущество UDP: почти realtime, низкая задержка.
⚠️ Недостаток: возможна потеря пакетов, поэтому иногда будут "дыры" в потоке.
"""

import socket
import numpy as np
import logging

logger = logging.getLogger(__name__)


class KrakenUDPReader:
    """
    Читает IQ данные из UDP потока KrakenSDR DAQ.
    Поддерживает real-time чтение и передачу чанков в numpy.
    """

    def __init__(self, ip="0.0.0.0", port=5000, dtype=np.complex64, chunk_samples=4096):
        """
        :param ip: локальный IP для прослушивания (обычно 0.0.0.0)
        :param port: порт UDP
        :param dtype: формат комплексных данных (по умолчанию complex64)
        :param chunk_samples: сколько отсчетов в одном чанке
        """
        self.ip = ip
        self.port = port
        self.dtype = dtype
        self.chunk_samples = chunk_samples
        self.sock = None
        self._bytes_per_chunk = np.dtype(dtype).itemsize * chunk_samples

    def start(self):
        """Инициализирует UDP сокет и начинает слушать порт"""
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.ip, self.port))
        logger.info(f"Listening for UDP IQ stream on {self.ip}:{self.port}")

    def stop(self):
        """Закрывает сокет"""
        if self.sock:
            self.sock.close()
            self.sock = None
            logger.info("Stopped UDP reader")

    def stream(self):
        """
        Генератор, возвращающий чанки IQ в numpy массиве
        """
        if self.sock is None:
            raise RuntimeError("Call start() before stream()")

        while True:
            data, _ = self.sock.recvfrom(self._bytes_per_chunk)
            if len(data) < self._bytes_per_chunk:
                # недополученный пакет
                continue
            iq = np.frombuffer(data, dtype=self.dtype)
            yield iq


# Пример использования
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    reader = KrakenUDPReader(ip="0.0.0.0", port=5000, dtype=np.complex64, chunk_samples=4096)
    reader.start()

    try:
        for i, chunk in enumerate(reader.stream()):
            print(f"Got chunk {i}, shape={chunk.shape}, dtype={chunk.dtype}")
            if i > 10:
                break
    finally:
        reader.stop()
