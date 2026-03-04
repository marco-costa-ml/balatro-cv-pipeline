import os
import multiprocessing as mp

# must be first
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
mp.set_start_method("spawn", force=True)

import time
import json
import cv2
import torch
from pathlib import Path
from PIL import Image
from transformers import TrOCRProcessor, VisionEncoderDecoderModel

VIDEO_PATH = Path("external/data/videos/sample.mp4")
BOXES_JSON = Path("text_boxes.json")
MODEL_DIR = Path("trocr-game")

NUM_FRAMES = 16
MAX_TARGET_LENGTH = 16

with open(BOXES_JSON, "r") as f:
    BOXES = json.load(f)["boxes"]

def load_frames(n):
    cap = cv2.VideoCapture(str(VIDEO_PATH))
    frames = []
    for _ in range(n):
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    return frames

def worker_init():
    global processor, model
    torch.set_num_threads(1)
    processor = TrOCRProcessor.from_pretrained(MODEL_DIR)
    model = VisionEncoderDecoderModel.from_pretrained(MODEL_DIR)
    model.eval()

def ocr_frame_cpu(frame):
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    crops = []
    for box in BOXES:
        x1, y1, x2, y2 = box["bbox"]
        crop = frame_rgb[y1:y2, x1:x2]
        crops.append(Image.fromarray(crop))

    pixel_values = processor(images=crops, return_tensors="pt").pixel_values

    with torch.inference_mode():
        model.generate(
            pixel_values=pixel_values,
            max_length=MAX_TARGET_LENGTH,
            do_sample=False,
        )

if __name__ == "__main__":
    frames = load_frames(NUM_FRAMES)
    print("frames loaded:", len(frames))

    for workers in [1, 2, 4, 8]:
        t0 = time.time()
        with mp.Pool(processes=workers, initializer=worker_init) as pool:
            list(pool.imap_unordered(ocr_frame_cpu, frames))
        dt = time.time() - t0
        print(f"workers={workers} | fps={len(frames)/dt:.3f}")

