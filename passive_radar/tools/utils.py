import numpy as np
import scipy.signal as signal
import scipy.ndimage as ndimage
from sklearn.cluster import DBSCAN
import logging
"""
единый utils.py для всего проекта →  passive_radar/tools/utils.py.
В него войдут основные функции из файлов:

src/cfar.py → CFAR пороги и детекция
src/clustering.py → DBSCAN кластеризация
src/morphology.py → морфологическая обработка
общие хелперы (db(), normalize(), логирование и т.п.)

подключать всё так:

from passive_radar.tools.utils import (
    detect_peaks_cfar, cluster_detections, morphological_filter, db
)
"""

# =========================================================
# Логирование
# =========================================================
def setup_logger(name="passive_radar", level=logging.INFO):
    """Инициализация и возврат логгера."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


# =========================================================
# CFAR: детекция целей
# =========================================================
def cfar_threshold(signal_power, guard_cells=2, training_cells=8, rate_fa=1e-3):
    """
    Вычисление CFAR-порога для массива мощности сигнала.
    signal_power : 1D numpy array
    """
    n = len(signal_power)
    threshold = np.zeros(n)

    # Коэффициент по формуле (для CA-CFAR)
    alpha = training_cells * (rate_fa ** (-1 / training_cells) - 1)

    for i in range(n):
        start = max(0, i - guard_cells - training_cells)
        end = min(n, i + guard_cells + training_cells)
        guard_start = max(0, i - guard_cells)
        guard_end = min(n, i + guard_cells)

        training_region = np.concatenate(
            (signal_power[start:guard_start], signal_power[guard_end:end])
        )
        noise_level = np.mean(training_region) if len(training_region) > 0 else 0
        threshold[i] = alpha * noise_level

    return threshold


def detect_peaks_cfar(signal_power, **kwargs):
    """
    Поиск детекций на основе CFAR.
    Возвращает (индексы_детекций, массив_порогов).
    """
    threshold = cfar_threshold(signal_power, **kwargs)
    detections = np.where(signal_power > threshold)[0]
    return detections, threshold


# =========================================================
# Морфологические фильтры (для матриц/heatmap)
# =========================================================
def morphological_filter(image, size=3, mode="open"):
    """
    Применение морфологического фильтра к 2D данным.
    mode = 'open' → бинарное открытие
    mode = 'close' → бинарное закрытие
    """
    if mode == "open":
        return ndimage.binary_opening(image, structure=np.ones((size, size)))
    elif mode == "close":
        return ndimage.binary_closing(image, structure=np.ones((size, size)))
    else:
        raise ValueError("mode must be 'open' или 'close'")


# =========================================================
# Кластеризация детекций (range, doppler)
# =========================================================
def cluster_detections(points, eps=2.0, min_samples=3):
    """
    Кластеризация точек с помощью DBSCAN.
    points : numpy array (N,2) → [[range, doppler], ...]
    Возвращает (labels, model)
    """
    if len(points) == 0:
        return np.array([]), None

    clustering = DBSCAN(eps=eps, min_samples=min_samples).fit(points)
    labels = clustering.labels_
    return labels, clustering


# =========================================================
# Общие вспомогательные функции
# =========================================================
def normalize(data):
    """Нормализация массива в [0,1]."""
    dmin, dmax = np.min(data), np.max(data)
    return (data - dmin) / (dmax - dmin + 1e-12)


def db(x):
    """Перевод мощности из линейного масштаба в dB."""
    return 10 * np.log10(np.abs(x) + 1e-12)


def moving_average(x, N=5):
    """Простой фильтр скользящего среднего."""
    return np.convolve(x, np.ones(N)/N, mode="same")
