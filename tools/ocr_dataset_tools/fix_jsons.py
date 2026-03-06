import glob
import json
import re
import os

json_dir = r"external\OCR\ocr_dataset"

json_files = glob.glob(os.path.join(json_dir, "*.json"))

fixed = 0

for path in json_files:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()

    try:
        json.loads(raw)
        continue  # already valid
    except json.JSONDecodeError:
        pass

    # fix patterns like: "empty_1":,
    raw_fixed = re.sub(
        r'"(empty_\d+)"\s*:\s*(?=[,}])',
        r'"\1": null',
        raw
    )

    try:
        data = json.loads(raw_fixed)
    except json.JSONDecodeError:
        print("still broken:", path)
        continue

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    fixed += 1
    print("fixed:", os.path.basename(path))

print("done. fixed", fixed, "files")
