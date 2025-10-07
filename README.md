[![CI](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions/workflows/python-ci.yml/badge.svg)](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions)
[![Docs](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions/workflows/docs.yml/badge.svg)](https://github.com/Stanislav-sipiko/passive-sdr-radar/actions)

# Passive SDR Radar Project

Passive radar implementation using KrakenSDR.  
Система пассивного радиолокационного наблюдения на основе KrakenSDR, Raspberry Pi 5 и центрального сервера
# Quick start
```bash
docker build -t passive-radar .
docker run --rm passive-radar
```
или через docker-compose:
```bash
docker-compose up --build
```

## 🎯 Цель проекта
Разработать пассивный радар для обнаружения воздушных целей (БПЛА, ракеты) с использованием сигналов DVB-T2 и приёмников KrakenSDR.  
Система должна:
- Отфильтровывать статические отражения
- Детектировать и сопровождать движущиеся цели
- Передавать данные в реальном времени для отображения на карте
- <a href="https://docs.google.com/document/d/1rKGx9qvzOKimBLht7yT1sAatVeAM7iHgrIm9Ku96HbA/edit?usp=sharing" target="_blank" >Как отделить статические отражения от динамических целей</a>
- <a href="https://docs.google.com/document/d/1tlU3pEldtRoaOue1CEXEpLfUNiG0ubDxb3B-OQVETpw/edit?usp=sharing" >SDR & IQ sample</a>


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

```javascript
      ┌───────────────┐
      │  IQ Capture   │  (KrakenSDR: reference + surveillance)
      └──────┬────────┘
             │
             ▼
      ┌───────────────┐
      │      CAF      │  (Delay × Doppler)
      └──────┬────────┘
             │
             ▼
      ┌───────────────┐
      │  MTI / CFAR   │  (фильтрация + детектор)
      └──────┬────────┘
             │
             ▼
      ┌───────────────┐
      │ Clustering    │  (DBSCAN/HDBSCAN)
      └──────┬────────┘
             │
             ▼
      ┌───────────────┐
      │   Tracking    │  (Kalman + ID assignment)
      └──────┬────────┘
             │
             ▼
      ┌───────────────┐
      │  Output JSON  │ → WebSocket → Browser Map (Leaflet)
      └───────────────┘
```
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
