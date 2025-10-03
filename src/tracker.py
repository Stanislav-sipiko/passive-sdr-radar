# passive_radar/track/tracker.py
"""
Simple multi-target tracker: Kalman filter (constant velocity) + Hungarian assignment.

Assumptions:
- Measurements are 2D positions in index space: (range_idx, doppler_idx)
- Simple linear model: state = [r, d, vr, vd] (positions + velocities in indices)
- Measurement model: z = H x = [r, d]
- Uses scipy.optimize.linear_sum_assignment for global assignment

Functions / Classes:
- Track: represents a single track (state, covariance, id, history, missed_count)
- Tracker: manages multiple Track objects (predict, associate, update, prune)

Пояснения / думы по интеграции
detections — ожидается список кортежей (range_idx, doppler_idx, power) из cfar.extract_detections. Преобразуй индексы в нужную систему (если используешь физические метрики — масштабируй).
Порог dist_threshold задаёт макс допустимый индекс-расстояние между предсказанием и детекцией; подбирается эмпирически.
Для реального времени:
вызывай predict_all(dt) с реальным dt между кадрами (в секундах),
перед вызовом update передавай реальные detections в этом кадре.
Для более сложных сценариев можно:
использовать Mahalanobis distance вместо Евклидова (учитывать ковариацию S),
интегрировать вероятность детекции / false alarm модель,
заменить Kalman на EKF/UKF если модель не линейна.
"""

from dataclasses import dataclass, field
import numpy as np
from scipy.optimize import linear_sum_assignment
import itertools
import time
from typing import List, Tuple, Optional


@dataclass
class Track:
    id: int
    state: np.ndarray          # shape (4,) -> [r, d, vr, vd]
    P: np.ndarray              # covariance matrix (4x4)
    last_update: float         # timestamp of last update
    history: List[Tuple[float, float, float]] = field(default_factory=list)
    missed: int = 0            # consecutive missed detections

    def predict(self, dt: float, F: np.ndarray, Q: np.ndarray):
        """Predict state forward by dt using given F and Q (in-place)."""
        # For constant-velocity model F is usually constant for given dt.
        self.state = F @ self.state
        self.P = F @ self.P @ F.T + Q
        self.missed += 1  # will be reset on update
        return self.state

    def update(self, meas: np.ndarray, H: np.ndarray, R: np.ndarray):
        """Kalman update with measurement meas (shape (2,))."""
        z = meas.reshape(2,)
        y = z - (H @ self.state)               # innovation
        S = H @ self.P @ H.T + R               # innovation covariance
        K = self.P @ H.T @ np.linalg.inv(S)    # Kalman gain
        self.state = self.state + K @ y
        I = np.eye(self.P.shape[0])
        self.P = (I - K @ H) @ self.P
        self.missed = 0
        self.last_update = time.time()
        # append to history: (timestamp, r, d)
        self.history.append((self.last_update, float(self.state[0]), float(self.state[1])))


