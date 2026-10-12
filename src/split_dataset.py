"""
Splits data/raw/<class_name>/*.jpg into data/train/<class_name>/ and
data/val/<class_name>/ using an 80/20 split, matching the paper's methodology:
"The dataset was divided into two portions: 20% for testing and 80% for
training the model."

Run this ONCE before training if your images are not already split:
    python src/split_dataset.py
"""
import os
import random
import shutil
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

try:
    from src import config
except ImportError:
    import config


def split_dataset():
    random.seed(config.SEED)

    if not os.path.isdir(config.RAW_DIR):
        raise FileNotFoundError(
            f"Raw data folder not found at '{config.RAW_DIR}'.\n"
            "Place your images like:\n"
            "  data/raw/Tomato___Septoria_leaf_spot/img1.jpg\n"
            "  data/raw/Tomato___healthy/img2.jpg\n"
            "  ... one sub-folder per class ..."
        )

    class_names = sorted(
        d for d in os.listdir(config.RAW_DIR)
        if os.path.isdir(os.path.join(config.RAW_DIR, d))
    )
    if not class_names:
        raise ValueError(f"No class sub-folders found inside {config.RAW_DIR}")

    os.makedirs(config.TRAIN_DIR, exist_ok=True)
    os.makedirs(config.VAL_DIR, exist_ok=True)

    total_train, total_val = 0, 0
    for class_name in class_names:
        src_dir = os.path.join(config.RAW_DIR, class_name)
        images = [
            f for f in os.listdir(src_dir)
            if f.lower().endswith((".jpg", ".jpeg", ".png"))
        ]
        random.shuffle(images)

        split_idx = int(len(images) * (1 - config.VALIDATION_SPLIT))
        train_imgs, val_imgs = images[:split_idx], images[split_idx:]

        train_out = os.path.join(config.TRAIN_DIR, class_name)
        val_out = os.path.join(config.VAL_DIR, class_name)
        os.makedirs(train_out, exist_ok=True)
        os.makedirs(val_out, exist_ok=True)

        for f in train_imgs:
            shutil.copy2(os.path.join(src_dir, f), os.path.join(train_out, f))
        for f in val_imgs:
            shutil.copy2(os.path.join(src_dir, f), os.path.join(val_out, f))

        total_train += len(train_imgs)
        total_val += len(val_imgs)
        print(f"{class_name:45s} -> train: {len(train_imgs):4d}  val: {len(val_imgs):4d}")

    print(f"\nDone. Total train images: {total_train}, total val images: {total_val}")
    print(f"Train dir: {config.TRAIN_DIR}")
    print(f"Val dir:   {config.VAL_DIR}")


if __name__ == "__main__":
    split_dataset()
