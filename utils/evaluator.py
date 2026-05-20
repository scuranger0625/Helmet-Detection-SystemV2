class Evaluator:

    def __init__(self):

        self.total_frames = 0
        self.yolo_calls = 0
        self.total_fps = 0.0
        self.violation_count = 0

    def update(
        self,

        fps,
        yolo_run,
        violations
    ):

        self.total_frames += 1
        self.total_fps += fps
        self.violation_count = violations

        if yolo_run:

            self.yolo_calls += 1

    def summary(self):

        avg_fps = (
            self.total_fps /
            max(self.total_frames, 1)
        )

        yolo_ratio = (
            self.yolo_calls /
            max(self.total_frames, 1)
        )

        saved_ratio = (
            1.0 - yolo_ratio
        )

        # ==========================================
        # 額外統計
        # ==========================================
        skipped_frames = (
            self.total_frames -
            self.yolo_calls
        )

        # 每100幀平均 YOLO 次數
        yolo_calls_per_100_frames = (
            yolo_ratio * 100.0
        )

        # 平均幾幀才跑一次 YOLO
        avg_frames_per_yolo_call = (
            self.total_frames /
            max(self.yolo_calls, 1)
        )

        # detector 成本降低百分比
        detector_cost_reduction_percent = (
            saved_ratio * 100.0
        )

        return {

            "saved_ratio": saved_ratio,

            "total_frames": self.total_frames,

            "avg_fps": avg_fps,

            "yolo_calls": self.yolo_calls,

            "yolo_ratio": yolo_ratio,

            "violations": self.violation_count,

            # ==========================================
            # 新增指標
            # ==========================================
            "skipped_frames": skipped_frames,

            "yolo_calls_per_100_frames":
                yolo_calls_per_100_frames,

            "avg_frames_per_yolo_call":
                avg_frames_per_yolo_call,

            "detector_cost_reduction_percent":
                detector_cost_reduction_percent
        }