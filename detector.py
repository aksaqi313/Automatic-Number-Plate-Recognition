"""
License Plate Detector using YOLOv8
Detects plates using a general object detector + heuristic plate cropping
as a fallback, making it robust for South Asian vehicles.
"""

importcv2
importnumpyasnp
fromultralyticsimportYOLO
fromconfigimport(
YOLO_MODEL,CONFIDENCE_THRESHOLD,IOU_THRESHOLD,
ANNOTATED_COLOR,TEXT_COLOR,FONT_SCALE,FONT_THICKNESS
)


classPlateDetector:
    def__init__(self):
        print("[Detector] Loading YOLOv8 model...")
self.model=YOLO(YOLO_MODEL)
print("[Detector] Model loaded successfully.")

defdetect(self,image:np.ndarray):
        """
        Detect license plates in the given BGR image.
        Returns list of dicts: [{bbox, crop, label}]
        """
results=self.model(image,conf=CONFIDENCE_THRESHOLD,
iou=IOU_THRESHOLD,verbose=False)
detections=[]

forresultinresults:
            boxes=result.boxes
ifboxesisNone:
                continue
forboxinboxes:
                cls_id=int(box.cls[0])
cls_name=self.model.names[cls_id]
conf=float(box.conf[0])
x1,y1,x2,y2=map(int,box.xyxy[0])



detections.append({
"label":cls_name,
"confidence":conf,
"bbox":(x1,y1,x2,y2),
"is_plate":False,
})


plate_crops=self._extract_plate_regions(image,detections)


contour_plates=self._contour_plate_detector(image)

all_plates=plate_crops+contour_plates
returnall_plates,detections

def_extract_plate_regions(self,image,vehicle_detections):
        """Extract likely plate regions from bottom portion of vehicle bboxes."""
h,w=image.shape[:2]
plates=[]
vehicle_classes={
"car","truck","bus","motorcycle","bicycle",
"vehicle","auto","rickshaw"
}

fordetinvehicle_detections:
            ifdet["label"].lower()notinvehicle_classes:
                continue
x1,y1,x2,y2=det["bbox"]

plate_y1=y1+int((y2-y1)*0.65)
plate_y2=y2
plate_x1=x1+int((x2-x1)*0.10)
plate_x2=x2-int((x2-x1)*0.10)

crop=image[plate_y1:plate_y2,plate_x1:plate_x2]
ifcrop.size==0:
                continue
plates.append({
"label":"license_plate",
"confidence":det["confidence"],
"bbox":(plate_x1,plate_y1,plate_x2,plate_y2),
"crop":crop,
"is_plate":True,
})

returnplates

def_contour_plate_detector(self,image):
        """
        Classic computer vision plate localisation using contours.
        Works well for rectangular plates under reasonable lighting.
        """
gray=cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
blur=cv2.bilateralFilter(gray,11,17,17)
edges=cv2.Canny(blur,30,200)

contours,_=cv2.findContours(
edges,cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE
)
contours=sorted(contours,key=cv2.contourArea,reverse=True)[:20]

plates=[]
h,w=image.shape[:2]
img_area=h*w

forcntincontours:
            peri=cv2.arcLength(cnt,True)
approx=cv2.approxPolyDP(cnt,0.018*peri,True)
area=cv2.contourArea(cnt)
rect=cv2.boundingRect(approx)
rx,ry,rw,rh=rect
aspect=rw/float(rh)ifrh>0else0
area_ratio=area/img_area


if(len(approx)>=4and
1.5<aspect<6.0and
0.001<area_ratio<0.15):
                crop=image[ry:ry+rh,rx:rx+rw]
ifcrop.size==0:
                    continue
plates.append({
"label":"license_plate",
"confidence":0.75,
"bbox":(rx,ry,rx+rw,ry+rh),
"crop":crop,
"is_plate":True,
})


plates=self._nms_plates(plates)
returnplates

def_nms_plates(self,plates,iou_thresh=0.4):
        """Simple NMS for plate detections."""
ifnotplates:
            return[]
boxes=np.array([p["bbox"]forpinplates],dtype=float)
scores=np.array([p["confidence"]forpinplates])
x1=boxes[:,0];y1=boxes[:,1]
x2=boxes[:,2];y2=boxes[:,3]
areas=(x2-x1+1)*(y2-y1+1)
order=scores.argsort()[::-1]
keep=[]
whileorder.size>0:
            i=order[0]
keep.append(i)
xx1=np.maximum(x1[i],x1[order[1:]])
yy1=np.maximum(y1[i],y1[order[1:]])
xx2=np.minimum(x2[i],x2[order[1:]])
yy2=np.minimum(y2[i],y2[order[1:]])
inter=np.maximum(0,xx2-xx1+1)*np.maximum(0,yy2-yy1+1)
iou=inter/(areas[i]+areas[order[1:]]-inter)
order=order[np.where(iou<=iou_thresh)[0]+1]
return[plates[i]foriinkeep]

defdraw_annotations(self,image:np.ndarray,plates,ocr_results):
        """Draw boxes and plate text on the image."""
annotated=image.copy()
fori,plateinenumerate(plates):
            x1,y1,x2,y2=plate["bbox"]
text=ocr_results[i]ifi<len(ocr_results)else""

cv2.rectangle(annotated,(x1,y1),(x2,y2),ANNOTATED_COLOR,2)

label=f" {text} "iftextelse" Plate "
(tw,th),_=cv2.getTextSize(
label,cv2.FONT_HERSHEY_SIMPLEX,FONT_SCALE,FONT_THICKNESS
)
cv2.rectangle(
annotated,
(x1,y1-th-10),
(x1+tw,y1),
ANNOTATED_COLOR,-1
)
cv2.putText(
annotated,label,
(x1,y1-5),
cv2.FONT_HERSHEY_SIMPLEX,
FONT_SCALE,(0,0,0),FONT_THICKNESS
)
returnannotated
