"""
FastAPI Backend for Automatic Number Plate Recognition (ANPR)
Endpoints:
  GET  /           → serve frontend
  POST /detect/image → process image upload
  POST /detect/video → process video upload
  GET  /demo       → generate and process demo image
"""

importos
importuuid
importshutil
importbase64
importtraceback
frompathlibimportPath

importcv2
importnumpyasnp
fromfastapiimportFastAPI,File,UploadFile,HTTPException
fromfastapi.responsesimportJSONResponse,FileResponse
fromfastapi.staticfilesimportStaticFiles
fromfastapi.middleware.corsimportCORSMiddleware

fromconfigimport(
OUTPUT_DIR,ALLOWED_IMAGE_TYPES,ALLOWED_VIDEO_TYPES,
MAX_IMAGE_SIZE_MB,MAX_VIDEO_SIZE_MB,
VIDEO_SKIP_FRAMES,MAX_VIDEO_FRAMES
)
fromdetectorimportPlateDetector
fromocr_engineimportOCREngine


app=FastAPI(title="ANPR System",version="1.0.0")

app.add_middleware(
CORSMiddleware,
allow_origins=["*"],allow_methods=["*"],allow_headers=["*"]
)

os.makedirs(OUTPUT_DIR,exist_ok=True)


_detector:PlateDetector|None=None
_ocr:OCREngine|None=None


defget_detector()->PlateDetector:
    global_detector
if_detectorisNone:
        _detector=PlateDetector()
return_detector


defget_ocr()->OCREngine:
    global_ocr
if_ocrisNone:
        _ocr=OCREngine()
return_ocr



defimg_to_b64(image:np.ndarray,ext:str=".jpg")->str:
    ok,buf=cv2.imencode(ext,image)
ifnotok:
        return""
returnbase64.b64encode(buf.tobytes()).decode("utf-8")


defvalidate_upload(file:UploadFile,allowed:set,max_mb:float):
    ext=Path(file.filename).suffix.lower()
ifextnotinallowed:
        raiseHTTPException(
400,
detail=f"Unsupported file type '{ext}'. Allowed: {allowed}"
)



static_dir=Path(__file__).parent/"static"

app.mount("/static",StaticFiles(directory=str(static_dir)),name="static")


@app.get("/")
asyncdefserve_frontend():
    returnFileResponse(str(static_dir/"index.html"))


@app.post("/detect/image")
asyncdefdetect_image(file:UploadFile=File(...)):
    validate_upload(file,ALLOWED_IMAGE_TYPES,MAX_IMAGE_SIZE_MB)
try:
        contents=awaitfile.read()
np_arr=np.frombuffer(contents,np.uint8)
image=cv2.imdecode(np_arr,cv2.IMREAD_COLOR)

ifimageisNone:
            raiseHTTPException(400,"Could not decode image.")

detector=get_detector()
ocr=get_ocr()

plates,vehicle_dets=detector.detect(image)

crops=[p["crop"]forpinplates]
plate_texts=ocr.read_all_plates(crops)

annotated=detector.draw_annotations(image,plates,plate_texts)


plate_results=[]
fori,pinenumerate(plates):
            text=plate_texts[i]ifi<len(plate_texts)else""
crop_b64=img_to_b64(p["crop"])ifp.get("crop")isnotNoneelse""
plate_results.append({
"text":text,
"confidence":round(p["confidence"],3),
"bbox":list(p["bbox"]),
"crop_image":crop_b64,
})

annotated_b64=img_to_b64(annotated)

returnJSONResponse({
"success":True,
"total_plates":len(plates),
"plates":plate_results,
"annotated_image":annotated_b64,
})

exceptHTTPException:
        raise
exceptExceptionase:
        traceback.print_exc()
raiseHTTPException(500,detail=str(e))


@app.post("/detect/video")
asyncdefdetect_video(file:UploadFile=File(...)):
    validate_upload(file,ALLOWED_VIDEO_TYPES,MAX_VIDEO_SIZE_MB)

tmp_path=Path(OUTPUT_DIR)/f"tmp_{uuid.uuid4().hex}{Path(file.filename).suffix}"
out_path=Path(OUTPUT_DIR)/f"out_{uuid.uuid4().hex}.mp4"

try:

        withopen(tmp_path,"wb")asf:
            shutil.copyfileobj(file.file,f)

