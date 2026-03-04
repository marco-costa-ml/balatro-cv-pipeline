
from pathlib import Path
import json
import pandas as pd
import os
import logging
import cv2

SEAL_OFFSET = (-25, -60)
STICKER_OFFSETS = {
    'eternal': (-65, -110),
    'perishable': (-65, -110),
    'rental': (-65, -45)
}

# setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

# config
IMAGE_WIDTH, IMAGE_HEIGHT = 2560, 1440
PX_SCALE = 112
CENTER_X, CENTER_Y = IMAGE_WIDTH / 2, IMAGE_HEIGHT / 2

# bbox sizes (w, h) in px
SIZES = {
    'card': (210, 290),
    'joker': (210, 290),
    'consumable': (210, 290),
    'booster': (220, 370),
    'tag': (80, 80),
    'voucher': (185, 280),
    'seal': (85, 85),
    'edition': {'foil': (210, 290), 'holo': (210, 290), 'negative': (210, 290)},
    'eternal': (55, 55),
    'perishable': (55, 55),
    'rental': (55, 55),
    'stake_white': (55, 55),
    'stake_gold': (55, 55),
    'card_back': (240, 306)
}

SEAL_OFFSET = (-25, -60)
STICKER_OFFSETS = {
    'eternal': (-65, -110),
    'perishable': (-65, -110),
    'rental': (-65, -45)
}


# NON SELECTED, CRT MAX
# HARDCODED_OBJECTS = [
#     {"x": -7.598214, "y": -1.258929, "class": "stake_white"},
#     {"x": -7.700893, "y": -3.294643, "class": "stake_white"}
# ]
# FIXED_LAST_8 = [
#     (-4.241071, 2.593750), (-2.700893, 2.522321), (-1.232143, 2.508929), (0.196429, 2.464286),
#     (1.772321, 2.437500), (3.098214, 2.446429), (4.674107, 2.500000), (6.200893, 2.629464)
# ]

# 4 SELECTED: _ _ I _ I _ I I 
# HARDCODED_OBJECTS = [
#     {"x": -7.754464, "y": -3.147321, "class": "stake_white"},
#     {"x": -7.593750, "y": -1.276786, "class": "stake_white"}
# ]

# FIXED_LAST_8 = [
#     (-4.258929, 2.607143), (-2.718750, 2.620536), (-1.209821, 1.991071), (0.254464, 2.446429),
#     (1.803571, 1.839286), (3.290179, 2.513393), (4.714286, 2.013393), (6.223214, 2.066964)
# ]

# NON SELECTED, CRT 0
HARDCODED_OBJECTS = [
    {"x": -7.754464, "y": -3.347321, "class": "stake_gold"},
    {"x": -7.593750, "y": -1.276786, "class": "stake_gold"}
]

FIXED_LAST_8 = [
    (-4.258929, 2.607143), (-2.718750, 2.520536), (-1.209821, 2.56071), (0.254464, 2.446429),
    (1.803571, 2.539286), (3.290179, 2.513393), (4.714286, 2.513393), (6.223214, 2.666964)
]

DATA_DIR = Path(r"C:\Users\Marco\Desktop\yolo")
#DATA_DIR = Path(r"C:\Users\Marco\Desktop\yolo\batch_2")

class_df = pd.read_csv(DATA_DIR / 'yolo_classes.csv', header=None, names=["id", "name"])
class_map = dict(zip(class_df["name"], class_df["id"]))

output = []
skipped = []

def card_name(rank, suit):
    r = rank.lower() if rank.isalpha() else rank
    s = suit.lower()
    return f"{r}_{s}"

def to_pixel_coords(x_off, y_off):
    x = CENTER_X + x_off * PX_SCALE
    y = CENTER_Y + y_off * PX_SCALE
    return x, y

def yolo_bbox(xc, yc, w, h):
    return xc / IMAGE_WIDTH, yc / IMAGE_HEIGHT, w / IMAGE_WIDTH, h / IMAGE_HEIGHT

def add_bbox(cls, x, y, w, h):
    if cls.startswith("p_"):
        cls = cls[:-2]
    if cls not in class_map:
        skipped.append(cls)
        logging.info(f"skipping: class '{cls}' not in class_map")
        return

    cx, cy = to_pixel_coords(x, y)

    # convert to top-left (x1, y1) and bottom-right (x2, y2)
    x1 = cx - w / 2
    y1 = cy - h / 2
    x2 = cx + w / 2
    y2 = cy + h / 2

    # check if completely out of frame
    if x2 < 0 or y2 < 0 or x1 > IMAGE_WIDTH or y1 > IMAGE_HEIGHT:
        logging.info(f"skipping: bbox for '{cls}' is fully out of frame")
        return

    # clamp to image bounds
    x1 = max(0, min(IMAGE_WIDTH, x1))
    y1 = max(0, min(IMAGE_HEIGHT, y1))
    x2 = max(0, min(IMAGE_WIDTH, x2))
    y2 = max(0, min(IMAGE_HEIGHT, y2))

    # recompute center and size
    clamped_cx = (x1 + x2) / 2
    clamped_cy = (y1 + y2) / 2
    clamped_w = x2 - x1
    clamped_h = y2 - y1

    norm = yolo_bbox(clamped_cx, clamped_cy, clamped_w, clamped_h)
    output.append(f"{class_map[cls]} {' '.join(map(str, norm))}")


