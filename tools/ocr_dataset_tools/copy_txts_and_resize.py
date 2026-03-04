import os
import cv2

src_dir = "external/OCR/ocr_dataset"
dst_dir = "external/OCR/dataset"
os.makedirs(dst_dir, exist_ok=True)

pngs = sorted([f for f in os.listdir(src_dir) if f.endswith(".png")])

for i, f in enumerate(pngs):
    # if i % 3 != 0:
    #     continue
    img = cv2.imread(os.path.join(src_dir, f))
    resized = cv2.resize(img, (640, 360))
    cv2.imwrite(os.path.join(dst_dir, f), resized)
