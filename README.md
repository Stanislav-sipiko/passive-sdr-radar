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
