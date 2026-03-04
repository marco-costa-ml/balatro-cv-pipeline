import cv2
import os
import json

img_path = "external/OCR/images/1.png"
output_path = "external/OCR/"

img = cv2.imread(img_path)
clone = img.copy()
boxes = []
drawing = False
start = None

def mouse(event, x, y, flags, param):
    global start, drawing, boxes, img, clone

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start = (x, y)

    elif event == cv2.EVENT_MOUSEMOVE and drawing:
        # show live box while dragging
        img[:] = clone.copy()
        cv2.rectangle(img, start, (x, y), (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        x1, y1 = start
        x2, y2 = x, y

        # normalize coords (top-left, bottom-right)
        x1, x2 = sorted([x1, x2])
        y1, y2 = sorted([y1, y2])

        cv2.rectangle(clone, (x1, y1), (x2, y2), (0, 255, 0), 2)
        img[:] = clone.copy()

        text = input(f"label for box {x1,y1,x2,y2}: ").strip()
        if text:
            boxes.append({
                "bbox": [x1, y1, x2, y2],
                "label": text
            })

cv2.namedWindow("label")
cv2.setMouseCallback("label", mouse)

while True:
    cv2.imshow("label", img)
    key = cv2.waitKey(1) & 0xFF
    if key == ord('q'):
        break

cv2.destroyAllWindows()

# save annotations next to image
label_path = output_path + "text_boxes_backup.json"
with open(label_path, "w", encoding="utf-8") as f:
    json.dump({"boxes": boxes}, f, ensure_ascii=False, indent=2)

print(f"saved {len(boxes)} boxes to {label_path}")