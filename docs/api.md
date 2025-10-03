
# 5) docs/api.md
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