cap=cv2.VideoCapture(str(tmp_path))
fps=cap.get(cv2.CAP_PROP_FPS)or25
w=int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
h=int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc=cv2.VideoWriter_fourcc(*"mp4v")
writer=cv2.VideoWriter(str(out_path),fourcc,fps,(w,h))

detector=get_detector()
ocr=get_ocr()

all_plate_texts=[]
frame_idx=0
processed=0

whileprocessed<MAX_VIDEO_FRAMES:
            ret,frame=cap.read()
ifnotret:
                break
frame_idx+=1

ifframe_idx%VIDEO_SKIP_FRAMES!=0:
                writer.write(frame)
continue

plates,_=detector.detect(frame)
crops=[p["crop"]forpinplates]
plate_texts=ocr.read_all_plates(crops)

fortxtinplate_texts:
                iftxtandtxtnotinall_plate_texts:
                    all_plate_texts.append(txt)

annotated_frame=detector.draw_annotations(frame,plates,plate_texts)
writer.write(annotated_frame)
processed+=1

cap.release()
writer.release()


withopen(out_path,"rb")asf:
            video_b64=base64.b64encode(f.read()).decode("utf-8")

returnJSONResponse({
"success":True,
"total_unique_plates":len(all_plate_texts),
"plate_texts":all_plate_texts,
"annotated_video":video_b64,
"frames_processed":processed,
})

exceptHTTPException:
        raise
exceptExceptionase:
        traceback.print_exc()
raiseHTTPException(500,detail=str(e))
finally:
        iftmp_path.exists():
            tmp_path.unlink()
ifout_path.exists():
            out_path.unlink()


@app.get("/demo")
asyncdefdemo():
    """Generate and process a demo image with a sample license plate."""
try:

        height,width=480,640
image=np.ones((height,width,3),dtype=np.uint8)*80


cv2.rectangle(image,(0,250),(width,height),(100,100,100),-1)


foriinrange(0,width,50):
            cv2.line(image,(i,280),(i+30,280),(255,255,255),2)


car_x,car_y=200,150
car_width,car_height=300,120
cv2.rectangle(image,(car_x,car_y),(car_x+car_width,car_y+car_height),
(40,40,50),-1)


cv2.rectangle(image,(car_x+40,car_y+20),(car_x+140,car_y+60),
(150,180,220),-1)
cv2.rectangle(image,(car_x+160,car_y+20),(car_x+260,car_y+60),
(150,180,220),-1)


cv2.circle(image,(car_x+60,car_y+car_height),15,(30,30,30),-1)
cv2.circle(image,(car_x+240,car_y+car_height),15,(30,30,30),-1)


plate_x,plate_y=car_x+240,car_y+85
plate_width,plate_height=80,35
cv2.rectangle(image,(plate_x,plate_y),(plate_x+plate_width,plate_y+plate_height),
(245,245,245),-1)
cv2.rectangle(image,(plate_x,plate_y),(plate_x+plate_width,plate_y+plate_height),
(20,20,20),2)


plate_text="ABC1234"
font=cv2.FONT_HERSHEY_DUPLEX
font_scale=1.2
font_color=(20,20,20)
thickness=2
text_size=cv2.getTextSize(plate_text,font,font_scale,thickness)[0]
text_x=plate_x+(plate_width-text_size[0])//2
text_y=plate_y+(plate_height+text_size[1])//2
cv2.putText(image,plate_text,(text_x,text_y),font,font_scale,font_color,thickness)


detector=get_detector()
ocr=get_ocr()

plates,vehicle_dets=detector.detect(image)
crops=[p["crop"]forpinplates]
plate_texts=ocr.read_all_plates(crops)

annotated=detector.draw_annotations(image,plates,plate_texts)


plate_results=[]
fori,pinenumerate(plates):
            text=plate_texts[i]ifi<len(plate_texts)else""
crop_b64=img_to_b64(p["crop"])ifp.get("crop")isnotNoneelse""
plate_results.append({
"text":text,
"confidence":round(p["confidence"],3),
"bbox":list(p["bbox"]),
"crop_image":crop_b64,
})

annotated_b64=img_to_b64(annotated)

returnJSONResponse({
"success":True,
"total_plates":len(plates),
"plates":plate_results,
"annotated_image":annotated_b64,
"is_demo":True,
})

exceptExceptionase:
        traceback.print_exc()
raiseHTTPException(500,detail=str(e))
