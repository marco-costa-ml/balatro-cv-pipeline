import os
import csv
import cv2
import torch
import numpy as np
from pathlib import Path
from ultralytics import YOLO

# ---------------- paths ----------------
video_path = "external/data/videos/sample.mp4"
out_csv = Path("external/event_classification/frames/det/sample.yolo.frames.csv")
model_path = "external/runs/detect/train/weights/best.pt"

frame_stride = 5


model_name = "YOLO"
model_version = "best.pt"
box_layout_version = ""

video_id = Path(video_path).stem

# ---------------- model ----------------

gpu_id = 1
torch.cuda.set_device(gpu_id)
model = YOLO(model_path).to(f"cuda:{gpu_id}")

# ---------------- video ----------------
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)

with open(out_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "video_id",
        "frame_idx",
        "timestamp_ms",
        "class_id",
        "conf",
        "x1",
        "y1",
        "x2",
        "y2",
        "model_name",
        "model_version",
        "box_layout_version",
    ])

    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_stride != 0:
            frame_idx += 1
            continue

        timestamp_ms = int(1000 * frame_idx / fps)

        results = model(frame, conf=0.3, iou=0.5, verbose=False)[0]

        if results.boxes is not None:
            boxes = results.boxes.xyxy.cpu().numpy()
            classes = results.boxes.cls.cpu().numpy()
            confs = results.boxes.conf.cpu().numpy()

            for cls, conf, box in zip(classes, confs, boxes):
                writer.writerow([
                    video_id,
                    frame_idx,
                    timestamp_ms,
                    int(cls),
                    float(conf),
                    float(box[0]),
                    float(box[1]),
                    float(box[2]),
                    float(box[3]),
                    model_name,
                    model_version,
                    box_layout_version,
                ])

        frame_idx += 1

cap.release()
print(f"wrote {out_csv}")
