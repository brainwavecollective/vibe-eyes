import time
import numpy as np
from typing import List


class VIBEBlender:
    """
    Attack–Hold–Decay VIBE system.

    - Bursts are shown at full strength
    - Held for a short time
    - Then decay back toward baseline
    - Each burst slightly nudges the baseline
    """

    DEFAULT_INFLUENCE = 0.22      # how much a normal sentence nudges baseline
    BASELINE_INFLUENCE = 0.70     # how much Ollama nudges baseline
    HOLD_SECONDS = 0.8
    DECAY_RATE = 0.06             # per tick at 10 Hz
    DWELL_SECONDS = 1.2


    def __init__(self):
        self.baseline = np.array([0.5, 0.5, 0.5, 0.5, 0.8])
        self.current = self.baseline.copy()
        self.hold_until = 0.0
        self.last_baseline_update = time.time()
        self.dwell_until = 0.0

    # ---- Burst application ----
    def apply_burst(self, burst: List[float], influence: float = None):
        burst_array = np.array(burst)

        # Show full emotion immediately
        self.current = burst_array.copy()

        # Hold peak for perceptual clarity
        now = time.time()
        self.dwell_until = now + self.DWELL_SECONDS
        self.hold_until = self.dwell_until + self.HOLD_SECONDS

        # Nudge baseline toward what we just showed
        alpha = influence if influence is not None else self.DEFAULT_INFLUENCE
        self.baseline += (self.current - self.baseline) * alpha
        self.baseline = np.clip(self.baseline, 0, 1)

    # ---- Baseline correction from Ollama ----
    def apply_baseline(self, new_baseline: List[float]):
        # Treat as a very strong burst
        self.apply_burst(new_baseline, influence=self.BASELINE_INFLUENCE)
        self.last_baseline_update = time.time()

    # ---- Called at ~10 Hz from server ----
    def tick(self) -> List[float]:
        now = time.time()

        # Dwell + Hold (plateau)
        if now < self.hold_until:
            return self.current.tolist()

        # Decay phase
        self.current += (self.baseline - self.current) * self.DECAY_RATE
        return self.current.tolist()

    # ---- Debugging ----
    def get_state(self):
        return {
            "baseline": self.baseline.tolist(),
            "current": self.current.tolist(),
            "hold_remaining": max(0.0, self.hold_until - time.time()),
            "time_since_baseline_update": time.time() - self.last_baseline_update,
        }

