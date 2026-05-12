"""Phase 1.4: convert the Keras checkpoint to 8-bit dynamic-range LiteRT (PTQ).

Fail-closed semantics:
- If the resulting `.tflite` exceeds the size limit (default 30 MB), raise
  `ConvertSizeError`. No metadata is written and nothing is copied to the
  Android assets directory.

Outputs (only on success):
  artifacts/intent_router.tflite              compiled INT8 LiteRT model
  artifacts/model_metadata.json               sidecar with hashes + schema
  android/app/src/main/assets/intent_router.tflite     copy
  android/app/src/main/assets/tokenizer.json           copy of HF tokenizer
  android/app/src/main/assets/model_metadata.json      copy of sidecar

The `intent_order` field in model_metadata.json is derived live from
`jarvis_training.intents.INTENT_ORDER`, so it cannot drift from the Python
schema. The Android side (`Intent.ORDER` in Intent.kt) must continue to match
the same ordinal sequence; the schema_version bumps when it changes.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from pathlib import Path

from jarvis_training.intents import INTENT_ORDER, INTENT_SCHEMA_VERSION

CONVERSION_MODE = "ptq_dynamic_range_int8"
DEFAULT_SIZE_LIMIT_MB = 30.0
MAX_SEQ_LENGTH = 128  # Mirrors train/model.py and Android WordPieceTokenizer.
MODEL_NAME = "google/mobilebert-uncased"


class ConvertSizeError(RuntimeError):
    """Raised when the quantized .tflite exceeds the size budget."""

    def __init__(self, size_mb: float, limit_mb: float) -> None:
        self.size_mb = size_mb
        self.limit_mb = limit_mb
        super().__init__(
            f"Quantized model is {size_mb:.2f} MB; limit is {limit_mb:.2f} MB. "
            "Tune training (smaller hidden size, prune layers) or consider QAT."
        )


@dataclass
class ConvertStats:
    tflite_path: str
    size_mb: float
    tokenizer_hash: str
    training_data_hash: str
    conversion_mode: str = CONVERSION_MODE
    schema_version: str = INTENT_SCHEMA_VERSION
    metadata_path: str = ""
    android_assets_dir: str = ""

    def as_dict(self) -> dict:
        return asdict(self)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _build_metadata(
    *,
    tokenizer_hash: str,
    training_data_hash: str,
    size_mb: float,
) -> dict:
    return {
        "schema_version": INTENT_SCHEMA_VERSION,
        "intent_order": [i.value for i in INTENT_ORDER],
        "tokenizer_hash": tokenizer_hash,
        "training_data_hash": training_data_hash,
        "conversion_mode": CONVERSION_MODE,
        "size_mb": round(size_mb, 4),
        "max_seq_length": MAX_SEQ_LENGTH,
        "model_name": MODEL_NAME,
    }


def _convert_keras_to_litert_int8(keras_path: Path, out_path: Path) -> None:
    """Run 8-bit dynamic-range PTQ on the Keras model and write a .tflite.

    The brief specifies `ai-edge-litert`. The exact converter symbol varies
    between releases of that package; we try a couple of well-known entry
    points and fall back to TF's built-in TFLiteConverter for dynamic-range
    quantization, which is functionally equivalent.
    """
    import tensorflow as tf

    model = tf.keras.models.load_model(keras_path)

    # Preferred path: ai-edge-litert. Try the most-recent published API first,
    # then older variants. We keep these in try/except because the package's
    # surface has changed across versions; the underlying behaviour we ask for
    # (DEFAULT optimizations = dynamic-range INT8) is stable.
    try:
        from ai_edge_litert import convert as litert_convert  # type: ignore

        if hasattr(litert_convert, "from_keras_model"):
            converter = litert_convert.from_keras_model(model)
        else:
            converter = litert_convert.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_bytes = converter.convert()
    except Exception:
        converter = tf.lite.TFLiteConverter.from_keras_model(model)
        converter.optimizations = [tf.lite.Optimize.DEFAULT]
        tflite_bytes = converter.convert()

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(tflite_bytes)


def convert(
    keras_path: Path,
    tokenizer_path: Path,
    data_path: Path,
    artifacts_dir: Path,
    android_assets_dir: Path,
    *,
    size_limit_mb: float = DEFAULT_SIZE_LIMIT_MB,
) -> ConvertStats:
    """Quantize the Keras checkpoint and stage all four assets for Android."""
    keras_path = Path(keras_path)
    tokenizer_path = Path(tokenizer_path)
    data_path = Path(data_path)
    artifacts_dir = Path(artifacts_dir)
    android_assets_dir = Path(android_assets_dir)

    if not keras_path.exists():
        raise FileNotFoundError(f"Keras checkpoint not found: {keras_path}")
    if not tokenizer_path.exists():
        raise FileNotFoundError(f"tokenizer.json not found: {tokenizer_path}")
    if not data_path.exists():
        raise FileNotFoundError(f"intents.jsonl not found: {data_path}")

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    tflite_path = artifacts_dir / "intent_router.tflite"

    _convert_keras_to_litert_int8(keras_path, tflite_path)

    size_mb = tflite_path.stat().st_size / (1024 * 1024)
    if size_mb >= size_limit_mb:
        # Fail closed: leave the .tflite on disk for inspection but DO NOT
        # write metadata or copy to assets — those would imply approval.
        raise ConvertSizeError(size_mb, size_limit_mb)

    tokenizer_hash = _sha256_hex(tokenizer_path.read_bytes())
    training_data_hash = _sha256_hex(data_path.read_bytes())

    metadata = _build_metadata(
        tokenizer_hash=tokenizer_hash,
        training_data_hash=training_data_hash,
        size_mb=size_mb,
    )
    metadata_path = artifacts_dir / "model_metadata.json"
    metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    android_assets_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(tflite_path, android_assets_dir / "intent_router.tflite")
    shutil.copy2(tokenizer_path, android_assets_dir / "tokenizer.json")
    shutil.copy2(metadata_path, android_assets_dir / "model_metadata.json")

    return ConvertStats(
        tflite_path=str(tflite_path),
        size_mb=size_mb,
        tokenizer_hash=tokenizer_hash,
        training_data_hash=training_data_hash,
        metadata_path=str(metadata_path),
        android_assets_dir=str(android_assets_dir),
    )
