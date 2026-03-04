import cv2
import os

img_path = "external/yolo/batch_2/1.png"

img = cv2.imread(img_path)
h, w = img.shape[:2]
boxes = []
drawing = False
start = (0, 0)

def mouse(event, x, y, flags, param):
    global start, drawing, boxes, img

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        start = (x, y)
    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        end = (x, y)
        x1, y1 = start
        x2, y2 = end
        cv2.rectangle(img, start, end, (0, 255, 0), 2)
        cx = ((x1 + x2) / 2) / w
        cy = ((y1 + y2) / 2) / h
        bw = abs(x2 - x1) / w
        bh = abs(y2 - y1) / h
        boxes.append((0, cx, cy, bw, bh))

cv2.namedWindow("Label")
cv2.setMouseCallback("Label", mouse)

while True:
    cv2.imshow("Label", img)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()

# save to label file
label_path = img_path.replace(".png", ".txt")
with open(label_path, "w") as f:
    for b in boxes:
        f.write(" ".join(map(str, b)) + "\n")
