import video_anomaly_service as video_service

CONFIG = video_service.get_config()

video_service.clear_bucket(CONFIG['minio_baseline_bucket'])