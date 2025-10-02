<a href="https://totoha.com/passive_radar/index.html" target="_blank" >Как отделить статические отражения от динамических целей</a>
# Passive SDR Radar Project

Passive radar implementation using KrakenSDR.  
Pipeline: IQ → CAF → MTI/CFAR → Clustering → Tracking.

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

## 📂 Структура проекта
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

🛰 Пример работы

Входные данные: IQ-файлы (reference + surveillance канал)
Выходные данные: карта детекций + треки целей (JSON, WebSocket)
{
  "id": 12,
  "range": 15.2,
  "doppler": -45.3,
  "velocity": 140,
  "timestamp": "2025-10-02T18:24:12Z"
}

📊 Визуализации

CAF карта (Delay × Doppler)
Детекции после CFAR
Треки целей на карте (Leaflet + WebSocket)

📌 TODO

 Подключение реальных данных с KrakenSDR
 Улучшение CFAR и фильтрации
 Трекинг с идентификацией целей

📜 Лицензия
GPL-3.0
