"""
Fusion server: receives detections from multiple KrakenSDR units,
performs data association and multilateration (optionally weighted by SNR),
and broadcasts fused tracks via WebSocket.
"""

import asyncio
import json
import numpy as np
from aiohttp import web

from .fusion_utils import fuse_tracks_lsq


class FusionServer:
    def __init__(self, host="0.0.0.0", port=8080):
        self.host = host
        self.port = port
        self.received_data = []

    async def handle_post(self, request):
        """Receive detections via POST."""
        data = await request.json()
        self.received_data.append(data)
        return web.Response(text="OK")

    async def handle_get(self, request):
        """Return fused targets."""
        fused = fuse_tracks_lsq(self.received_data)
        return web.json_response(fused)

    def run(self):
        app = web.Application()
        app.router.add_post('/data', self.handle_post)
        app.router.add_get('/tracks', self.handle_get)
        web.run_app(app, host=self.host, port=self.port)


if __name__ == "__main__":
    FusionServer().run()
