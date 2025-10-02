"""
Passive SDR Radar - Main Pipeline
---------------------------------
Простейший демонстрационный скрипт:
IQ → CAF → MTI → CFAR → Morphology → Clustering → Saver
"""

from passive_radar.capture import kraken_reader
from passive_radar.caf import caf
from passive_radar.preprocess import filters
from passive_radar.detect import cfar
from passive_radar.postprocess import morphology, clustering
from passive_radar.output import saver

def main():
    # 1. Загрузка IQ данных (заглушка)
    iq = kraken_reader.load_iq("data/sample.iq")

    # 2. Вычисляем CAF
    caf_matrix = caf.compute_caf_block(iq)

    # 3. MTI фильтрация
    caf_mti = filters.mti_filter(caf_matrix)

    # 4. CFAR детекция
    detections = cfar.cfar_2d(caf_mti)

    # 5. Морфологическая очистка
    detections_clean = morphology.morph_clean(detections)

    # 6. Кластеризация
    clusters = clustering.cluster_detections(detections_clean)

    # 7. Сохраняем результаты
    saver.save_event(clusters, out_dir="results")

    print("Pipeline complete. Events saved.")

if __name__ == "__main__":
    main()
