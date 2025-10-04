# Passive Radar Network Module

This directory contains the networking and fusion components for the distributed passive radar system.

## Structure

- **`fusion.py`** — combines tracks and detections from multiple radar units using SNR-weighted averaging.
- **`server.py`** — WebSocket server that receives detections and publishes fused tracks.
- **`network_config.json`** — configuration for network parameters and participating clients.
- **`passive_radar_server.service`** — systemd unit for running the fusion server on Raspberry Pi or central server.

## Usage

```bash
python3 -m passive_radar.network.server
```

Or enable systemd unit:

```bash
sudo cp passive_radar/network/passive_radar_server.service /etc/systemd/system/
sudo systemctl enable --now passive_radar_server.service
```

## Fusion logic

Each detection contains:
```json
{ "id": 1, "pos": [x, y], "snr": 23.5 }
```
The server fuses detections by averaging positions and weighting them by SNR.
