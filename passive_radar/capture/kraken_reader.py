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

    Как это работает
    Модуль               	Задача
UDP Reader            	Читает поток IQ-данных от KrakenSDR по UDP и пишет в shared memory
Shared Memory	          Общий буфер между процессами, чтобы не копировать IQ-данные
CAF Workers (×5)	      Каждый процесс берёт «свой» канал и выполняет CAF (например, cross-ambiguity-function)
Event Sync	            Синхронизирует запуск — чтобы CAF-процессы не начали раньше, чем reader создаст поток

"""
import socket
import numpy as np
from multiprocessing import shared_memory, Process, Event
from passive_radar.caf.caf import process_iq_block

# ────────────────────────────────
# Константы
# ────────────────────────────────
SAMPLE_RATE = 1_000_000          # Гц
BLOCK_SIZE = 32768               # выборок на канал
CHANNELS = 5                     # KrakenSDR: 5 каналов
DTYPE = np.complex64
NUM_BLOCKS = 8                   # глубина кольцевого буфера
UDP_PORT = 5000

# ────────────────────────────────
# Shared Memory Буфер
# ────────────────────────────────
class SharedIQBuffer:
    """Общий буфер IQ-данных для обмена между процессами без копирования."""

    def __init__(self, channels=CHANNELS, num_blocks=NUM_BLOCKS, block_size=BLOCK_SIZE):
        self.channels = channels
        self.num_blocks = num_blocks
        self.block_shape = (channels, block_size)
        self.block_size_bytes = np.prod(self.block_shape) * np.dtype(DTYPE).itemsize
        self.total_size = self.num_blocks * self.block_size_bytes

        self.shm = shared_memory.SharedMemory(create=True, size=self.total_size)
        self.buffer = np.ndarray((self.num_blocks, *self.block_shape), dtype=DTYPE, buffer=self.shm.buf)

        self.write_index = 0

    def write_block(self, iq_block):
        idx = self.write_index % self.num_blocks
        self.buffer[idx] = iq_block
        self.write_index += 1
        return idx

    def get_block(self, idx):
        return self.buffer[idx % self.num_blocks]

    def close(self):
        self.shm.close()
        self.shm.unlink()

# ────────────────────────────────
# UDP Reader
# ────────────────────────────────
def udp_reader(shared_name, num_blocks, ready_event):
    """Слушает UDP-поток от KrakenSDR и пишет IQ в shared memory."""
    shm = shared_memory.SharedMemory(name=shared_name)
    buffer = np.ndarray((num_blocks, CHANNELS, BLOCK_SIZE), dtype=DTYPE, buffer=shm.buf)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", UDP_PORT))
    print(f"[UDP] Listening on port {UDP_PORT}")

    packet_size = BLOCK_SIZE * CHANNELS * 8  # complex64 = 8 bytes
    write_idx = 0
    ready_event.set()  # сообщаем, что читатель готов

    while True:
        data, _ = sock.recvfrom(packet_size)
        iq = np.frombuffer(data, dtype=np.complex64).reshape(CHANNELS, BLOCK_SIZE)
        buffer[write_idx % num_blocks] = iq
        write_idx += 1

# ────────────────────────────────
# CAF Worker (один процесс на канал)
# ────────────────────────────────
def caf_worker(shared_name, num_blocks, channel_id, start_event):
    """Читает блоки из shared memory для конкретного канала и выполняет CAF."""
    shm = shared_memory.SharedMemory(name=shared_name)
    buffer = np.ndarray((num_blocks, CHANNELS, BLOCK_SIZE), dtype=DTYPE, buffer=shm.buf)

    print(f"[CAF-{channel_id}] Started")
    start_event.wait()  # ждём, пока reader начнёт писать

    read_idx = 0
    while True:
        block = buffer[read_idx % num_blocks][channel_id]
        process_iq_block(block, channel_id=channel_id)  # поддержка многоканальности
        read_idx += 1

# ────────────────────────────────
# Main
# ────────────────────────────────
if __name__ == "__main__":
    shared_buf = SharedIQBuffer()

    ready_event = Event()

    # Запускаем UDP reader
    p_udp = Process(target=udp_reader, args=(shared_buf.shm.name, shared_buf.num_blocks, ready_event))
    p_udp.start()

    # Запускаем 5 CAF-процессов (по одному на канал)
    workers = []
    for ch in range(CHANNELS):
        p = Process(target=caf_worker, args=(shared_buf.shm.name, shared_buf.num_blocks, ch, ready_event))
        p.start()
        workers.append(p)

    print(f"[System] Running with {CHANNELS} CAF workers on shared memory")

    p_udp.join()
    for p in workers:
        p.join()
