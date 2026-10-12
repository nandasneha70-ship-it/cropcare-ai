"""
Trains the plant disease detection CNN.

Usage:
    python src/train.py

Expects:
    data/train/<class_name>/*.jpg
    data/val/<class_name>/*.jpg
(Run split_dataset.py first if you only have data/raw/.)

Implements the methodology described in the paper:
  - Images resized to 224x224, pixel values scaled 0-1 (handled by backbone preprocess)
  - Data augmentation: rotation, flip, zoom, crop -> "helped get past the
    problem of inadequate data"
  - Adam optimizer, categorical cross-entropy loss
  - 10 epochs with early stopping if no improvement
  - Reports accuracy, precision, recall after training
"""
import json
import os
import sys
import time

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from PIL import Image
import tensorflow as tf
from tensorflow.keras.preprocessing.image import ImageDataGenerator

try:
    from src import config
    from src.model import build_model, unfreeze_for_fine_tuning
except ImportError:
    import config
    from model import build_model, unfreeze_for_fine_tuning

# Robust image loader wrapper to gracefully handle OneDrive hydration/read glitches
try:
    from keras.src.utils import image_utils
    _orig_load_img = image_utils.load_img

    def _safe_load_img(path, *args, **kwargs):
        for attempt in range(3):
            try:
                return _orig_load_img(path, *args, **kwargs)
            except OSError as e:
                if attempt == 2:
                    print(f"\n[Warning] Transient I/O error on {path}: {e}. Using fallback image.")
                    target_size = kwargs.get("target_size") or config.IMG_SIZE
                    return Image.new("RGB", (target_size[1], target_size[0]), (0, 0, 0))
                time.sleep(0.3)

    image_utils.load_img = _safe_load_img
    tf.keras.utils.load_img = _safe_load_img
    tf.keras.preprocessing.image.load_img = _safe_load_img
except Exception:
    pass


def get_data_generators():
    train_datagen = ImageDataGenerator(
        rotation_range=30,
        width_shift_range=0.2,
        height_shift_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        shear_range=0.1,
        fill_mode="nearest",
    )
    val_datagen = ImageDataGenerator()  # no augmentation on validation data

    # Strictly ensure train and val share the exact same classes and index mapping
    class_names = sorted(
        d for d in os.listdir(config.TRAIN_DIR)
        if os.path.isdir(os.path.join(config.TRAIN_DIR, d))
    )

    train_gen = train_datagen.flow_from_directory(
        config.TRAIN_DIR,
        classes=class_names,
        target_size=config.IMG_SIZE,
        batch_size=config.BATCH_SIZE,
        class_mode="categorical",
        seed=config.SEED,
    )
    val_gen = val_datagen.flow_from_directory(
        config.VAL_DIR,
        classes=class_names,
        target_size=config.IMG_SIZE,
        batch_size=config.BATCH_SIZE,
        class_mode="categorical",
        shuffle=False,
        seed=config.SEED,
    )
    return train_gen, val_gen, class_names


def plot_history(history, fine_tune_history=None):
    acc = history.history["accuracy"]
    val_acc = history.history["val_accuracy"]
    loss = history.history["loss"]
    val_loss = history.history["val_loss"]

    if fine_tune_history is not None:
        acc += fine_tune_history.history["accuracy"]
        val_acc += fine_tune_history.history["val_accuracy"]
        loss += fine_tune_history.history["loss"]
        val_loss += fine_tune_history.history["val_loss"]

    epochs_range = range(1, len(acc) + 1)

    plt.figure(figsize=(12, 5))
    plt.subplot(1, 2, 1)
    plt.plot(epochs_range, acc, label="Training Accuracy")
    plt.plot(epochs_range, val_acc, label="Validation Accuracy")
    plt.legend(loc="lower right")
    plt.title("Training vs Validation Accuracy")
    plt.xlabel("Epoch")
    plt.ylabel("Accuracy")

    plt.subplot(1, 2, 2)
    plt.plot(epochs_range, loss, label="Training Loss")
    plt.plot(epochs_range, val_loss, label="Validation Loss")
    plt.legend(loc="upper right")
    plt.title("Training vs Validation Loss")
    plt.xlabel("Epoch")
    plt.ylabel("Loss")

    plt.tight_layout()
    plt.savefig(config.HISTORY_PLOT_PATH)
    print(f"Saved training history plot to {config.HISTORY_PLOT_PATH}")


def main():
    os.makedirs(config.MODELS_DIR, exist_ok=True)

    train_gen, val_gen, class_names = get_data_generators()
    num_classes = len(class_names)

    with open(config.CLASS_NAMES_PATH, "w") as f:
        json.dump(class_names, f, indent=2)
    print(f"Found {num_classes} classes. Saved class names to {config.CLASS_NAMES_PATH}")

    model, base_model = build_model(num_classes)
    model.summary()

    callbacks = [
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=config.EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
        ),
        tf.keras.callbacks.ModelCheckpoint(
            config.MODEL_PATH, monitor="val_accuracy", save_best_only=True
        ),
    ]

    print("\n--- Phase 1: training classification head (backbone frozen) ---")
    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=config.EPOCHS,
        callbacks=callbacks,
    )

    print("\n--- Phase 2: fine-tuning top backbone layers ---")
    model = unfreeze_for_fine_tuning(model, base_model)
    fine_tune_history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=config.EPOCHS,
        callbacks=callbacks,
    )

    model.save(config.MODEL_PATH)
    print(f"\nFinal model saved to {config.MODEL_PATH}")

    print("\n--- Final evaluation on validation set ---")
    results = model.evaluate(val_gen)
    for name, value in zip(model.metrics_names, results):
        print(f"{name}: {value:.4f}")

    plot_history(history, fine_tune_history)


if __name__ == "__main__":
    main()
