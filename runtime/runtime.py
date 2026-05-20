from dataclasses import dataclass, field


@dataclass
class RuntimeState:

    cached_detections: list = field(default_factory=list)

    violation_count: int = 0

    yolo_history: list = field(default_factory=list)

    def reset(
        self,
        scheduler,
        motion_estimator,
        classifier
    ):

        self.cached_detections.clear()

        self.violation_count = 0

        self.yolo_history.clear()

        scheduler.reset()

        motion_estimator.prev_gray = None

        classifier.reset()