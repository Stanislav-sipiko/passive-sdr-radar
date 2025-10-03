"""
Как запускать

Поднять DAQ (на Raspberry Pi):

./krakensdr_daq --freq 650000000 --rate 2000000 --gain 30 --udp 192.168.1.100:5000


(настраиваешь частоту и параметры под сигнал, например DVB-T).

На ноутбуке (или том же Pi):

python passive_radar/pipeline/realtime_pipeline.py


В логе ты увидишь:

Iter 0: CAF shape=(128, 256), detections=0
Iter 1: CAF shape=(128, 256), detections=1
 → Target: Doppler=5, Delay=42, Power=27.4
 """
import logging
import numpy as np

from passive_radar.capture.kraken_reader import KrakenUDPReader
from passive_radar.processing.caf import CAFProcessor
from passive_radar.processing.cfar import CFARProcessor


logger = logging.getLogger(__name__)


class RealtimeRadarPipeline:
    """
    Потоковый пассивный радар:
    - Читает IQ по UDP
    - Строит CAF (Cross Ambiguity Function)
    - Применяет CFAR для обнаружения целей
    """

    def __init__(
        self,
        ref_channel=0,
        echo_channel=1,
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

        self.ref_channel = ref_channel
        self.echo_channel = echo_channel
        self.sample_rate = sample_rate
        self.chunk_samples = chunk_samples

    def run(self, max_iters=None):
        """
        Запускает обработку в реальном времени
        :param max_iters: ограничить количество шагов (None = бесконечно)
        """
        logger.info("Starting realtime passive radar pipeline...")
        self.reader.start()

        try:
            for i, iq in enumerate(self.reader.stream()):
                # IQ: [N] или [N,channels] в зависимости от формата DAQ
                # Если DAQ передает каналы подряд — тут потребуется reshape
                # Для простоты считаем, что у нас 2 канала: ref и echo
                if iq.ndim == 1:
                    # сделаем "фейковые" два канала (для отладки)
                    ref = iq
                    echo = iq
                else:
                    ref = iq[:, self.ref_channel]
                    echo = iq[:, self.echo_channel]

                # CAF
                caf_map = self.caf.compute(ref, echo)

                # CFAR
                detections = self.cfar.detect(caf_map)

                # Вывод
                logger.info(f"Iter {i}: CAF shape={caf_map.shape}, detections={len(detections)}")
                if detections:
                    for (dop, delay, power) in detections:
                        logger.info(f" → Target: Doppler={dop}, Delay={delay}, Power={power:.2f}")

                if max_iters and i >= max_iters:
                    break

        finally:
            self.reader.stop()
            logger.info("Pipeline stopped")
