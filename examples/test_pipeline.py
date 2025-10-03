"""
Test pipeline for Passive SDR Radar
-----------------------------------
Пример демонстрирует полный цикл обработки:
IQ → фильтры → CAF → CFAR → морфология → кластеризация → трекер → сохранение результатов.
"""

import numpy as np

from passive_radar.capture.kraken_reader import load_iq, calibrate_iq
from passive_radar.preprocess.filters import mti_filter, fir_highpass, normalize
from passive_radar.caf.caf import compute_caf_block
from passive_radar.detect.cfar import cfar_2d, extract_peaks
from passive_radar.postprocess.morphology import morph_clean
from passive_radar.postprocess.clustering import dbscan_cluster
from passive_radar.track.tracker import MultiTargetTracker
from passive_radar.output.saver import save_event, save_manifest


def run_pipeline(iq_file: str, sample_rate: float = 1e6):
    print(f"[INFO] Загружаем IQ из {iq_file} ...")
    iq_data = load_iq(iq_file)
    iq_data = calibrate_iq(iq_data)

    # === Preprocess ===
    iq_data = normalize(iq_data)
    iq_data = fir_highpass(iq_data)
    iq_data = mti_filter(iq_data)

    # === CAF ===
    caf_matrix = compute_caf_block(iq_data, ref_channel=0, sr=sample_rate)

    # === CFAR ===
    cfar_mask = cfar_2d(caf_matrix)
    peaks = extract_peaks(caf_matrix, cfar_mask)

    # === Morphology ===
    cleaned = morph_clean(cfar_mask)

    # === Clustering ===
    clustered = dbscan_cluster(peaks)

    # === Tracking ===
    tracker = MultiTargetTracker()
    tracked = tracker.update(clustered)

    # === Output ===
    save_event("results", tracked)
    save_manifest("results")

    print(f"[INFO] Найдено целей: {len(tracked)}")
    for t in tracked:
        print(f"  → ID={t['id']} pos={t['pos']} vel={t['vel']}")


if __name__ == "__main__":
    # Для теста можно указать файл с IQ-данными или сгенерировать
    test_file = "examples/sample_iq.dat"
    run_pipeline(test_file)

