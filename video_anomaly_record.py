import time
import logging
import cv2
import uuid
import video_anomaly_service as video_service
import os 

dir_path = os.path.dirname(os.path.realpath(__file__))
logger = logging.getLogger(__name__)

BUCKET = ''
IS_BASELINE = False

video_service.setup()

CONFIG = video_service.get_config()

if IS_BASELINE:
    BUCKET_NAME = CONFIG["minio_baseline_bucket"]
else:
    BUCKET_NAME = CONFIG["minio_alarm_bucket"]    

cam = cv2.VideoCapture(0)

frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

fourcc = cv2.VideoWriter_fourcc(*'mp4v')
myuuid = str(uuid.uuid4())

video_file_path = dir_path + "/"+  CONFIG['temp_folder'] + '/' + myuuid + ".mp4"
out = cv2.VideoWriter(video_file_path, fourcc, 20.0, (frame_width, frame_height))


frame = None

frames = []

#maybe move the camera
while True:
    if cv2.waitKey(1) == ord('q'):
        break
    ret, frame = cam.read()
    cv2.imshow('Camera', frame)
    out.write(frame)

cam.release()
out.release()   
cv2.destroyAllWindows() 

time.sleep(3)

video_service.save_video(BUCKET_NAME, myuuid,video_file_path)    

os.remove(video_file_path)




 





