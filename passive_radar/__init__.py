"""
Passive Radar package
=====================

Этот пакет содержит модули для реализации пассивного радара
с использованием SDR (например, KrakenSDR) и обработки сигналов.

Структура пакета:
-----------------
- capture     → чтение и предварительная обработка IQ данных
- detection   → алгоритмы CFAR/CA-CFAR и выделение целей
- tracking    → трекер и ассоциация целей
- postprocess → морфология, фильтрация и дообработка
- tools       → утилиты (нормализация, логирование, вспомогательные функции)

Пример использования:
---------------------
from passive_radar.capture import kraken_reader
from passive_radar.tools.utils import detect_peaks_cfar, db
"""

__version__ = "0.1.0"
__author__ = "Stanislav Rafalski"
__license__ = "MIT"

# Упрощённые импорты для верхнего уровня
from .tools import utils
from .capture import kraken_reader
