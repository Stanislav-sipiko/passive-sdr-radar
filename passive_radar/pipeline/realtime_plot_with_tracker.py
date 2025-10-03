#!/usr/bin/env python3
"""
realtime_plot_with_tracker.py

Realtime CAF visualization + CFAR + multi-target tracking (Kalman + Hungarian).

Requirements:
- matplotlib
- numpy
- passive_radar.capture.kraken_reader.KrakenUDPReader
- passive_radar.caf.caf.CAFProcessor
- passive_radar.detect.cfar.cfar_2d / or CFARProcessor wrapper
- passive_radar.track.tracker.Tracker  (the Kalman+Hungarian tracker implemented earlier)

Run:
    python passive_radar/pipeline/realtime_plot_with_tracker.py

    Реализует потоковую визуализацию 2D-трекер (Калман + Hungarian), чтобы на живой CAF-карте цели получали постоянные ID и следы (трэки). 
    Код строит тепловую карту, 
    наносит CFAR-детекции (красные крестики), а сверху рисует треки разными цветами и подписывает ID
    Мы используем твой существующий Tracker (Калман + Hungarian). Tracker.update(detections, timestamp) должен возвращать список объектов Track с полем state = [r, d, vr, vd] и id.

Отображаются:

тепловая карта CAF (из rdmap),

красные крестики CFAR-детекций,

цветные точки/треки и ID для каждого активного трека.

В демо-пайплайне CAF строится из одного чанка (как compute_caf_block(iq, iq)), а доплер-ось временно симулируется (в реальной системе CAF → RD требует накопления нескольких блоков и FFT по времени). После интеграции с реальным CAFProcessor замените _process_iq_to_caf на вызовы, которые накапливают несколько блоков и вычисляют настоящую RD-карту.

Параметры, которые можно подстроить: cfar_guard, cfar_ref, pfa, track_dt, dist_threshold в трекере.

Если DAQ присылает многоканальный поток (interleaved samples для каналов), нужно распарсить пакет и разделить на каналы перед CAF.
    
"""

import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import matplotlib.cm as cm
import time
from collections import defaultdict, deque

