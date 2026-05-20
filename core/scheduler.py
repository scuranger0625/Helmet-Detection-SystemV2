from dataclasses import dataclass
from collections import deque
import numpy as np


@dataclass
class SystemState:
    # 畫面變化程度，來自 motion estimator
    motion_score: float

    # 分類器不確定性
    # 0.0 = 很確定
    # 1.0 = 很不確定
    classifier_entropy: float = 0.0

    # tracker 信心
    # 1.0 = 很穩
    # 0.0 = 很不穩
    tracker_confidence: float = 1.0

    # detector 預算壓力
    # 0.0 = 很空
    # 1.0 = 快爆了
    budget_pressure: float = 0.0


class BOSScheduler:

    def __init__(
        self,
        base_motion_threshold=0.03,
        history_size=20,
        urgency_threshold=0.40,
        force_refresh=5,
        burst_weight=1.5,
    ):

        self.base_motion_threshold = base_motion_threshold

        self.motion_history = deque(
            maxlen=history_size
        )

        self.urgency_threshold = urgency_threshold

        self.force_refresh = force_refresh

        self.burst_weight = burst_weight

        # ==========================================
        # scheduler 自己管理 cache age
        # main.py 不要再傳 cache_age 進來
        # ==========================================
        self.cache_age = 0

        # ==========================================
        # debug info
        # ==========================================
        self.last_urgency = 0.0

        self.last_dynamic_threshold = base_motion_threshold

    def reset(self):

        self.motion_history.clear()

        self.cache_age = 0

        self.last_urgency = 0.0

        self.last_dynamic_threshold = (
            self.base_motion_threshold
        )

    def update_motion_history(
        self,
        motion_score
    ):

        self.motion_history.append(
            float(motion_score)
        )

    def compute_dynamic_motion_threshold(self):

        if len(self.motion_history) < 3:

            self.last_dynamic_threshold = (
                self.base_motion_threshold
            )

            return self.base_motion_threshold

        avg_motion = float(
            np.mean(self.motion_history)
        )

        std_motion = float(
            np.std(self.motion_history)
        )

        dynamic_threshold = (
            avg_motion +
            self.burst_weight * std_motion
        )

        dynamic_threshold = max(
            dynamic_threshold,
            self.base_motion_threshold
        )

        self.last_dynamic_threshold = float(
            dynamic_threshold
        )

        return float(dynamic_threshold)

    def normalize_motion(
        self,
        motion_score
    ):

        dynamic_threshold = (
            self.compute_dynamic_motion_threshold()
        )

        normalized_motion = (
            float(motion_score) /
            max(dynamic_threshold, 1e-6)
        )

        normalized_motion = min(
            normalized_motion,
            2.0
        )

        return float(normalized_motion)

    def compute_urgency(
        self,
        state: SystemState
    ):

        # ==========================================
        # 1. motion urgency
        # ==========================================
        motion_term = self.normalize_motion(
            state.motion_score
        )

        # ==========================================
        # 2. cache age urgency
        # cache 越舊，越該 refresh
        # ==========================================
        cache_term = min(
            self.cache_age / max(self.force_refresh, 1),
            1.0
        )

        # ==========================================
        # 3. tracker risk
        # tracker_confidence 越低，risk 越高
        # ==========================================
        tracker_risk = 1.0 - float(
            np.clip(
                state.tracker_confidence,
                0.0,
                1.0
            )
        )

        # ==========================================
        # 4. classifier uncertainty
        # ==========================================
        entropy_term = float(
            np.clip(
                state.classifier_entropy,
                0.0,
                1.0
            )
        )

        # ==========================================
        # 5. budget pressure
        # 預算壓力越高，越不應該亂跑 YOLO
        # ==========================================
        budget_term = float(
            np.clip(
                state.budget_pressure,
                0.0,
                1.0
            )
        )

        # ==========================================
        # BOS-inspired urgency score
        # 目前可信訊號：
        # motion + cache_age
        # 其他訊號先保守使用
        # ==========================================
        urgency = (
            0.45 * motion_term +
            0.35 * cache_term +
            0.05 * tracker_risk +
            0.10 * entropy_term -
            0.10 * budget_term
        )

        urgency = float(
            np.clip(
                urgency,
                0.0,
                1.5
            )
        )

        self.last_urgency = urgency

        return urgency

    def should_detect(
        self,
        state: SystemState
    ):

        self.update_motion_history(
            state.motion_score
        )

        urgency = self.compute_urgency(
            state
        )

        # ==========================================
        # cache 太舊，強制跑 YOLO
        # ==========================================
        if self.cache_age >= self.force_refresh:

            self.cache_age = 0

            return True, urgency, "force_refresh"

        # ==========================================
        # urgency 達標，跑 YOLO
        # ==========================================
        if urgency >= self.urgency_threshold:

            self.cache_age = 0

            return True, urgency, "high_urgency"

        # ==========================================
        # 否則沿用 cache
        # ==========================================
        self.cache_age += 1

        return False, urgency, "reuse_cache"


# ==========================================
# 舊版相容包裝
# 若某些舊程式還在呼叫：
# scheduler.should_detect(motion_score)
# 可以繼續跑
# ==========================================
class MotionScheduler(BOSScheduler):

    def __init__(
        self,
        motion_threshold=0.03,
        max_idle=10,
        history_size=10,
        burst_weight=1.5
    ):

        super().__init__(
            base_motion_threshold=motion_threshold,
            history_size=history_size,
            urgency_threshold=0.55,
            force_refresh=max_idle,
            burst_weight=burst_weight
        )

    def should_detect(
        self,
        motion_score
    ):

        state = SystemState(
            motion_score=motion_score,
            classifier_entropy=0.0,
            tracker_confidence=1.0,
            budget_pressure=0.0
        )

        run_detect, urgency, reason = super().should_detect(
            state
        )

        return run_detect