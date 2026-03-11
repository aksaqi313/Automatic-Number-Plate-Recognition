"""
OCR Engine — reads text from license plate image crops using EasyOCR.
"""

import re
import cv2
import numpy as np
import easyocr
from config import OCR_LANGUAGES, OCR_GPU


class OCREngine:
    def __init__(self):
        print("[OCR] Loading EasyOCR reader...")
        self.reader = easyocr.Reader(OCR_LANGUAGES, gpu=OCR_GPU)
        print("[OCR] EasyOCR ready.")

    def read_plate(self, crop: np.ndarray) -> str:
        """
        Given a BGR crop of a license plate, return the cleaned plate text.
        """
        if crop is None or crop.size == 0:
            return ""

        # Pre-process for better OCR
        processed = self._preprocess(crop)

        try:
            results = self.reader.readtext(processed, detail=0, paragraph=True)
        except Exception as e:
            print(f"[OCR] Error reading plate: {e}")
            return ""

        text = " ".join(results).strip()
        return self._clean_text(text)

    def read_all_plates(self, crops: list) -> list:
        """Read OCR text from a list of plate crop images."""
        return [self.read_plate(crop) for crop in crops]

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Enhance plate image for better OCR accuracy."""
        # Scale up small plates
        h, w = image.shape[:2]
        if w < 200:
            scale = 200 / w
            image = cv2.resize(
                image, (int(w * scale), int(h * scale)),
                interpolation=cv2.INTER_CUBIC
            )

        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Sharpen
        kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
        sharp = cv2.filter2D(gray, -1, kernel)
        # Adaptive threshold
        thresh = cv2.adaptiveThreshold(
            sharp, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        # Convert back to BGR for EasyOCR
        return cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

    def _clean_text(self, text: str) -> str:
        """Remove noise characters from OCR output."""
        # Keep alphanumeric + common plate separators
        text = re.sub(r"[^A-Z0-9\-\s\u0600-\u06FF]", "", text.upper())
        text = re.sub(r"\s+", " ", text).strip()
        return text
