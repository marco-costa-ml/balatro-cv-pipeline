
from ultralytics import YOLO

model = YOLO("yolov8n.pt")
model.train(
    data="external/balatro_dataset/data.yaml",
    epochs=300,
    patience=20,
    imgsz=640,
    batch=64,
    device=0  # DDP will override this
)