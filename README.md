## Automatic Number Plate Recognition (ANPR)

FastAPI-based backend for automatic number plate recognition from **images**, **videos**, and **live streams**.

The service exposes HTTP endpoints that:
- **Serve a frontend** from the `static` folder.
- **Detect plates in images** and return plate texts + annotated image.
- **Detect plates in videos** and return unique plate texts + annotated video.
- **Process IP/CCTV streams** and return unique plate texts + an annotated snapshot.

---

## Features

- **FastAPI backend** (`app.py`) with:
  - `GET /` → serves `static/index.html`
  - `POST /detect/image` → image upload, returns JSON with:
    - detected plate texts
    - confidence scores
    - bounding boxes
    - annotated image (base64)
  - `POST /detect/video` → video upload, returns:
    - unique plate texts across frames
    - processed frame count
    - annotated video (base64)
  - `GET /detect/stream?url=...` → processes a short segment from an RTSP/HTTP stream.
- **Plate detection** (via `PlateDetector` in `detector.py`).
- **OCR engine** (`OCREngine` in `ocr_engine.py`) using **EasyOCR** with preprocessing for better accuracy.
- Basic configuration in `config.py` (file types, size limits, OCR languages, GPU flag, frame skipping, etc.).

---

## Requirements

You need **Python 3.10+** installed and available on your PATH.

Python packages (typical):
- `fastapi`
- `uvicorn`
- `opencv-python`
- `numpy`
- `easyocr`

If you have a `requirements.txt` in the project, you can install everything with:

```bash
pip install -r requirements.txt
```

Otherwise, install the core dependencies manually:

```bash
pip install fastapi uvicorn opencv-python numpy easyocr
```

> On Windows you may also need additional Microsoft C++ build tools for some libraries.

---

## How to Run (Development)

From the project root:

```bash
cd "Automatic Number Plate Recognition"
uvicorn app:app --reload
```

Then open in your browser:

```text
http://127.0.0.1:8000/
```

If `static/index.html` is present, it will be served at `/`.  
The API docs are also available at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

---

## API Overview

- **`GET /`**
  - Serves the frontend HTML (`static/index.html`).

- **`POST /detect/image`**
  - Body: `multipart/form-data` with `file` (image).
  - Returns JSON:
    - `success` (bool)
    - `total_plates`
    - `plates`: list of:
      - `text`
      - `confidence`
      - `bbox`
      - `crop_image` (base64)
    - `annotated_image` (base64 of full frame with boxes & labels).

- **`POST /detect/video`**
  - Body: `multipart/form-data` with `file` (video).
  - Returns JSON:
    - `success`
    - `total_unique_plates`
    - `plate_texts` (list)
    - `annotated_video` (base64-encoded MP4)
    - `frames_processed`

- **`GET /detect/stream?url=...`**
  - Query param: `url` → RTSP/HTTP URL of your IP/CCTV camera.
  - Returns JSON:
    - `success`
    - `total_unique_plates`
    - `plate_texts`
    - `annotated_frame` (base64 of one annotated frame)
    - `frames_processed`

---

## OCR Engine Details

`ocr_engine.py` defines `OCREngine`, which:
- Loads an **EasyOCR** reader (`easyocr.Reader`) with languages from `config.OCR_LANGUAGES`.
- Uses GPU if `config.OCR_GPU` is `True`.
- Preprocesses plate crops by:
  - Upscaling small plates.
  - Converting to grayscale and sharpening.
  - Applying adaptive thresholding.
- Cleans the OCR text to keep:
  - A–Z, 0–9
  - Dashes and spaces
  - Optional Arabic/Persian characters (`\u0600-\u06FF`).

---

## Notes

- The first request may be slower because the detector and OCR models are lazy-loaded.
- Large video/stream processing may be CPU/GPU intensive; tune parameters in `config.py` (`VIDEO_SKIP_FRAMES`, `MAX_VIDEO_FRAMES`, etc.).
- Ensure your Python environment has the correct **OpenCV** and **EasyOCR** dependencies for your OS.