from passive_radar.capture.kraken_reader import KrakenUDPReader
from passive_radar.caf.caf import CAFProcessor
from passive_radar.detect.cfar import cfar_2d, extract_detections
from passive_radar.track.tracker import Tracker  # assumes Tracker is defined as before

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RealtimeRadarPlotWithTracker:
    def __init__(
        self,
        udp_ip="0.0.0.0",
        udp_port=5000,
        sample_rate=2_000_000,
        chunk_samples=4096,
        doppler_bins=128,
        delay_bins=256,
        cfar_guard=(2, 2),
        cfar_ref=(8, 8),
        pfa=1e-3,
        track_dt=1.0,
    ):
        # Reader
        self.reader = KrakenUDPReader(
            ip=udp_ip,
            port=udp_port,
            dtype=np.complex64,
            chunk_samples=chunk_samples,
        )

        # CAF processor
        self.caf = CAFProcessor(sample_rate=sample_rate, block_size=chunk_samples)

        # CFAR params (we will call simple 2D CFAR from detect.cfar)
        self.cfar_guard = cfar_guard
        self.cfar_ref = cfar_ref
        self.pfa = pfa

        # Tracker
        self.tracker = Tracker(dt=track_dt, dist_threshold=12.0, max_missed=5)

        # CAF map size (we'll compute doppler from multiple blocks; for simplicity we derive delay=bins=block_size)
        self.delay_bins = delay_bins
        self.doppler_bins = doppler_bins

        # Initialize CAF map (doppler x delay)
        self.caf_map = np.zeros((self.doppler_bins, self.delay_bins))

        # Tracking history: store last N positions per track id for plotting trails
        self.trail_len = 20
        self.trails = defaultdict(lambda: deque(maxlen=self.trail_len))

        # Color map for tracks
        self.colors = {}
        self.colormap = cm.get_cmap("tab20")

        # Matplotlib setup
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.img = self.ax.imshow(
            20 * np.log10(self.caf_map + 1e-12),
            aspect="auto",
            origin="lower",
            cmap="viridis",
            interpolation="nearest",
        )
        self.ax.set_title("Realtime Passive Radar (CAF + CFAR + Tracker)")
        self.ax.set_xlabel("Delay bins")
        self.ax.set_ylabel("Doppler bins")

        # Detections scatter
        self.scatter = self.ax.scatter([], [], marker="x", color="red", s=40, label="CFAR")

        # Track artists (will be a dict of Line2D objects and text labels)
        self.track_lines = {}
        self.track_dots = {}
        self.track_texts = {}

        # Legend
        self.ax.legend(loc="upper right")

    def _assign_color(self, tid):
        """Assign consistent color per track id."""
        if tid not in self.colors:
            idx = (tid - 1) % 20
            self.colors[tid] = self.colormap(idx)
        return self.colors[tid]

    def _process_iq_to_caf(self, iq_chunk):
        """
        Convert single IQ chunk(s) to a CAF map.
        For demo we compute CAF block and then a very small doppler stacking to form a 2D map,
        because full RD mapping often requires a stream of blocks.
        """

        # If iq_chunk is complex array 1D, compute a CAF block and replicate (quick demo)
        # compute_caf_block returns 1D array (delay dimension)
        caf_block = self.caf.compute_caf_block(iq_chunk, iq_chunk)  # self-correlation as placeholder
        # take magnitude and resize to desired delay_bins
        delay = np.abs(caf_block)
        # reduce/extend delay to desired delay_bins
        if delay.size >= self.delay_bins:
            delay = delay[: self.delay_bins]
        else:
            pad = np.zeros(self.delay_bins - delay.size)
            delay = np.concatenate([delay, pad])

        # Create a doppler axis by short-time FFT along a tiny buffer.
        # For realtime demo, we just tile the delay vector across doppler_bins and add slight random phase to simulate doppler variation.
        rd = np.tile(delay, (self.doppler_bins, 1))
        # add tiny doppler-like variation for visual interest (remove in real implementation)
        noise = np.random.randn(*rd.shape) * 0.01 * np.max(rd + 1e-12)
        rd = rd + noise
        return rd

    def _run_cfar_on_rd(self, rdmap):
        """
        Run CFAR on RD map and return list of detections (doppler_idx, delay_idx, power).
        We'll use a simple approach: run cfar_2d row-wise or use provided 2D CFAR.
        """
        # reuse the cfar_2d function expecting rdmap shape (doppler, delay)
        det_map, thr_map = cfar_2d(rdmap, guard_cells=self.cfar_guard, ref_cells=self.cfar_ref, pfa=self.pfa)
        dets = extract_detections(det_map, rdmap, threshold=0)
        # dets is list of (doppler, range, power)
        return dets

    def update_frame(self, frame):
        """
        Called by matplotlib animation. Reads one IQ chunk, updates CAF, CFAR, tracker and plot.
        """
        try:
            iq = next(self.reader.stream())
        except Exception as e:
            logger.exception("Error receiving IQ chunk: %s", e)
            return self.img,

        # For multi-channel DAQ, reshape appropriately. We assume single-channel complex array here.
        # Compute a quick RD map from the chunk:
        rdmap = self._process_iq_to_caf(iq)

        # Save the CAF map for visualization
        # Optionally apply normalization / smoothing
        vis_map = 20 * np.log10(np.abs(rdmap) + 1e-12)
        self.img.set_data(vis_map)
        self.img.set_clim(np.percentile(vis_map, 5), np.percentile(vis_map, 99))

        # CFAR detections
        dets = self._run_cfar_on_rd(rdmap)  # list of tuples (doppler, delay, power)

        # Prepare detections for tracker: convert to (range_idx, doppler_idx, power)
        detections_for_tracker = []
        for dop, rng, power in dets:
            # convert indices: tracker expects (r_idx, d_idx, power)
            # here r_idx = rng (delay index), d_idx = dop (doppler index)
            detections_for_tracker.append((float(rng), float(dop), float(power)))

        # Update tracker with detections
        tracks = self.tracker.update(detections_for_tracker, timestamp=time.time())

        # Update trails and graphics
        # First: plot CFAR detections
        if dets:
            xs = [d[1] for d in dets]  # delay
            ys = [d[0] for d in dets]  # doppler
            self.scatter.set_offsets(np.c_[xs, ys])
        else:
            self.scatter.set_offsets([])

        # Update / create track artists
        current_ids = set()
        for tr in tracks:
            tid = tr.id
            current_ids.add(tid)
            # current estimated position from state: [r, d, vr, vd]
            x = float(tr.state[0])  # range/delay index
            y = float(tr.state[1])  # doppler index

            # update trail
            self.trails[tid].append((x, y))

            # line for trail
            xs_trail = [p[0] for p in self.trails[tid]]
            ys_trail = [p[1] for p in self.trails[tid]]

            color = self._assign_color(tid)

            # create line artist if missing
            if tid not in self.track_lines:
                (line,) = self.ax.plot(xs_trail, ys_trail, "-", color=color, linewidth=2, label=f"Track {tid}")
                dot = self.ax.plot(x, y, "o", color=color, markersize=6)[0]
                txt = self.ax.text(x + 1, y + 1, f"{tid}", color=color, fontsize=9)
                self.track_lines[tid] = line
                self.track_dots[tid] = dot
                self.track_texts[tid] = txt
            else:
                self.track_lines[tid].set_data(xs_trail, ys_trail)
                self.track_dots[tid].set_data([x], [y])
                self.track_texts[tid].set_position((x + 1, y + 1))
                self.track_texts[tid].set_text(str(tid))

        # Remove artists for deleted tracks
        for tid in list(self.track_lines.keys()):
            if tid not in current_ids:
                # track was removed — delete artists
                ln = self.track_lines.pop(tid)
                dn = self.track_dots.pop(tid)
                tx = self.track_texts.pop(tid)

                try:
                    ln.remove()
                    dn.remove()
                    tx.remove()
                except Exception:
                    pass
                # also clear trail
                if tid in self.trails:
                    del self.trails[tid]

        # redraw legend to include tracks (only once)
        # (avoid creating huge legends each frame)
        self.ax.relim()
        self.ax.autoscale_view()

        logger.info(f"Frame updated. Detections: {len(detections_for_tracker)}, Tracks: {len(tracks)}")
        return (self.img, self.scatter) + tuple(self.track_lines.values())

    def run(self):
        """Start the reader and run the matplotlib animation loop."""
        self.reader.start()
        ani = animation.FuncAnimation(self.fig, self.update_frame, interval=200, blit=False)
        plt.show()
        self.reader.stop()


if __name__ == "__main__":
    radar = RealtimeRadarPlotWithTracker(
        udp_ip="0.0.0.0",
        udp_port=5000,
        sample_rate=2_000_000,
        chunk_samples=4096,
        doppler_bins=128,
        delay_bins=256,
        cfar_guard=(2, 2),
        cfar_ref=(8, 8),
        pfa=1e-3,
        track_dt=1.0,
    )
    radar.run()
