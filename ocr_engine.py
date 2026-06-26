"""
OCR Engine — reads text from license plate image crops using EasyOCR.
"""

importre
importcv2
importnumpyasnp
importeasyocr
fromconfigimportOCR_LANGUAGES,OCR_GPU


classOCREngine:
    def__init__(self):
        print("[OCR] Loading EasyOCR reader...")
self.reader=easyocr.Reader(OCR_LANGUAGES,gpu=OCR_GPU)
print("[OCR] EasyOCR ready.")

defread_plate(self,crop:np.ndarray)->str:
        """
        Given a BGR crop of a license plate, return the cleaned plate text.
        """
ifcropisNoneorcrop.size==0:
            return""


processed=self._preprocess(crop)

try:
            results=self.reader.readtext(processed,detail=0,paragraph=True)
exceptExceptionase:
            print(f"[OCR] Error reading plate: {e}")
return""

text=" ".join(results).strip()
returnself._clean_text(text)

defread_all_plates(self,crops:list)->list:
        """Read OCR text from a list of plate crop images."""
return[self.read_plate(crop)forcropincrops]

def_preprocess(self,image:np.ndarray)->np.ndarray:
        """Enhance plate image for better OCR accuracy."""

h,w=image.shape[:2]
ifw<200:
            scale=200/w
image=cv2.resize(
image,(int(w*scale),int(h*scale)),
interpolation=cv2.INTER_CUBIC
)

gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)

kernel=np.array([[0,-1,0],[-1,5,-1],[0,-1,0]])
sharp=cv2.filter2D(gray,-1,kernel)

thresh=cv2.adaptiveThreshold(
sharp,255,
cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
cv2.THRESH_BINARY,11,2
)

returncv2.cvtColor(thresh,cv2.COLOR_GRAY2BGR)

def_clean_text(self,text:str)->str:
        """Remove noise characters from OCR output."""

text=re.sub(r"[^A-Z0-9\-\s\u0600-\u06FF]","",text.upper())
text=re.sub(r"\s+"," ",text).strip()
returntext
