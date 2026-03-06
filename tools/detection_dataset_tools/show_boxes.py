import cv2
import os

# absolute paths
img_path = r'external\yolo\balatro_dataset\images\train\12697.png'
label_path = r'external\yolo\balatro_dataset\labels\train\12697.txt'

# load image
img = cv2.imread(img_path)
if img is None:
    raise FileNotFoundError(f"Image not found: {img_path}")
h, w = img.shape[:2]

# load labels
if not os.path.exists(label_path):
    raise FileNotFoundError(f"Label file not found: {label_path}")

with open(label_path, 'r') as f:
    for line in f:
        parts = line.strip().split()
        class_id, cx, cy, bw, bh = int(parts[0]), *map(float, parts[1:])
        x = int((cx - bw / 2) * w)
        y = int((cy - bh / 2) * h)
        box_w = int(bw * w)
        box_h = int(bh * h)

        cv2.rectangle(img, (x, y), (x + box_w, y + box_h), (0, 255, 0), 2)
        cv2.putText(img, str(class_id), (x, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

# display
cv2.imshow('YOLO BBoxes', img)
cv2.waitKey(0)
cv2.destroyAllWindows()
