# passive_radar/postprocess/clustering.py
"""
Модуль для кластеризации детекций после морфологической очистки.
Используются DBSCAN (из sklearn) и HDBSCAN (если установлен).
Основные шаги:
extract_points() — преобразует бинарную карту в список координат целей.
cluster_dbscan() — стандартная кластеризация DBSCAN.
cluster_hdbscan() — расширенный алгоритм HDBSCAN (если установлен).
"""

import numpy as np
from sklearn.cluster import DBSCAN

try:
    import hdbscan
    HDBSCAN_AVAILABLE = True
except ImportError:
    HDBSCAN_AVAILABLE = False


def extract_points(detection_map: np.ndarray) -> np.ndarray:
    """
    Преобразует бинарную карту в список точек (y, x).

    Args:
        detection_map (np.ndarray): бинарная карта (0/1).

    Returns:
        np.ndarray: массив координат точек (N, 2).
    """
    points = np.argwhere(detection_map > 0)
    return points


def cluster_dbscan(points: np.ndarray,
                   eps: float = 3.0,
                   min_samples: int = 3) -> np.ndarray:
    """
    Кластеризация с помощью DBSCAN.

    Args:
        points (np.ndarray): массив координат (N, 2).
        eps (float): радиус окрестности.
        min_samples (int): минимальное число точек для образования кластера.

    Returns:
        np.ndarray: метки кластеров для каждой точки.
    """
    if len(points) == 0:
        return np.array([])

    db = DBSCAN(eps=eps, min_samples=min_samples)
    labels = db.fit_predict(points)
    return labels


def cluster_hdbscan(points: np.ndarray,
                    min_cluster_size: int = 5,
                    min_samples: int = 3) -> np.ndarray:
    """
    Кластеризация с помощью HDBSCAN (если установлен).

    Args:
        points (np.ndarray): массив координат (N, 2).
        min_cluster_size (int): минимальный размер кластера.
        min_samples (int): минимальное число точек для устойчивости.

    Returns:
        np.ndarray: метки кластеров для каждой точки.
    """
    if not HDBSCAN_AVAILABLE:
        raise ImportError("HDBSCAN не установлен. Установите: pip install hdbscan")

    if len(points) == 0:
        return np.array([])

    clusterer = hdbscan.HDBSCAN(min_cluster_size=min_cluster_size,
                                min_samples=min_samples)
    labels = clusterer.fit_predict(points)
    return labels


if __name__ == "__main__":
    # Демонстрация работы
    test = np.zeros((20, 20), dtype=np.uint8)
    test[5:7, 5:7] = 1
    test[10:14, 10:14] = 1
    test[15:18, 15:18] = 1

    pts = extract_points(test)
    print("Координаты точек:", pts)

    labels_db = cluster_dbscan(pts, eps=2.5, min_samples=2)
    print("DBSCAN метки:", labels_db)

    if HDBSCAN_AVAILABLE:
        labels_hdb = cluster_hdbscan(pts, min_cluster_size=2)
        print("HDBSCAN метки:", labels_hdb)

