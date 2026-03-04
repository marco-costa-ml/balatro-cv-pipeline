import os
import sys
import json
import csv
import cv2
import numpy as np
from pathlib import Path
import multiprocessing as mp


VIDEO_DIR = Path("../data_local/videos/")
BOXES_PATH = Path("../assets/text_boxes.json")

CONFIG_PATH = "../ocr/en_PP-OCRv4_mobile_rec.yml"
MODEL_PATH = "external/ocr/PaddleOCR/inference/rec_infer_custom/inference"

FRAME_STRIDE = 100000
NUM_GPUS = 8

SHARD_DIR = Path("broad_ocr_sampling_shards")
FINAL_CSV = Path("broad_ocr_sampling.csv")


def worker(gpu_id, video_list):
    os.environ["CUDA_VISIBLE_DEVICES"] = str(gpu_id)
    os.environ["OMP_NUM_THREADS"] = "4"

    sys.path.insert(0, "external/ocr/PaddleOCR")

    from paddle.inference import Config, create_predictor
    from tools.program import load_config
    from ppocr.data import create_operators, transform
    from ppocr.postprocess import build_post_process

    with open(BOXES_PATH, "r") as f:
        boxes = json.load(f)["boxes"]

    cfg = load_config(CONFIG_PATH)

    bad = {
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
        if isinstance(t, dict) and not any(k in t for k in bad)
    ]

    ops = create_operators(cfg["Eval"]["dataset"]["transforms"], cfg["Global"])
    post = build_post_process(cfg["PostProcess"], cfg["Global"])

    config = Config(MODEL_PATH + ".pdmodel", MODEL_PATH + ".pdiparams")
    config.enable_use_gpu(100, 0)
    config.switch_ir_optim(True)
    config.enable_memory_optim()

    predictor = create_predictor(config)
    input_handle = predictor.get_input_handle(predictor.get_input_names()[0])
    output_handles = [predictor.get_output_handle(n) for n in predictor.get_output_names()]

    SHARD_DIR.mkdir(parents=True, exist_ok=True)

    for video_path in video_list:
        shard_csv = SHARD_DIR / f"{video_path.name}.csv"

        done = set()
        if shard_csv.exists():
            with open(shard_csv, "r") as f:
                r = csv.DictReader(f)
                for row in r:
                    done.add(int(row["frame_idx"]))

        write_header = not shard_csv.exists()
        f_out = open(shard_csv, "a", newline="")
        w = csv.writer(f_out)
        if write_header:
            w.writerow(["video", "frame_idx", "timestamp_ms", "label", "text"])

        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            f_out.close()
            continue

        fps = cap.get(cv2.CAP_PROP_FPS)
        if not fps or fps <= 0:
            fps = 60.0

        frame_idx = 0

        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_idx % FRAME_STRIDE == 0:
                if frame_idx in done:
                    frame_idx += 1
                    continue

                timestamp_ms = int(frame_idx * 1000.0 / fps)
                h_vid, w_vid = frame.shape[:2]

                for box in boxes:
                    label = box["label"]
                    x1, y1, x2, y2 = box["bbox"]

                    x1 = max(0, x1)
                    y1 = max(0, y1)
                    x2 = min(w_vid, x2)
                    y2 = min(h_vid, y2)

                    crop = frame[y1:y2, x1:x2]
                    if crop.size == 0:
                        continue

                    crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
                    data = {"image": crop, "img_path": "frame.jpg"}
                    data = transform(data, ops)

                    inp = np.expand_dims(data["image"], axis=0).astype("float32")

                    input_handle.reshape(inp.shape)
                    input_handle.copy_from_cpu(inp)
                    predictor.run()

                    preds = [h.copy_to_cpu() for h in output_handles]
                    rec = post(preds)
                    text = rec[0][0] if rec and rec[0] else ""

                    w.writerow([video_path.name, frame_idx, timestamp_ms, label, text])

                f_out.flush()
                done.add(frame_idx)

            frame_idx += 1

        cap.release()
        f_out.close()
        print(f"gpu{gpu_id} done {video_path.name}")


def merge():
    shards = sorted(SHARD_DIR.glob("*.csv"))
    with open(FINAL_CSV, "w", newline="") as out_f:
        w = csv.writer(out_f)
        w.writerow(["video", "frame_idx", "timestamp_ms", "label", "text"])
        for shard in shards:
            with open(shard, "r") as in_f:
                r = csv.reader(in_f)
                next(r, None)
                for row in r:
                    w.writerow(row)


def main():
    videos = sorted(VIDEO_DIR.glob("*.mp4"))
    chunks = [videos[i::NUM_GPUS] for i in range(NUM_GPUS)]

    procs = []
    for gpu_id in range(NUM_GPUS):
        p = mp.Process(target=worker, args=(gpu_id, chunks[gpu_id]))
        p.start()
        procs.append(p)

    for p in procs:
        p.join()

    merge()
    print("done.")


if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    main()
