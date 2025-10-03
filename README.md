[![CI](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions)
[![Docs](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions/workflows/docs.yml/badge.svg)](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions)

# Passive SDR Radar Project

Passive radar implementation using KrakenSDR.  
Pipeline: IQ → CAF → MTI/CFAR → Clustering → Tracking.
# Quick start
```bash
docker build -t passive-radar .
docker run --rm passive-radar
```
или через docker-compose:
```bash
docker-compose up --build
```

<a href="https://totoha.com/passive_radar/index.html" target="_blank" >Как отделить статические отражения от динамических целей</a>
---

## 🎯 Цель проекта
Разработать пассивный радар для обнаружения воздушных целей (БПЛА, ракеты) с использованием сигналов DVB-T2 и приёмников KrakenSDR.  
Система должна:
- Отфильтровывать статические отражения
- Детектировать и сопровождать движущиеся цели
- Передавать данные в реальном времени для отображения на карте

---

## ⚙️ Требования

- **ОС:** Linux (Ubuntu 20.04+), Windows 10/11
- **Python:** 3.9+
- **Зависимости:** см. [`requirements.txt`](requirements.txt)
- **Оборудование:** KrakenSDR (5-канальный SDR), GPS/PPS для синхронизации

---

## 🚀 Установка и запуск

```bash
git clone https://github.com/Stanislav-sipiko/passive-sdr-radar.git
cd passive-sdr-radar
pip install -r requirements.txt
python main.py
```
---
## 📂 Структура проекта
```bash
passive_radar/
├─ capture/       # чтение и калибровка IQ данных
├─ caf/           # вычисление CAF
├─ preprocess/    # фильтры MTI, high-pass
├─ detect/        # CFAR детекция
├─ postprocess/   # морфология, кластеризация
├─ track/         # трекер (Kalman + Hungarian)
├─ output/        # сохранение результатов
├─ realtime/      # websocket сервер для карты
└─ tools/         # утилиты
```
---
## Блок-схема
<img width="241" height="342" alt="block_shema" src="https://github.com/user-attachments/assets/9979d670-d4c0-4efe-b2ce-ed88b8bd6256" />

---

## Логика:

- capture/kraken_reader.py → читает и калибрует IQ.
- preprocess/filters.py → нормализует, фильтрует, убирает помехи.
- caf/caf.py → считает CAF.
- detect/cfar.py → находит пики.
- postprocess/morphology.py + clustering.py → чистка + объединение целей.
- track/tracker.py → сопровождение.
- output/saver.py → сохраняет результаты.
- realtime/ws_server.py → стрим в реальном времени.

---
## 🛰 Пример работы

Входные данные: IQ-файлы (reference + surveillance канал)
Выходные данные: карта детекций + треки целей (JSON, WebSocket)
```json
{
  "id": 12,
  "range": 15.2,
  "doppler": -45.3,
  "velocity": 140,
  "timestamp": "2025-10-02T18:24:12Z"
}
```
---
## 📊 Визуализации
- CAF карта (Delay × Doppler)
- Детекции после CFAR
- Треки целей на карте (Leaflet + WebSocket)

---
## 📌 TODO

- Подключение реальных данных с KrakenSDR
- Улучшение CFAR и фильтрации
- Трекинг с идентификацией целей
 
---
## 📜 Лицензия
GPL-3.0
