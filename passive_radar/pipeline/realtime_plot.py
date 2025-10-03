"""
Запуск

На Raspberry Pi (DAQ → UDP):

./krakensdr_daq --freq 650000000 --rate 2000000 --gain 30 --udp 192.168.1.100:5000


На твоём ПК:

python passive_radar/pipeline/realtime_plot.py


Увидишь живую тепловую карту CAF:

Цвет = уровень сигнала

Красные крестики = цели (CFAR)
"""
import logging
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

from passive_radar.capture.kraken_reader import KrakenUDPReader
from passive_radar.processing.caf import CAFProcessor
from passive_radar.processing.cfar import CFARProcessor


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class RealtimeRadarPlot:
    def __init__(
        self,
        udp_ip="0.0.0.0",
        udp_port=5000,
        sample_rate=2_000_000,
        chunk_samples=4096,
        doppler_bins=128,
        delay_bins=256,
        cfar_threshold=20.0,
    ):
        self.reader = KrakenUDPReader(
            ip=udp_ip,
            port=udp_port,
            dtype=np.complex64,
            chunk_samples=chunk_samples,
        )

        self.caf = CAFProcessor(
            sample_rate=sample_rate,
            n_doppler=doppler_bins,
            n_delay=delay_bins,
        )

        self.cfar = CFARProcessor(
            threshold=cfar_threshold,
            guard_cells=2,
            training_cells=8,
        )

        # Матрица CAF
        self.caf_map = np.zeros((doppler_bins, delay_bins))

        # Настраиваем фигуру
        self.fig, self.ax = plt.subplots(figsize=(8, 6))
        self.img = self.ax.imshow(
            20 * np.log10(np.abs(self.caf_map) + 1e-12),
            aspect="auto",
            origin="lower",
            cmap="viridis",
            interpolation="nearest",
        )
        self.ax.set_title("Realtime Passive Radar (CAF + CFAR)")
        self.ax.set_xlabel("Delay bins")
        self.ax.set_ylabel("Doppler bins")

        self.scatter = self.ax.scatter([], [], marker="x", color="red")

    def update_frame(self, frame):
        iq = next(self.reader.stream())

        # Разбиваем на ref и echo (если 2 канала)
        if iq.ndim == 1:
            ref = iq
            echo = iq
        else:
            ref = iq[:, 0]
            echo = iq[:, 1]

        # CAF
        self.caf_map = self.caf.compute(ref, echo)

        # CFAR
        detections = self.cfar.detect(self.caf_map)

        # Обновляем картинку
        self.img.set_data(20 * np.log10(np.abs(self.caf_map) + 1e-12))

        if detections:
            xs = [d[1] for d in detections]  # delay
            ys = [d[0] for d in detections]  # doppler
            self.scatter.set_offsets(np.c_[xs, ys])
        else:
            self.scatter.set_offsets([])

        logger.info(f"Frame: detections={len(detections)}")
        return self.img, self.scatter

    def run(self):
        self.reader.start()
        ani = animation.FuncAnimation(
            self.fig,
            self.update_frame,
            interval=200,  # мс между апдейтами
            blit=False,
        )
        plt.show()
        self.reader.stop()


if __name__ == "__main__":
    radar = RealtimeRadarPlot(
        udp_ip="0.0.0.0",
        udp_port=5000,
        sample_rate=2_000_000,
        chunk_samples=4096,
        doppler_bins=128,
        delay_bins=256,
        cfar_threshold=20.0,
    )
    radar.run()
