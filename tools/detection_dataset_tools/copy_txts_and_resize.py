import os
import shutil
import cv2


# # copy labels to all images
# label_path = "labels/1.txt"
# image_dir = "images/train"
# label_dir = "labels/train"

# for fname in os.listdir(image_dir):
#     if fname.endswith(".png"):
#         label_name = fname.replace(".png", ".txt")
#         dest = os.path.join(label_dir, label_name)
#         shutil.copy(label_path, dest)

# resize images to 640x360
src_dir = "external/yolo/batch_6"
dst_dir = "external/yolo/balatro_dataset/images/train"
txt_dst_dir = "external/yolo/balatro_dataset/labels/train"
os.makedirs(dst_dir, exist_ok=True)

for f in os.listdir(src_dir):
    if f.endswith(".png"):
        img = cv2.imread(os.path.join(src_dir, f))
        resized = cv2.resize(img, (640, 360))
        cv2.imwrite(os.path.join(dst_dir, f), resized)

for f in os.listdir(src_dir):
    if f.endswith(".txt"):
        shutil.copy(os.path.join(src_dir, f), os.path.join(txt_dst_dir, f))