def process_file(json_path, png_path):
    global output, skipped
    with open(json_path) as f:
        data = json.load(f)

    cards = data['cards']
    output = []
    skipped = []
    card_back_class = cards[0]['card_back']

    for card in cards:
        x, y = card['x'], card['y']
        is_facedown = card.get('debuff') == 'facedown'
        is_mstone = card.get('enhancement') == 'm_stone'

        if x is not None and y is not None:
            if is_facedown:
                add_bbox('facedown', x, y, *SIZES['card'])
                continue

            if is_mstone:
                add_bbox('m_stone', x, y, *SIZES['card'])
                if card.get('edition') in SIZES['edition']:
                    add_bbox(f"e_{card['edition']}", x, y, *SIZES['edition'][card['edition']])
                if card.get('seal'):
                    seal_cls = f"{card['seal'].lower()}_seal"
                    sx, sy = x + SEAL_OFFSET[0]/PX_SCALE, y + SEAL_OFFSET[1]/PX_SCALE
                    add_bbox(seal_cls, sx, sy, *SIZES['seal'])
                continue

            if card.get('joker'):
                add_bbox(card['joker'], x, y, *SIZES['joker'])
            elif card.get('consumable'):
                add_bbox(card['consumable'], x, y, *SIZES['consumable'])
            elif card.get('booster'):
                add_bbox(card['booster'], x, y, *SIZES['booster'])
            elif card.get('tag'):
                add_bbox(card['tag'], x, y, *SIZES['tag'])
            elif card.get('voucher'):
                add_bbox(card['voucher'], x, y, *SIZES['voucher'])
            elif card.get('suit') and card.get('rank'):
                add_bbox(card_name(card['rank'], card['suit']), x, y, *SIZES['card'])

            if card.get('edition') in SIZES['edition']:
                add_bbox(f"e_{card['edition']}", x, y, *SIZES['edition'][card['edition']])

            if card.get('enhancement'):
                add_bbox(card['enhancement'], x, y, *SIZES['card'])

            if card.get('seal'):
                seal_cls = f"{card['seal'].lower()}_seal"
                sx, sy = x + SEAL_OFFSET[0]/PX_SCALE, y + SEAL_OFFSET[1]/PX_SCALE
                add_bbox(seal_cls, sx, sy, *SIZES['seal'])

            for sticker in ['eternal', 'perishable', 'rental']:
                if card.get(sticker):
                    dx, dy = STICKER_OFFSETS[sticker]
                    sx, sy = x + dx/PX_SCALE, y + dy/PX_SCALE
                    add_bbox(sticker, sx, sy, *SIZES[sticker])

            if card.get('debuff') == 'debuffed':
                add_bbox('debuffed', x, y, *SIZES['card'])

    for (x, y), card in zip(FIXED_LAST_8, cards[-8:]):
        if card.get('debuff') == 'facedown':
            add_bbox('facedown', x, y, *SIZES['card'])
            continue
        if card.get('enhancement') == 'm_stone':
            add_bbox('m_stone', x, y, *SIZES['card'])
            if card.get('edition') in SIZES['edition']:
                add_bbox(f"e_{card['edition']}", x, y, *SIZES['edition'][card['edition']])
            if card.get('seal'):
                seal_cls = f"{card['seal'].lower()}_seal"
                sx, sy = x + SEAL_OFFSET[0]/PX_SCALE, y + SEAL_OFFSET[1]/PX_SCALE
                add_bbox(seal_cls, sx, sy, *SIZES['seal'])
            continue
        if card.get('suit') and card.get('rank'):
            add_bbox(card_name(card['rank'], card['suit']), x, y, *SIZES['card'])
        if card.get('edition') in SIZES['edition']:
            add_bbox(f"e_{card['edition']}", x, y, *SIZES['edition'][card['edition']])
        if card.get('enhancement'):
            add_bbox(card['enhancement'], x, y, *SIZES['card'])
        if card.get('seal'):
            seal_cls = f"{card['seal'].lower()}_seal"
            sx, sy = x + SEAL_OFFSET[0]/PX_SCALE, y + SEAL_OFFSET[1]/PX_SCALE
            add_bbox(seal_cls, sx, sy, *SIZES['seal'])
        for sticker in ['eternal', 'perishable', 'rental']:
            if card.get(sticker):
                dx, dy = STICKER_OFFSETS[sticker]
                sx, sy = x + dx/PX_SCALE, y + dy/PX_SCALE
                add_bbox(sticker, sx, sy, *SIZES[sticker])
        if card.get('debuff') == 'debuffed':
            add_bbox('debuffed', x, y, *SIZES['card'])

    for obj in HARDCODED_OBJECTS:
        add_bbox(obj['class'], obj['x'], obj['y'], *SIZES[obj['class']])
    add_bbox(card_back_class, 8.419643, 4.294643, *SIZES['card_back'])

    with open(json_path.with_suffix('.txt'), 'w') as f:
        for line in output:
            f.write(line + '\n')

    img = cv2.imread(str(png_path))
    h, w = img.shape[:2]
    for line in output:
        parts = line.strip().split()
        class_id, cx, cy, bw, bh = int(parts[0]), *map(float, parts[1:])
        x = int((cx - bw / 2) * w)
        y = int((cy - bh / 2) * h)
        box_w = int(bw * w)
        box_h = int(bh * h)
        cv2.rectangle(img, (x, y), (x + box_w, y + box_h), (0, 255, 0), 2)
        cv2.putText(img, str(class_id), (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

    cv2.imwrite(str(json_path.with_suffix('.preview.png')), img)
    print(f"Processed {json_path.name} → {json_path.with_suffix('.txt').name}")

# run batch
for json_file in DATA_DIR.glob("*.json"):
    img_file = json_file.with_suffix('.png')
    if img_file.exists():
        process_file(json_file, img_file)
