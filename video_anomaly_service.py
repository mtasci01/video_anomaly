import os
from minio import Minio
import cv2
from PIL import Image
from io import BytesIO
import hashlib

def get_config():
    return {
        "minio_url":"localhost:9000",
    "minio_access_key":"EzJtXz81jYGEEFHC",
    "minio_secret_key":"DCkU1WkwPT97yMEWV8G8bO7SXTzmhvmo",
    "minio_baseline_bucket":"video-anomaly-baseline",
    "minio_alarm_bucket":"video-anomaly-alarm",
    "minio_baseline_imgname": "video-anomaly-baseline",
    "assets_folder":"assets",
    "temp_folder":"temp"
    }

def  create_minio_client():
    config = get_config()  
    return Minio(config["minio_url"],
        access_key=config["minio_access_key"],
        secret_key=config["minio_secret_key"],
        secure=False
    ) 



def calculate_sha256(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
    

def opencv_to_pil_png(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    return pil_image 

def opencv_to_png_bytes(frame):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(rgb_frame)
    buffer = BytesIO()
    pil_image.save(buffer, format="PNG")
    png_data = buffer.getvalue()
    return png_data   

def get_minio_objects(bucket_name):
    client = create_minio_client()
    return client.list_objects(bucket_name, recursive=True)

def save_frame(bucket_name, object_name,frame_png, metadata):
    client = create_minio_client()
    client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=BytesIO(frame_png),
            length=len(frame_png),
            content_type="image/png"
        ) 

def save_video(bucket_name, object_name,video_file_path):
    client = create_minio_client()
    client.fput_object(
        bucket_name=bucket_name,
        object_name=object_name,
        file_path=video_file_path,
        content_type="video/mp4" 
    )
    print("saved " + object_name + " in bucket " + bucket_name)    

def get_baseline():
    client = create_minio_client()
    config = get_config()  
    response = client.get_object(
            bucket_name=config["minio_baseline_bucket"],
            object_name=config["minio_baseline_imgname"]
    )     

    image_data = response.read()  
    response.close() 
    response.release_conn()  

    image = Image.open(BytesIO(image_data))
    
    if image.format != 'PNG':
        raise ValueError("The downloaded object is not a PNG image")
    
    return image


def download_file(bucket_name, file_id, download_path):
    client = create_minio_client()
    client.fget_object(bucket_name, file_id, download_path)
         

def sync_bucket(bucket_name):
    client = create_minio_client()
    found = client.bucket_exists(bucket_name)
    if not found:
        client.make_bucket(bucket_name)
        print("Created bucket", bucket_name)
    else:
        print("Bucket", bucket_name, "already exists")

def clear_bucket(bucket_name):
    client = create_minio_client()
    objects = client.list_objects(bucket_name, recursive=True, include_version=True)
    for obj in objects:
        client.remove_object(bucket_name, obj.object_name, version_id=obj.version_id)
        print("removed " + obj.object_name + " in bucket " + bucket_name) 
        

def setup(): 
    config = get_config()       
    sync_bucket(config["minio_baseline_bucket"])
    sync_bucket(config["minio_alarm_bucket"])
    dir_path = os.path.dirname(os.path.realpath(__file__))
    if not os.path.exists(dir_path + "/" + config['temp_folder']):
         os.makedirs(dir_path + "/" + config['temp_folder'])
    if not os.path.exists(dir_path + "/" + config['assets_folder']):
         os.makedirs(dir_path + "/" + config['assets_folder'])     