class Tracker:
    def __init__(self,
                 dt: float = 1.0,
                 process_var: float = 1.0,
                 meas_var: float = 10.0,
                 dist_threshold: float = 10.0,
                 max_missed: int = 5):
        """
        :param dt: default time step between frames (s) — used to build F
        :param process_var: process noise variance (controls Q)
        :param meas_var: measurement noise variance (controls R)
        :param dist_threshold: gating threshold in index-space for assignment
        :param max_missed: max consecutive missed frames before deleting track
        """
        self.dt = dt
        self.process_var = process_var
        self.meas_var = meas_var
        self.dist_threshold = dist_threshold
        self.max_missed = max_missed

        self._next_id = 1
        self.tracks: dict[int, Track] = {}

        # measurement matrix H (2x4): map state -> measurement (r,d)
        self.H = np.array([[1, 0, 0, 0],
                           [0, 1, 0, 0]], dtype=float)

        # measurement noise
        self.R = np.eye(2) * meas_var

    def _build_F_Q(self, dt: float) -> Tuple[np.ndarray, np.ndarray]:
        """Build state transition F and process noise Q for given dt."""
        # constant velocity model: x = [r, d, vr, vd]
        F = np.array([[1, 0, dt, 0],
                      [0, 1, 0, dt],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]], dtype=float)
        # Simple Q: process_var on accel integrated -> approximate
        q = self.process_var
        Q = np.array([[dt**3/3, 0, dt**2/2, 0],
                      [0, dt**3/3, 0, dt**2/2],
                      [dt**2/2, 0, dt, 0],
                      [0, dt**2/2, 0, dt]], dtype=float) * q
        return F, Q

    def predict_all(self, dt: Optional[float] = None):
        """Predict all tracks forward by dt (if None use self.dt)."""
        if dt is None:
            dt = self.dt
        F, Q = self._build_F_Q(dt)
        for track in list(self.tracks.values()):
            track.predict(dt, F, Q)

    def _gate_cost_matrix(self, predictions: np.ndarray, detections: np.ndarray) -> np.ndarray:
        """
        Compute cost matrix (num_tracks x num_detections) = Euclidean distance in position space.
        predictions: (Ntracks, 2) predicted positions
        detections: (Ndets, 2)
        """
        if predictions.size == 0 or detections.size == 0:
            return np.zeros((predictions.shape[0], detections.shape[0]))

        # pairwise distances
        dists = np.linalg.norm(predictions[:, None, :] - detections[None, :, :], axis=2)
        return dists

    def update(self, detections: List[Tuple[int, int, float]], timestamp: Optional[float] = None):
        """
        Main update step: associate detections to tracks and update Kalman filters.
        :param detections: list of (r_idx, d_idx, power)
        :param timestamp: optional timestamp (float). If None, time.time() used.
        :return: list of active tracks after update
        """
        if timestamp is None:
            timestamp = time.time()

        # Step 1: Predict all tracks to current time (we assume fixed dt)
        self.predict_all(dt=self.dt)

        # Prepare arrays of predicted positions
        track_ids = list(self.tracks.keys())
        preds = []
        for tid in track_ids:
            st = self.tracks[tid].state
            preds.append([st[0], st[1]])
        preds = np.array(preds) if len(preds) > 0 else np.empty((0, 2))

        # Prepare detections array
        dets = np.array([[float(r), float(d)] for (r, d, p) in detections]) if len(detections) > 0 else np.empty((0, 2))

        # Step 2: Compute cost matrix and assignment
        if preds.shape[0] == 0:
            assigned_tracks = []
            assigned_dets = []
        else:
            cost = self._gate_cost_matrix(preds, dets)
            # apply gating: large cost -> set to large value
            gated_cost = cost.copy()
            gated_cost[gated_cost > self.dist_threshold] = 1e6

            # Hungarian assignment
            row_ind, col_ind = linear_sum_assignment(gated_cost)
            assigned_tracks = []
            assigned_dets = []
            for r, c in zip(row_ind, col_ind):
                if gated_cost[r, c] < 1e6:
                    assigned_tracks.append(track_ids[r])
                    assigned_dets.append(c)
                # else: assignment considered invalid (gated out)

        # Step 3: Update assigned tracks
        updated_track_ids = set()
        for track_id, det_idx in zip(assigned_tracks, assigned_dets):
            meas = dets[det_idx]
            track = self.tracks[track_id]
            track.update(meas, self.H, self.R)
            updated_track_ids.add(track_id)

        # Step 4: Create new tracks for unassigned detections
        assigned_det_set = set(assigned_dets)
        for idx, det in enumerate(detections):
            if idx not in assigned_det_set:
                r_idx, d_idx, power = det
                # initialize state with zero velocity and large covariance
                init_state = np.array([float(r_idx), float(d_idx), 0.0, 0.0], dtype=float)
                P0 = np.diag([50.0, 50.0, 25.0, 25.0])  # initial uncertainty
                tid = self._next_id
                self._next_id += 1
                track = Track(id=tid, state=init_state, P=P0, last_update=timestamp)
                track.history.append((timestamp, float(r_idx), float(d_idx)))
                self.tracks[tid] = track

        # Step 5: Increase missed counters for un-updated tracks already incremented in predict, prune if necessary
        to_delete = []
        for tid, track in list(self.tracks.items()):
            if tid not in updated_track_ids and len(track.history) == 0:
                # newly created without history? unlikely, skip
                pass
            if track.missed > self.max_missed:
                to_delete.append(tid)

        for tid in to_delete:
            del self.tracks[tid]

        # Return list of current tracks
        return list(self.tracks.values())


if __name__ == "__main__":
    # Demo: synthetic detections for two moving targets
    import matplotlib.pyplot as plt

    tr = Tracker(dt=1.0, dist_threshold=8.0, max_missed=3)

    # Generate synthetic detections per frame: two targets moving linearly, plus noise
    frames = 20
    detections_per_frame = []
    for t in range(frames):
        # target A: r=10+0.8*t, d=20+0.3*t
        a = (10 + 0.8 * t + np.random.randn()*0.4, 20 + 0.3 * t + np.random.randn()*0.4, 10.0)
        # target B: r=40-0.5*t, d=60-0.6*t
        b = (40 - 0.5 * t + np.random.randn()*0.6, 60 - 0.6 * t + np.random.randn()*0.6, 8.0)
        # plus occasional false alarms
        fas = []
        if np.random.rand() < 0.2:
            fas.append((np.random.uniform(0, 80), np.random.uniform(0, 80), 5.0))
        dets = [a, b] + fas
        detections_per_frame.append(dets)

    # Run tracker
    all_track_histories = {}
    for t, dets in enumerate(detections_per_frame):
        tracks = tr.update(dets, timestamp=time.time())
        for track in tracks:
            all_track_histories.setdefault(track.id, []).append((t, track.state.copy()))

    # Plot histories
    plt.figure(figsize=(8, 6))
    for tid, hist in all_track_histories.items():
        xs = [s[1][0] for s in hist]  # r
        ys = [s[1][1] for s in hist]  # d
        plt.plot(xs, ys, '-o', label=f'Track {tid}')
    plt.xlabel('Range index')
    plt.ylabel('Doppler index')
    plt.title('Tracked trajectories (demo)')
    plt.legend()
    plt.grid()
    plt.show()
