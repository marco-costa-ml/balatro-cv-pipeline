# OCR Model

Text recognition model used to extract structured game state from **Balatro gameplay frames**.

The model is trained using **synthetic UI crops generated from gameplay recordings**, allowing consistent recognition of UI text elements across different resolutions and video encodings.

![OCR Example](../assets/synthetic_ocr_example.png)

Example OCR outputs include:

* chip counts
* dollar values
* blind names
* round number
* hand level
* joker values

---

# Training

The OCR model is trained using the PaddleOCR framework.

## 1. Clone PaddleOCR

```bash
git clone https://github.com/PaddlePaddle/PaddleOCR
cd PaddleOCR
pip install -r requirements.txt
```

Recommended version:

```
paddle.__version__ == 3.0.0
```

---

## 2. Train the Recognition Model

Run training using the provided configuration:

```bash
nohup bash -c "
export CUDA_VISIBLE_DEVICES=0
python -m paddle.distributed.launch tools/train.py \
  -c ../assets/en_PP-OCRv4_mobile_rec.yml
" > train.log 2>&1 &
```

Training logs will be written to:

```
train.log
```

---

# Dataset Format

Training data is located in:

```
ocr/data/
```

Label files follow the PaddleOCR recognition format.

Each line contains:

```
image_path<TAB>text_label
```

Example:

```
sample_images/1000_dollars_aug0.png    $25
```

Images are synthetic crops of Balatro UI elements generated from gameplay recordings.

---

# Output

The trained recognition model can be used by the OCR inference scripts located in:

```
scripts/ocr/
```

These scripts support:

* single frame OCR inference
* bulk OCR processing for gameplay videos
* integration with the detection pipeline
