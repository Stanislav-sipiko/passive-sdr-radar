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


```bash
python examples/test_pipeline.py
