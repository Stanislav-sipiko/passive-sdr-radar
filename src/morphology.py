# passive_radar/postprocess/morphology.py
"""
Модуль для морфологической постобработки карт обнаружений.
Используется после CFAR для удаления шумов, сглаживания и подготовки данных к кластеризации.
Функции:
morph_clean() — убирает шумные точки, объединяет разрывы и удаляет объекты меньше min_size.
label_regions() — нумерует все выделенные объекты (можно потом отправить в clustering.py).
"""

import numpy as np
from scipy import ndimage
from skimage.morphology import binary_opening, binary_closing, remove_small_objects


def morph_clean(detection_map: np.ndarray,
                min_size: int = 5,
                structure_size: int = 3,
                perform_opening: bool = True,
                perform_closing: bool = True) -> np.ndarray:
    """
    Морфологическая очистка бинарной карты обнаружений.

    Args:
        detection_map (np.ndarray): бинарная карта (0/1) после CFAR.
        min_size (int): минимальный размер объекта для сохранения (меньшие будут удалены).
        structure_size (int): размер структурного элемента (квадрат).
        perform_opening (bool): применять ли морфологическое открытие.
        perform_closing (bool): применять ли морфологическое закрытие.

    Returns:
        np.ndarray: очищенная бинарная карта.
    """
    # Преобразуем в булев тип
    mask = detection_map.astype(bool)

    # Структурный элемент (квадрат)
    struct = np.ones((structure_size, structure_size), dtype=bool)

    # Морфологическое открытие (удаление шумных пикселей)
    if perform_opening:
        mask = binary_opening(mask, struct)

    # Морфологическое закрытие (заполнение дыр)
    if perform_closing:
        mask = binary_closing(mask, struct)

    # Удаляем слишком маленькие объекты
    mask = remove_small_objects(mask, min_size=min_size)

    return mask.astype(np.uint8)


def label_regions(clean_map: np.ndarray) -> tuple[np.ndarray, int]:
    """
    Находит связанные компоненты на очищенной карте.

    Args:
        clean_map (np.ndarray): бинарная карта (0/1).

    Returns:
        labels (np.ndarray): карта, где каждой области присвоен уникальный индекс.
        num (int): количество найденных областей.
    """
    labels, num = ndimage.label(clean_map)
    return labels, num


if __name__ == "__main__":
    # Демонстрация работы
    test = np.zeros((20, 20), dtype=np.uint8)
    test[5:7, 5:7] = 1   # шум
    test[10:14, 10:14] = 1  # крупный объект

    print("До очистки:")
    print(test)

    clean = morph_clean(test, min_size=5, structure_size=2)
    labels, n = label_regions(clean)

    print("После очистки:")
    print(clean)
    print(f"Найдено объектов: {n}")

