from pathlib import Path

# ── Project Paths ──────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Model Settings ─────────────────────────────────────────────────────────────
YOLO_MODEL = "yolov8n.pt"          # Model file (downloaded on first run)
CONFIDENCE_THRESHOLD = 0.3          # Minimum confidence for detections
IOU_THRESHOLD = 0.45                # Intersection over Union for NMS

# ── OCR Settings ───────────────────────────────────────────────────────────────
OCR_LANGUAGES = ['en']              # EasyOCR language codes
OCR_GPU = False                     # Set True if CUDA is available

# ── Upload & Security ──────────────────────────────────────────────────────────
MAX_IMAGE_SIZE_MB = 20.0
MAX_VIDEO_SIZE_MB = 200.0
ALLOWED_IMAGE_TYPES = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_VIDEO_TYPES = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

# ── Processing & UI ────────────────────────────────────────────────────────────
VIDEO_SKIP_FRAMES = 2               # Process every Nth frame
MAX_VIDEO_FRAMES = 500              # Cap total frames processed

ANNOTATED_COLOR = (0, 255, 80)      # BGR color for bounding boxes
TEXT_COLOR = (255, 255, 255)        # BGR color for labels
FONT_SCALE = 0.8
FONT_THICKNESS = 2
