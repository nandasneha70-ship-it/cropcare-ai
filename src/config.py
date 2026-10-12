"""
Central configuration for the Plant Disease Detection System.
Edit paths/hyperparameters here rather than inside the scripts.
"""
import os

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_DIR = os.path.join(BASE_DIR, "data")
TRAIN_DIR = os.path.join(DATA_DIR, "train")   # expects data/train/<class_name>/*.jpg
VAL_DIR = os.path.join(DATA_DIR, "val")       # expects data/val/<class_name>/*.jpg
# If you only have ONE folder of images per class (no manual train/val split),
# set RAW_DIR and use src/split_dataset.py to auto-create train/ and val/ (80/20
# split, matching the paper's methodology).
RAW_DIR = os.path.join(DATA_DIR, "raw")       # expects data/raw/<class_name>/*.jpg

MODELS_DIR = os.path.join(BASE_DIR, "models")
MODEL_PATH = os.path.join(MODELS_DIR, "plant_disease_model.keras")
CLASS_NAMES_PATH = os.path.join(MODELS_DIR, "class_names.json")
HISTORY_PLOT_PATH = os.path.join(MODELS_DIR, "training_history.png")

ORGANIC_SOLUTIONS_PATH = os.path.join(DATA_DIR, "organic_solutions.json")

# ---------------------------------------------------------------------------
# Image / training hyperparameters (mirrors the paper's methodology)
# ---------------------------------------------------------------------------
IMG_SIZE = (224, 224)      # paper: "images were resized to 224x224 pixels"
BATCH_SIZE = 32
EPOCHS = 10                # paper: "Training was conducted over 10 iterations (epochs)"
VALIDATION_SPLIT = 0.2     # paper: "20% for testing and 80% for training"
LEARNING_RATE = 1e-4
BACKBONE = "MobileNetV2"   # paper mentions MobileNet and ResNet; MobileNetV2 is
                            # lightweight enough to fine-tune quickly and matches
                            # the paper's future goal of mobile deployment.
FINE_TUNE_AT = 100         # layer index to start unfreezing for fine-tuning
EARLY_STOPPING_PATIENCE = 3
SEED = 42
