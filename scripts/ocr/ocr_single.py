import sys
import json
import cv2
import csv
import numpy as np
from pathlib import Path

sys.path.insert(0, "external/ocr/PaddleOCR")

import paddle
from paddle.inference import Config, create_predictor
from tools.program import load_config
from ppocr.data import create_operators, transform
from ppocr.postprocess import build_post_process

# ---------------- paths ----------------
video_path = "../data_local/videos/sample.mp4"
boxes_path = "../assets/text_boxes.json"
out_csv = Path("../data_local/ocr_results/sample.ocr.frames.csv")

config_path = "../assets/en_PP-OCRv4_mobile_rec.yml"
model_path = "external/ocr/PaddleOCR/inference/rec_infer_custom/inference"

frame_stride = 5

model_name = "PP-OCRv4"
model_version = ""
box_layout_version = ""

video_id = Path(video_path).stem

# ---------------- load boxes ----------------
with open(boxes_path, "r") as f:
    boxes_data = json.load(f)["boxes"]

# ---------------- config ----------------
cfg = load_config(config_path)

BAD_KEYS = {
    "DecodeImage",
    "MultiLabelEncode",
    "CTCLabelEncode",
    "SARLabelEncode",
    "NRTRLabelEncode",
    "AttnLabelEncode",
    "KeepKeys",
}

cfg["Eval"]["dataset"]["transforms"] = [
    t for t in cfg["Eval"]["dataset"]["transforms"]
    if isinstance(t, dict) and not any(k in t for k in BAD_KEYS)
]

ops = create_operators(cfg["Eval"]["dataset"]["transforms"], cfg["Global"])
post_process = build_post_process(cfg["PostProcess"], cfg["Global"])

# ---------------- predictor ----------------
config = Config(
    model_path + ".pdmodel",
    model_path + ".pdiparams"
)
config.enable_use_gpu(100, 0)
config.switch_ir_optim(True)
config.enable_memory_optim()

predictor = create_predictor(config)
input_handle = predictor.get_input_handle(predictor.get_input_names()[0])
output_handles = [
    predictor.get_output_handle(n)
    for n in predictor.get_output_names()
]

# ---------------- video ----------------
cap = cv2.VideoCapture(video_path)

with open(out_csv, "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow([
        "video_id",
        "frame_idx",
        "timestamp_ms",
        "label",
        "text",
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

        timestamp_ms = int(cap.get(cv2.CAP_PROP_POS_MSEC))
        h, w = frame.shape[:2]

        for box in boxes_data:
            x1, y1, x2, y2 = box["bbox"]
            label = box.get("label", "")

            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(w, x2), min(h, y2)

            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue

            crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)

            data = {
                "image": crop,
                "img_path": "frame.jpg"
            }
            data = transform(data, ops)

            inp = data["image"]
            inp = np.expand_dims(inp, axis=0).astype("float32")

            input_handle.reshape(inp.shape)
            input_handle.copy_from_cpu(inp)
            predictor.run()

            preds = [h.copy_to_cpu() for h in output_handles]
            rec_res = post_process(preds)

            text = rec_res[0][0] if rec_res and rec_res[0] else ""

            writer.writerow([
                video_id,
                frame_idx,
                timestamp_ms,
                label,
                text,
                model_name,
                model_version,
                box_layout_version,
            ])

        frame_idx += 1

cap.release()
print(f"wrote {out_csv}")

