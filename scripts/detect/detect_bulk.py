import os
import torch
import csv
import cv2
import numpy as np
from multiprocessing import Process
from ultralytics import YOLO
from tqdm import tqdm

# config
VIDEO_DIR = "external/videos"
VIDEO_LIST = [f for f in os.listdir(VIDEO_DIR) if f.endswith(".mp4")]
MODEL_PATH = "external/runs/detect/train/weights/best.pt"
SKIP_EVERY = 40
GPUS = [1, 3, 4, 5, 6, 7]

def process_video(video_file, gpu_id):
    print(f"🚀 starting {video_file} on GPU {gpu_id}")
    try:
        torch.cuda.set_device(gpu_id)
        model = YOLO(MODEL_PATH).to(f"cuda:{gpu_id}")
        print(f"✅ model ready on cuda:{gpu_id}")
    except Exception as e:
        print(f"❌ failed to load model on GPU {gpu_id}: {e}")
        return

    input_path = os.path.join(VIDEO_DIR, video_file)
    output_path = os.path.join(VIDEO_DIR, f"{os.path.splitext(video_file)[0]}.csv")

    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"❌ can't open {video_file}")
        return

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"📼 {video_file}: {total_frames} frames")

    frame_id = 0
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "class_id", "conf", "x1", "y1", "x2", "y2"])

        with tqdm(total=total_frames, desc=video_file) as pbar:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    print(f"🔚 done reading {video_file}")
                    break

                if frame_id % SKIP_EVERY == 0:
                    if frame is None or not isinstance(frame, torch.Tensor) and not isinstance(frame, (np.ndarray,)):
                        print(f"⚠️ invalid frame at {frame_id}")
                    else:
                        try:
                            results = model(frame, conf=0.3, iou=0.5)[0]
                            boxes = results.boxes.xyxy.cpu()
                            classes = results.boxes.cls.cpu()
                            confs = results.boxes.conf.cpu()

                            for cls, conf, box in zip(classes, confs, boxes):
                                #if int(cls) >= 52:
                                #    continue
                                writer.writerow([frame_id, int(cls), float(conf), *map(float, box)])
                        except Exception as e:
                            print(f"❌ error at frame {frame_id}: {e}")

                frame_id += 1
                pbar.update(1)

    cap.release()
    print(f"✅ done: {video_file}")

if __name__ == "__main__":
    processes = []
    for idx, video in enumerate(VIDEO_LIST):
        gpu_id = GPUS[idx % len(GPUS)]
        p = Process(target=process_video, args=(video, gpu_id))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()
