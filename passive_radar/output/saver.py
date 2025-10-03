# passive_radar/output/saver.py
"""
Saver module: responsible for saving radar events, patches, and maintaining a manifest file.

Functions:
- save_event: save single detection/track event (metadata) to JSON + append to manifest
- save_patch: save 2D/3D CAF/MTI patches around detection for later ML training
- manifest: handles updating/reading manifest.json (index of saved data)

Data is organized under an output_dir with subfolders:
  events/    -> JSON metadata files
  patches/   -> npy/png arrays
  manifest.json -> global index
  Как использовать:
  from passive_radar.output import saver
import numpy as np

# Сохраняем событие
eid = saver.save_event("results", {
    "range": 200,
    "doppler": 15,
    "snr": 9.1,
    "track_id": 3
})

# Сохраняем патч вокруг детекции
patch = np.random.randn(64, 64)
saver.save_patch("results", eid, patch, fmt="npy")

После этого в results/ будет структура:

results/
  events/
    <uuid>.json
  patches/
    <uuid>.npy
  manifest.json
"""

import os
import json
import uuid
import datetime
import numpy as np
from typing import Dict, Any, Optional
from pathlib import Path
from matplotlib import pyplot as plt


def _ensure_dirs(base_dir: str):
    """Create required subfolders if missing."""
    Path(base_dir, "events").mkdir(parents=True, exist_ok=True)
    Path(base_dir, "patches").mkdir(parents=True, exist_ok=True)


def _manifest_path(base_dir: str) -> Path:
    return Path(base_dir) / "manifest.json"


def load_manifest(base_dir: str) -> Dict[str, Any]:
    """Load manifest.json if exists, else return empty dict."""
    path = _manifest_path(base_dir)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        return {"events": []}


def save_manifest(base_dir: str, manifest: Dict[str, Any]):
    """Write manifest.json to disk."""
    path = _manifest_path(base_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def save_event(base_dir: str,
               event: Dict[str, Any],
               event_id: Optional[str] = None) -> str:
    """
    Save event metadata (JSON) and update manifest.
    :param base_dir: root output dir
    :param event: dict with event info, e.g. {range, doppler, snr, track_id, timestamp}
    :param event_id: optional preassigned ID, else UUID4
    :return: event_id used
    """
    _ensure_dirs(base_dir)
    manifest = load_manifest(base_dir)

    if event_id is None:
        event_id = str(uuid.uuid4())

    # add timestamp if missing
    if "timestamp" not in event:
        event["timestamp"] = datetime.datetime.utcnow().isoformat()

    # save JSON
    event_path = Path(base_dir, "events", f"{event_id}.json")
    with open(event_path, "w", encoding="utf-8") as f:
        json.dump(event, f, indent=2, ensure_ascii=False)

    # update manifest
    manifest["events"].append({
        "id": event_id,
        "file": str(event_path.relative_to(base_dir)),
        "timestamp": event["timestamp"],
        "range": event.get("range"),
        "doppler": event.get("doppler"),
        "track_id": event.get("track_id"),
    })
    save_manifest(base_dir, manifest)

    return event_id


def save_patch(base_dir: str,
               event_id: str,
               patch: np.ndarray,
               fmt: str = "npy",
               cmap: str = "viridis") -> str:
    """
    Save CAF/MTI patch around detection.
    :param base_dir: root output dir
    :param event_id: link to saved event
    :param patch: ndarray [h,w] or [t,h,w]
    :param fmt: "npy" or "png"
    :param cmap: colormap if saving png
    :return: filename of saved patch
    """
    _ensure_dirs(base_dir)
    patch_dir = Path(base_dir, "patches")
    fname = f"{event_id}.{fmt}"
    out_path = patch_dir / fname

    if fmt == "npy":
        np.save(out_path, patch)
    elif fmt == "png":
        if patch.ndim == 3:
            # if sequence, plot first frame
            img = patch[0]
        else:
            img = patch
        plt.imsave(out_path, img, cmap=cmap)
    else:
        raise ValueError(f"Unsupported patch format {fmt}")

    # update manifest entry
    manifest = load_manifest(base_dir)
    for ev in manifest["events"]:
        if ev["id"] == event_id:
            ev["patch"] = str(out_path.relative_to(base_dir))
            break
    save_manifest(base_dir, manifest)

    return str(out_path)


# Demo usage
if __name__ == "__main__":
    base = "output_demo"
    dummy_event = {
        "range": 123,
        "doppler": -5,
        "snr": 12.3,
        "track_id": 1
    }
    eid = save_event(base, dummy_event)
    print("Saved event:", eid)

    patch = np.random.randn(64, 64)
    pfile = save_patch(base, eid, patch, fmt="png")
    print("Saved patch:", pfile)
