# Архитектура и блок-схема

## Краткое описание
Пайплайн:
1. **IQ capture** (KrakenSDR) — reference + surveillance
2. **CAF** — delay × doppler карты
3. **MTI / FIR** — подавление стационарных отражений
4. **CFAR** — адаптивная детекция
5. **Morphology / Clustering** — объединение пятен
6. **Tracker** (Kalman + assignment) — присвоение ID и история
7. **Output** — JSON/patches + WebSocket → фронтенд карта

## Блок-схема
