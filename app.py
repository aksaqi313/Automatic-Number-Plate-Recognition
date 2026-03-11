"""
FastAPI Backend for Automatic Number Plate Recognition (ANPR)
Endpoints:
  GET  /           → serve frontend
  POST /detect/image → process image upload
  POST /detect/video → process video upload
"""

import os
import uuid
import shutil
import base64
import traceback
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from config import (
    OUTPUT_DIR, ALLOWED_IMAGE_TYPES, ALLOWED_VIDEO_TYPES,
    MAX_IMAGE_SIZE_MB, MAX_VIDEO_SIZE_MB,
    VIDEO_SKIP_FRAMES, MAX_VIDEO_FRAMES
)
from detector import PlateDetector
from ocr_engine import OCREngine

# ── Initialisation ─────────────────────────────────────────────────────────────
app = FastAPI(title="ANPR System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Lazy-load models (first request may be slower)
_detector: PlateDetector | None = None
_ocr: OCREngine | None = None


def get_detector() -> PlateDetector:
    global _detector
    if _detector is None:
        _detector = PlateDetector()
    return _detector


def get_ocr() -> OCREngine:
    global _ocr
    if _ocr is None:
        _ocr = OCREngine()
    return _ocr


# ── Helpers ────────────────────────────────────────────────────────────────────
def img_to_b64(image: np.ndarray, ext: str = ".jpg") -> str:
    ok, buf = cv2.imencode(ext, image)
    if not ok:
        return ""
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def validate_upload(file: UploadFile, allowed: set, max_mb: float):
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed:
        raise HTTPException(
            400,
            detail=f"Unsupported file type '{ext}'. Allowed: {allowed}"
        )


# ── Routes ─────────────────────────────────────────────────────────────────────
static_dir = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse(str(static_dir / "index.html"))


@app.post("/detect/image")
async def detect_image(file: UploadFile = File(...)):
    validate_upload(file, ALLOWED_IMAGE_TYPES, MAX_IMAGE_SIZE_MB)
    try:
        contents = await file.read()
        np_arr = np.frombuffer(contents, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if image is None:
            raise HTTPException(400, "Could not decode image.")

        detector = get_detector()
        ocr = get_ocr()

        plates, vehicle_dets = detector.detect(image)

        crops = [p["crop"] for p in plates]
        plate_texts = ocr.read_all_plates(crops)

        annotated = detector.draw_annotations(image, plates, plate_texts)

        # Build result payload
        plate_results = []
        for i, p in enumerate(plates):
            text = plate_texts[i] if i < len(plate_texts) else ""
            crop_b64 = img_to_b64(p["crop"]) if p.get("crop") is not None else ""
            plate_results.append({
                "text": text,
                "confidence": round(p["confidence"], 3),
                "bbox": list(p["bbox"]),
                "crop_image": crop_b64,
            })

        annotated_b64 = img_to_b64(annotated)

        return JSONResponse({
            "success": True,
            "total_plates": len(plates),
            "plates": plate_results,
            "annotated_image": annotated_b64,
        })

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))


@app.post("/detect/video")
async def detect_video(file: UploadFile = File(...)):
    validate_upload(file, ALLOWED_VIDEO_TYPES, MAX_VIDEO_SIZE_MB)

    tmp_path = Path(OUTPUT_DIR) / f"tmp_{uuid.uuid4().hex}{Path(file.filename).suffix}"
    out_path = Path(OUTPUT_DIR) / f"out_{uuid.uuid4().hex}.mp4"

    try:
        # Save uploaded video to disk
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        cap = cv2.VideoCapture(str(tmp_path))
        fps = cap.get(cv2.CAP_PROP_FPS) or 25
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(out_path), fourcc, fps, (w, h))

        detector = get_detector()
        ocr = get_ocr()

        all_plate_texts = []
        frame_idx = 0
        processed = 0

        while processed < MAX_VIDEO_FRAMES:
            ret, frame = cap.read()
            if not ret:
                break
            frame_idx += 1

            if frame_idx % VIDEO_SKIP_FRAMES != 0:
                writer.write(frame)
                continue

            plates, _ = detector.detect(frame)
            crops = [p["crop"] for p in plates]
            plate_texts = ocr.read_all_plates(crops)

            for txt in plate_texts:
                if txt and txt not in all_plate_texts:
                    all_plate_texts.append(txt)

            annotated_frame = detector.draw_annotations(frame, plates, plate_texts)
            writer.write(annotated_frame)
            processed += 1

        cap.release()
        writer.release()

        # Encode output video to base64 for browser playback
        with open(out_path, "rb") as f:
            video_b64 = base64.b64encode(f.read()).decode("utf-8")

        return JSONResponse({
            "success": True,
            "total_unique_plates": len(all_plate_texts),
            "plate_texts": all_plate_texts,
            "annotated_video": video_b64,
            "frames_processed": processed,
        })

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(500, detail=str(e))
    finally:
        if tmp_path.exists():
            tmp_path.unlink()
        if out_path.exists():
            out_path.unlink()
