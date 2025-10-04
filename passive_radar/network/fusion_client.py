"""
Client that sends local detections to the fusion server and receives fused targets.
"""

import requests
import time


class FusionClient:
    def __init__(self, server_url="http://localhost:8080"):
        self.server_url = server_url

    def send_tracks(self, tracks):
        payload = {"tracks": tracks}
        try:
            r = requests.post(f"{self.server_url}/data", json=payload, timeout=2)
            return r.status_code == 200
        except requests.RequestException:
            return False

    def get_fused(self):
        try:
            r = requests.get(f"{self.server_url}/tracks", timeout=2)
            return r.json()
        except requests.RequestException:
            return []


if __name__ == "__main__":
    client = FusionClient()
    while True:
        client.send_tracks([{"id": "local_1", "position": [1, 2, 3], "snr": 10.0}])
        print(client.get_fused())
        time.sleep(2)
