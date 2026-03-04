import os
import json
import cv2

# paths
ROOT = r"external/OCR"
BOX_FILE = os.path.join(ROOT, "text_boxes.json")
INPUT_IMAGE_DIR = os.path.join(ROOT, "dataset")
JSON_DIR = os.path.join(ROOT, "ocr_dataset")

# folder where cropped pieces go
OUTPUT_IMAGE_DIR = os.path.join(ROOT, "out_images")
os.makedirs(OUTPUT_IMAGE_DIR, exist_ok=True)

# labels file
LABELS_PATH = os.path.join(ROOT, "labels.jsonl")

NUM_SAMPLES = 5019  # 1..5000

# load box definitions
with open(BOX_FILE, "r", encoding="utf-8") as f:
    box_cfg = json.load(f)["boxes"]


def make_text(label, data):
    hand = data["hand"]
    state = data["state"]
    counts = data["counts"]
    blind = data["blind"]

    if label == "hand_and_level":
        return f'{hand["name"]} lvl.{hand["level"]}'
    elif label == "hands_left":
        return str(state["hands_left"])
    elif label == "discards_left":
        return str(state["discards_left"])
    elif label == "dollars":
        return str(state["dollars"])
    elif label == "ante":
        return str(state["ante"]) + "/8"
    elif label == "round":
        return str(state["round"])
    elif label == "joker_values":
        return f'{counts["jokers"]}/{state["max_jokers"]}'
    elif label == "consumable_values":
        return f'{counts["consumables"]}/{state["consumable_slots"]}'
    elif label == "blind_name":
        return str(blind.get("name") or "")
    elif label == "chips":
        return "*" + str(hand.get("chips") or "")
    elif label.startswith("empty_"):
        return ""
    else:
        raise ValueError(f"unknown label in text_boxes.json: {label}")


with open(LABELS_PATH, "w", encoding="utf-8") as out_f:
    for i in range(1, NUM_SAMPLES + 1):
        img_name = f"{i}.png"
        json_name = f"{i}.json"

        img_path = os.path.join(INPUT_IMAGE_DIR, img_name)
        json_path = os.path.join(JSON_DIR, json_name)

        if not os.path.exists(img_path):
            print(f"missing image: {img_path}, skipping")
            continue
        if not os.path.exists(json_path):
            print(f"missing json: {json_path}, skipping")
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"failed to read image: {img_path}, skipping")
            continue

        with open(json_path, "r", encoding="utf-8") as jf:
            data = json.load(jf)

        for box in box_cfg:
            x1, y1, x2, y2 = box["bbox"]
            label = box["label"]

            # # crop
            crop = img[y1:y2, x1:x2]
            if crop.size == 0:
                print(f"empty crop for {img_name} {label} bbox={box['bbox']}")
                continue

            out_img_name = f"{i}_{label}.png"
            out_img_path = os.path.join(OUTPUT_IMAGE_DIR, out_img_name)

            cv2.imwrite(out_img_path, crop)

            # path used in jsonl, relative (matches your example)
            jsonl_img_path = f"images/{out_img_name}".replace("\\", "/")

            text = make_text(label, data)

            entry = {"image": jsonl_img_path, "text": text}
            out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")

print(f"done. labels written to {LABELS_PATH}")
print(f"cropped images in {OUTPUT_IMAGE_DIR}")
