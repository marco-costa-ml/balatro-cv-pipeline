import cv2
import json
import os

img_path = r'C:\Users\Marco\Desktop\OCR\ocr_dataset\1000.png'
label_path = r'C:\Users\Marco\Desktop\OCR\text_boxes.json'

# load image
img = cv2.imread(img_path)
if img is None:
    raise FileNotFoundError(f"Image not found: {img_path}")

H, W = img.shape[:2]       # target resolution (2560x1440)

# original label space (360p assumed)
orig_W = 640
orig_H = 360

scale_x = W / orig_W
scale_y = H / orig_H

# load json
with open(label_path, 'r') as f:
    data = json.load(f)

for item in data["boxes"]:
    x1, y1, x2, y2 = item["bbox"]
    label = item["label"]

    x1 = int(x1 * scale_x)
    y1 = int(y1 * scale_y)
    x2 = int(x2 * scale_x)
    y2 = int(y2 * scale_y)

    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    cv2.putText(img, label, (x1, y1 - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# save
out_path = 'external/OCR/ocr_example_2.png'
cv2.imwrite(out_path, img)
print("saved:", out_path)
