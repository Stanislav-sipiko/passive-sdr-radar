# Установка

Требования:
- Python 3.9+
- pip

Рекомендуется создать виртуальное окружение:
```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows
```
# Установить зависимости:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```
# Для KrakenSDR — установи нативные драйверы/утилиты (см. документацию KrakenSDR).

- 4) `docs/usage.md`
```markdown
# Примеры запуска
- Прогнать демонстрационный pipeline (examples/test_pipeline.py):
- Откалибровать IQ и сохранить .npy:
```bash
python passive_radar/capture/kraken_reader.py path/to/iq_dir --out calibrated.npy
```
- Построить CAF и сохранить RD map:
```markdown
python passive_radar/caf/caf.py --ref calibrated_ref.npy --echo calibrated_echo.npy --out results
```
- Сделать CFAR:
  ```markdown
  python passive_radar/detect/cfar.py --input results/rdmap.npy --out results

# 5) `docs/api.md`
```markdown
# API / Быстрая навигация по коду

- `passive_radar.capture.kraken_reader` — load_channels(), remove_dc(), normalize(), calibrate_phase(), save_npy()
- `passive_radar.caf.caf` — CAFProcessor.compute_caf_block(), compute_caf_stream(), doppler_processing()
- `passive_radar.preprocess.filters` — mti_filter(), fir_highpass(), normalize()
- `passive_radar.detect.cfar` — cfar_2d(), extract_detections()
- `passive_radar.postprocess.morphology` — morph_clean(), label_regions()
- `passive_radar.postprocess.clustering` — extract_points(), cluster_dbscan(), cluster_hdbscan()
- `passive_radar.track.tracker` — Tracker.update(), Track class
- `passive_radar.output.saver` — save_event(), save_patch(), manifest helpers
- `passive_radar.tools.utils` — cfar_threshold(), cluster_detections(), db(), normalize()
```





```bash
python examples/test_pipeline.py
