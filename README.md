<a href="https://totoha.com/passive_radar/index.html" target="_blank" >Как отделить статические отражения от динамических целей</a>
# passive-sdr-radar
Passive radar with KrakenSDR (IQ → CAF → MTI/CFAR → tracking)
=======
=======
>>>>>>> bf7b23f82263bf5ca98a78a52b90faf0d7728278
# Passive SDR Radar Project

Passive radar implementation using **KrakenSDR**.  
Pipeline: **IQ → CAF → MTI/CFAR → Clustering → Tracking**.

---

## 🚀 Overview
Passive radar works by using existing broadcast signals (like DVB-T) as illumination sources.  
We receive two streams:
- **Reference channel** – direct DVB-T signal from transmitter
- **Surveillance channel** – reflections from objects (planes, drones, rockets)

By computing the **Cross Ambiguity Function (CAF)** we detect moving objects, filter out static reflections, and track dynamic targets.

---

## 🛠️ Project Structure
<<<<<<< HEAD
>>>>>>> bf7b23f (Initial commit: base project structure)
=======
>>>>>>> bf7b23f82263bf5ca98a78a52b90faf0d7728278
