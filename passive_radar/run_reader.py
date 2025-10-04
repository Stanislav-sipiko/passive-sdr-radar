"""
run_reader.py — загрузка конфигурации и запуск IQ reader
Запуск
# Чтение UDP потока
python run_reader.py --mode udp

# или чтение IQ-файла
python run_reader.py --mode file


(Режим выбирается через config.yaml.)
"""

import yaml
from passive_radar.capture.kraken_reader import get_iq_source
import logging

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_config(path="config.yaml"):
    """Загрузка YAML-конфига."""
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    mode = cfg["mode"]

    if mode == "file":
        file_cfg = cfg["file"]
        source = get_iq_source(
            mode="file",
            file_path=file_cfg["path"],
            chunk_size=file_cfg.get("chunk_size", 4096),
        )
    elif mode == "udp":
        udp_cfg = cfg["udp"]
        source = get_iq_source(
            mode="udp",
            host=udp_cfg["host"],
            port=udp_cfg["port"],
        )
    else:
        raise ValueError(f"Неизвестный режим: {mode}")

    logger.info(f"Старт чтения IQ данных (режим: {mode})...")

    for i, block in enumerate(source):
        logger.info(f"[{i}] Получен блок: {len(block)} IQ-сэмплов")
        if i >= 10:  # ограничим количество итераций для теста
            break


if __name__ == "__main__":
    main()
