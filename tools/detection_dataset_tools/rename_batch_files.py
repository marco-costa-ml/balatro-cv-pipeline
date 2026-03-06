import os
import re

folder = r"external\yolo\batch_3"
prefix = "batch3_"

for filename in os.listdir(folder):
    filepath = os.path.join(folder, filename)
    if not os.path.isfile(filepath):
        continue

    name, ext = os.path.splitext(filename)

    # clean up any existing prefixes like batch1_, batch2_, etc.
    cleaned = re.sub(r'(batch\d+_)+', '', name)

    new_name = f"{prefix}{cleaned}{ext}"
    new_path = os.path.join(folder, new_name)
    os.rename(filepath, new_path)
    print(f"{filename} → {new_name}")
