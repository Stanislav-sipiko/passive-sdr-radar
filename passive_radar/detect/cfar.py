#!/usr/bin/env python3
"""
cfar.py
CFAR (Constant False Alarm Rate) детектор для Range-Doppler карт.
Что делает скрипт
Загружает rdmap.npy из CAF.
Применяет 2D CA-CFAR (с защитными и опорными ячейками).
Строит:
det_map.npy — бинарная карта целей.
thr_map.npy — карта порогов.
detections.npy — список пиков (doppler, range, power).
cfar_detections.png — картинка с отмеченными целями.

 Запуск:
python cfar.py --input results/rdmap.npy --out results
"""

import numpy as np
import matplotlib.pyplot as plt
import os


def cfar_2d(rdmap, guard_cells=(2, 2), ref_cells=(8, 8), pfa=1e-3):
    """
    2D CA-CFAR по Range-Doppler карте.

    :param rdmap: входная карта (2D numpy array, amplitudes)
    :param guard_cells: (doppler, range) число защитных ячеек вокруг CUT
    :param ref_cells: (doppler, range) число опорных ячеек вокруг зоны CUT
    :param pfa: вероятность ложной тревоги
    :return: detection_map (бинарная карта), threshold_map (уровень порога)
    """
    n_doppler, n_range = rdmap.shape
    det_map = np.zeros_like(rdmap, dtype=np.uint8)
    thr_map = np.zeros_like(rdmap, dtype=float)

    # коэффициент (для CA-CFAR с суммированием мощности)
    alpha = ref_cells[0]*ref_cells[1]*((pfa**(-1/(ref_cells[0]*ref_cells[1])))-1)

    for i in range(ref_cells[0] + guard_cells[0], n_doppler - (ref_cells[0] + guard_cells[0])):
        for j in range(ref_cells[1] + guard_cells[1], n_range - (ref_cells[1] + guard_cells[1])):

            # область для опорных ячеек
            dop_min = i - (ref_cells[0] + guard_cells[0])
            dop_max = i + (ref_cells[0] + guard_cells[0])
            rng_min = j - (ref_cells[1] + guard_cells[1])
            rng_max = j + (ref_cells[1] + guard_cells[1])

            window = rdmap[dop_min:dop_max+1, rng_min:rng_max+1].copy()
            # вырезаем область защитных ячеек
            window[(ref_cells[0]):-(ref_cells[0]+1), (ref_cells[1]):-(ref_cells[1]+1)] = 0

            # средний уровень шума
            noise_level = np.sum(window) / (window.size - (2*guard_cells[0]+1)*(2*guard_cells[1]+1))
            threshold = alpha * noise_level
            thr_map[i, j] = threshold

            # проверка CUT
            if rdmap[i, j] > threshold:
                det_map[i, j] = 1

    return det_map, thr_map


def extract_detections(det_map, rdmap, threshold=0):
    """
    Извлечение списка детекций (пиков).
    :param det_map: бинарная карта CFAR
    :param rdmap: исходная RD карта
    :param threshold: минимальная мощность для записи
    :return: список детекций [(doppler, range, power), ...]
    """
    detections = []
    idx = np.argwhere(det_map == 1)
    for (i, j) in idx:
        power = rdmap[i, j]
        if power > threshold:
            detections.append((i, j, power))
    return detections


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CFAR detection on Range-Doppler map")
    parser.add_argument("--input", required=True, help="Path to rdmap.npy")
    parser.add_argument("--out", default="results", help="Output directory")
    args = parser.parse_args()

    os.makedirs(args.out, exist_ok=True)

    # Загружаем Range-Doppler карту
    rdmap = np.load(args.input)

    # CFAR
    det_map, thr_map = cfar_2d(rdmap, guard_cells=(2, 2), ref_cells=(8, 8), pfa=1e-3)

    # Извлечение целей
    detections = extract_detections(det_map, rdmap, threshold=10)

    # Сохраняем данные
    np.save(os.path.join(args.out, "det_map.npy"), det_map)
    np.save(os.path.join(args.out, "thr_map.npy"), thr_map)
    np.save(os.path.join(args.out, "detections.npy"), np.array(detections, dtype=object))

    # Визуализация
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    plt.title("Range-Doppler Map (dB)")
    plt.imshow(20*np.log10(rdmap + 1e-6), aspect="auto", origin="lower", cmap="viridis")
    plt.colorbar(label="dB")

    plt.subplot(1, 2, 2)
    plt.title("CFAR Detections")
    plt.imshow(det_map, aspect="auto", origin="lower", cmap="gray_r")
    plt.colorbar(label="Detections (1=True)")

    plt.tight_layout()
    plt.savefig(os.path.join(args.out, "cfar_detections.png"))
    plt.show()
