"""
CNN model for plant disease classification, built with transfer learning as
described in the paper's methodology:

  "Convolutional neural networks (CNNs) were specifically designed to process
   the photos and detect patterns of disease. The process was made more
   efficient by pooling layers... Fully connected layers analyzed the features
   and classified them into different diseases... pre-trained models like
   MobileNet and ResNet were fine-tuned using the collected plant disease
   dataset."
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import tensorflow as tf
from tensorflow.keras import layers, models

try:
    from src import config
except ImportError:
    import config


def build_model(num_classes: int, backbone: str = None) -> tf.keras.Model:
    """
    Builds a transfer-learning CNN:
      pre-trained backbone (frozen) -> GlobalAveragePooling (pooling layer)
      -> Dense fully-connected layers -> softmax classification head
    """
    backbone = backbone or config.BACKBONE
    input_shape = config.IMG_SIZE + (3,)

    if backbone == "MobileNetV2":
        base_model = tf.keras.applications.MobileNetV2(
            input_shape=input_shape, include_top=False, weights="imagenet"
        )
        preprocess_input = tf.keras.applications.mobilenet_v2.preprocess_input
    elif backbone == "ResNet50":
        base_model = tf.keras.applications.ResNet50(
            input_shape=input_shape, include_top=False, weights="imagenet"
        )
        preprocess_input = tf.keras.applications.resnet50.preprocess_input
    else:
        raise ValueError(f"Unsupported backbone: {backbone}")

    base_model.trainable = False  # freeze pre-trained weights initially

    inputs = layers.Input(shape=input_shape)
    x = preprocess_input(inputs)          # scales pixel values appropriately
    x = base_model(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)  # pooling layer (paper)
    x = layers.Dense(256, activation="relu")(x)  # fully connected layer (paper)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)  # multi-class head

    model = models.Model(inputs, outputs)

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.LEARNING_RATE),
        loss="categorical_crossentropy",   # paper: categorical cross-entropy loss
        metrics=["accuracy", tf.keras.metrics.Precision(name="precision"),
                 tf.keras.metrics.Recall(name="recall")],
    )
    return model, base_model


def unfreeze_for_fine_tuning(model: tf.keras.Model, base_model: tf.keras.Model,
                              fine_tune_at: int = None):
    """Unfreezes the top layers of the backbone for a lower-LR fine-tuning pass."""
    fine_tune_at = fine_tune_at or config.FINE_TUNE_AT
    base_model.trainable = True
    for layer in base_model.layers[:fine_tune_at]:
        layer.trainable = False

    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=config.LEARNING_RATE / 10),
        loss="categorical_crossentropy",
        metrics=["accuracy", tf.keras.metrics.Precision(name="precision"),
                 tf.keras.metrics.Recall(name="recall")],
    )
    return model
