"""MobileBERT tokenizer + classification head builders for 1.3.

The 128-token max length is mirrored by `WordPieceTokenizer.DEFAULT_MAX_LENGTH`
on the Android side ([WordPieceTokenizer.kt]). Both must move together.
"""

from __future__ import annotations

from jarvis_training.intents import INTENT_ORDER

MODEL_NAME = "google/mobilebert-uncased"

# MUST match android/.../WordPieceTokenizer.kt DEFAULT_MAX_LENGTH (=128).
# Changing this without changing the Android constant silently truncates inputs
# differently in train vs. inference.
MAX_SEQ_LENGTH = 128


def build_tokenizer():
    """Return a HuggingFace fast tokenizer.

    The fast (Rust-backed) tokenizer is the one whose `save_pretrained` emits
    `tokenizer.json` in the format `WordPieceTokenizer.fromTokenizerJson`
    parses on Android.
    """
    from transformers import AutoTokenizer

    return AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=True)


def build_model(num_labels: int = len(INTENT_ORDER)):
    """Return a compiled Keras model wrapping TFMobileBertForSequenceClassification."""
    import tensorflow as tf
    from transformers import TFMobileBertForSequenceClassification

    model = TFMobileBertForSequenceClassification.from_pretrained(
        MODEL_NAME, num_labels=num_labels
    )
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=3e-5),
        loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=[tf.keras.metrics.SparseCategoricalAccuracy(name="accuracy")],
    )
    return model
