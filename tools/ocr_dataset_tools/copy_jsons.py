import json
import csv
import glob
import os

# folder where your json files are
json_dir = "external/OCR/ocr_dataset/"
out_csv = os.path.join(json_dir, "labels.csv")

# columns we will output
fieldnames = [
    "filename",
    "hand_name",
    "hand_level",
    "dollars",
    "blind_name",
    "discards_left",
    "hands_left",
    "round",
    "ante",
    "max_jokers",
    "consumable_slots",
    "jokers_count",
    "consumables_count",
    "empty_1",
    "empty_2",
    "empty_3",
]


json_files = glob.glob(os.path.join(json_dir, "*.json"))

with open(out_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for path in json_files:
        with open(path, "r", encoding="utf-8") as jf:
            data = json.load(jf)

        row = {
            "filename": os.path.basename(path),
            "hand_name":        data["hand"]["name"],
            "hand_level":       data["hand"]["level"],
            "dollars":          data["state"]["dollars"],
            "blind_name":       data["blind"]["name"],
            "discards_left":    data["state"]["discards_left"],
            "hands_left":       data["state"]["hands_left"],
            "round":            data["state"]["round"],
            "ante":             data["state"]["ante"],
            "max_jokers":       data["state"]["max_jokers"],
            "consumable_slots": data["state"]["consumable_slots"],
            "jokers_count":     data["counts"]["jokers"],
            "consumables_count": data["counts"]["consumables"],
            "empty_1": "",
            "empty_2": "",
            "empty_3": "",
        }

        writer.writerow(row)

print(f"wrote {len(json_files)} rows to {out_csv}")
