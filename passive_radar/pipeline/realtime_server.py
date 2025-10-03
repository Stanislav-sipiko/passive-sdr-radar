#!/usr/bin/env python3
"""
realtime_server.py

Headless realtime pipeline:
- Читает IQ с KrakenSDR через UDP
- Считает CAF (Range-Doppler карту)
- CFAR → детекции
- Трекинг (Kalman + Hungarian)
- Отправляет события в WebSocket клиентам

Запуск:
    python passive_radar/pipeline/realtime_server.py --udp_port 5000 --ws_port 8765

    Как запускать на Raspberry Pi

Установить зависимости:

sudo apt update
sudo apt install python3-pip -y
pip3 install numpy websockets matplotlib


Запустить наш сервер:

python3 passive_radar/pipeline/realtime_server.py --udp_port 5000 --ws_port 8765


На другом компьютере (или на Pi же) подключиться к WebSocket:

const ws = new WebSocket("ws://raspberrypi.local:8765");
ws.onmessage = (msg) => {
    const data = JSON.parse(msg.data);
    console.log("Tracks:", data.tracks);
};


👉 Теперь у нас два режима:

GUI (realtime_plot_with_tracker.py) для отладки на ноуте.

Headless (realtime_server.py) для Raspberry Pi + WebSocket-выдачи.
"""

import asyncio
import json
import time
import logging
import numpy as np
import argparse

import websockets

from passive_radar.capture.kraken_reader import KrakenUDPReader
from passive_radar.caf.caf import CAFProcessor
from passive_radar.detect.cfar import cfar_2d, extract_detections
from passive_radar.track.tracker import Tracker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RealtimeServer")


class RealtimeRadarServer:
    def __init__(
        self,
        udp_ip="0.0.0.0",
        udp_port=5000,
        ws_port=8765,
        sample_rate=2_000_000,
        chunk_samples=4096,
        doppler_bins=128,
        delay_bins=256,
        cfar_guard=(2, 2),
        cfar_ref=(8, 8),
        pfa=1e-3,
        track_dt=1.0,
    ):
        # UDP reader
        self.reader = KrakenUDPReader(
            ip=udp_ip,
            port=udp_port,
            dtype=np.complex64,
            chunk_samples=chunk_samples,
        )

        # CAF
        self.caf = CAFProcessor(sample_rate=sample_rate, block_size=chunk_samples)

        # CFAR params
        self.cfar_guard = cfar_guard
        self.cfar_ref = cfar_ref
        self.pfa = pfa

        # Tracker
        self.tracker = Tracker(dt=track_dt, dist_threshold=12.0, max_missed=5)

        # Buffers
        self.doppler_bins = doppler_bins
        self.delay_bins = delay_bins

        # WebSocket
        self.ws_port = ws_port
        self.clients = set()

    def _process_chunk(self, iq):
        """Compute CAF → RD map → CFAR → tracker"""
        caf_block = self.caf.compute_caf_block(iq, iq)
        delay = np.abs(caf_block)
        if delay.size >= self.delay_bins:
            delay = delay[: self.delay_bins]
        else:
            pad = np.zeros(self.delay_bins - delay.size)
            delay = np.concatenate([delay, pad])

        rd = np.tile(delay, (self.doppler_bins, 1))
        rd += np.random.randn(*rd.shape) * 0.01 * np.max(rd + 1e-12)

        det_map, thr_map = cfar_2d(
            rd, guard_cells=self.cfar_guard, ref_cells=self.cfar_ref, pfa=self.pfa
        )
        dets = extract_detections(det_map, rd, threshold=0)

        detections_for_tracker = [(float(r), float(d), float(p)) for d, r, p in dets]
        tracks = self.tracker.update(detections_for_tracker, timestamp=time.time())

        return dets, tracks

    async def _ws_handler(self, websocket, path):
        self.clients.add(websocket)
        try:
            async for _ in websocket:
                pass  # server only sends
        finally:
            self.clients.remove(websocket)

    async def _broadcast(self, message: dict):
        if self.clients:
            msg = json.dumps(message)
            await asyncio.gather(*[ws.send(msg) for ws in self.clients])

    async def run(self):
        logger.info(f"Starting UDP reader on {self.reader.ip}:{self.reader.port}")
        self.reader.start()

        logger.info(f"Starting WebSocket server on port {self.ws_port}")
        ws_server = await websockets.serve(self._ws_handler, "0.0.0.0", self.ws_port)

        try:
            while True:
                iq = next(self.reader.stream())
                dets, tracks = self._process_chunk(iq)

                # Формируем JSON
                payload = {
                    "timestamp": time.time(),
                    "detections": [
                        {"doppler": float(d), "range": float(r), "power": float(p)}
                        for d, r, p in dets
                    ],
                    "tracks": [
                        {
                            "id": tr.id,
                            "range": float(tr.state[0]),
                            "doppler": float(tr.state[1]),
                            "vr": float(tr.state[2]),
                            "vd": float(tr.state[3]),
                        }
                        for tr in tracks
                    ],
                }

                await self._broadcast(payload)
        except KeyboardInterrupt:
            logger.info("Shutting down server...")
        finally:
            self.reader.stop()
            ws_server.close()
            await ws_server.wait_closed()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--udp_ip", default="0.0.0.0")
    parser.add_argument("--udp_port", type=int, default=5000)
    parser.add_argument("--ws_port", type=int, default=8765)
    args = parser.parse_args()

    srv = RealtimeRadarServer(
        udp_ip=args.udp_ip,
        udp_port=args.udp_port,
        ws_port=args.ws_port,
    )

    asyncio.run(srv.run())
