import cv2
import uvicorn
import os
import asyncio

from pathlib import Path

from fastapi import FastAPI
from fastapi import Request
from fastapi import File
from fastapi import UploadFile

from fastapi.responses import (
    StreamingResponse,
    HTMLResponse,
    JSONResponse
)

from fastapi.templating import (
    Jinja2Templates
)

from fastapi.middleware.cors import (
    CORSMiddleware
)

from runtime.modules import (
    InferenceModules
)

from runtime.runtime import (
    RuntimeState
)

from runtime.pipeline import (
    process_frame
)

# =====================================================
# Base Directory
# =====================================================

BASE_DIR = Path(__file__).resolve().parent

# =====================================================
# FastAPI
# =====================================================

app = FastAPI(
    title="Helmet Detection System"
)

# =====================================================
# CORS
# =====================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# Templates
# =====================================================

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

# =====================================================
# Video Paths
# =====================================================

VIDEO_DIR = str(
    BASE_DIR / "video"
)

VIDEO_SOURCE = str(
    BASE_DIR
    / "video"
    / "input_video.mp4"
)

os.makedirs(
    VIDEO_DIR,
    exist_ok=True
)

# =====================================================
# Global Stats
# =====================================================

global_stats = {

    "fps": 0.0,

    "violations": 0,

    "motion": 0.0,

    "urgency": 0.0,

    "yolo_run": False,

    "rider_count": 0,

    "yolo_calls": 0,

    "total_frames": 0,

    "saved_ratio": 0.0,

    "avg_inference_ms": 0.0
}

# =====================================================
# Runtime Modules
# =====================================================

modules = InferenceModules()

runtime = RuntimeState()

# =====================================================
# Home Page
# =====================================================

@app.get(
    "/",
    response_class=HTMLResponse
)

async def index(
    request: Request
):

    return templates.TemplateResponse(

        request=request,

        name="index.html",

        context={
            "request": request
        }
    )

# =====================================================
# Upload Video
# =====================================================

@app.post("/upload_video")

async def upload_video(

    file: UploadFile = File(...)
):

    try:

        content = await file.read()

        with open(
            VIDEO_SOURCE,
            "wb"
        ) as f:

            f.write(content)

            f.flush()

            os.fsync(f.fileno())

        # reset runtime
        modules.reset(runtime)

        global_stats["fps"] = 0.0

        global_stats["violations"] = 0

        print("✅ 新影片已載入")

        return {

            "status": "success"
        }

    except Exception as e:

        return JSONResponse(

            status_code=500,

            content={
                "message": str(e)
            }
        )

# =====================================================
# Stats
# =====================================================

@app.get("/stats")

async def get_stats():

    return global_stats

# =====================================================
# Frame Generator
# =====================================================

async def gen_frames():

    global global_stats

    await asyncio.sleep(1.0)

    if not os.path.exists(
        VIDEO_SOURCE
    ):
        return

    cap = cv2.VideoCapture(
        VIDEO_SOURCE
    )

    frame_idx = 0

    encode_param = [

        int(cv2.IMWRITE_JPEG_QUALITY),

        80
    ]

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        frame_idx += 1

        try:

            output_frame = process_frame(

                frame,

                frame_idx,

                runtime,

                modules
            )

        except Exception as e:

            print(
                f"辨識出錯！"
                f"{frame.shape[1]}x"
                f"{frame.shape[0]}"
            )

            print(
                f"錯誤原因: {e}"
            )

            output_frame = frame

        # update stats
        global_stats["fps"] = round(

            modules.fps_counter.fps

            if hasattr(
                modules.fps_counter,
                "fps"
            )

            else 0.0,

            1
        )

        global_stats["violations"] = (
            runtime.violation_count
        )

        # ==================================================
        # Motion Score
        # ==================================================
        global_stats["motion"] = round(

            runtime.motion_score,

            3

        ) if hasattr(
            runtime,
            "motion_score"
        ) else 0.0

        # ==================================================
        # Urgency Score
        # ==================================================
        global_stats["urgency"] = round(

            runtime.urgency_score,

            3

        ) if hasattr(
            runtime,
            "urgency_score"
        ) else 0.0

        # ==================================================
        # YOLO 是否執行
        # ==================================================
        global_stats["yolo_run"] = (

            runtime.last_yolo_run

        ) if hasattr(
            runtime,
            "last_yolo_run"
        ) else False

        # ==================================================
        # Rider Count
        # ==================================================
        global_stats["rider_count"] = (

            runtime.rider_count

        ) if hasattr(
            runtime,
            "rider_count"
        ) else 0

        # ==================================================
        # YOLO 呼叫次數
        # ==================================================
        global_stats["yolo_calls"] = (

            runtime.yolo_calls

        ) if hasattr(
            runtime,
            "yolo_calls"
        ) else 0

        # ==================================================
        # Total Frames
        # ==================================================
        global_stats["total_frames"] = frame_idx

        # ==================================================
        # Saved Compute Ratio
        # ==================================================
        if frame_idx > 0:

            saved_ratio = 1.0 - (

                global_stats["yolo_calls"]

                / frame_idx
            )

            global_stats["saved_ratio"] = round(

                saved_ratio * 100,

                1
            )

        # ==================================================
        # Avg Inference Time
        # ==================================================
        global_stats["avg_inference_ms"] = round(

            runtime.avg_inference_ms,

            1

        ) if hasattr(
            runtime,
            "avg_inference_ms"
        ) else 0.0

        # encode jpg
        ret, buffer = cv2.imencode(

            ".jpg",

            output_frame,

            encode_param
        )

        if not ret:
            continue

        yield (

            b"--frame\r\n"

            b"Content-Type: image/jpeg\r\n\r\n"

            + buffer.tobytes()

            + b"\r\n"
        )

        await asyncio.sleep(0.005)

    cap.release()

# =====================================================
# Video Feed
# =====================================================

@app.get("/video_feed")

async def video_feed():

    return StreamingResponse(

        gen_frames(),

        media_type=(
            "multipart/x-mixed-replace;"
            " boundary=frame"
        )
    )

# =====================================================
# Main
# =====================================================

if __name__ == "__main__":

    uvicorn.run(

        app,

        host="0.0.0.0",

        port=8000
    )