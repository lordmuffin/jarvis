"""Phase 1.3 entry point: fine-tune MobileBERT on `data/clean/intents.jsonl`.

Fail-closed semantics:
- If any class's validation accuracy is below `min_per_class_val_acc`, we raise
  `TrainingGateError` and write NO checkpoint. The downstream `make convert`
  then fails fast at "missing keras file" rather than emitting a weak model.

Outputs (only on success) under `artifacts_dir`:
    mobilebert_intent.keras      Keras-format checkpoint (full model)
    tokenizer.json               HF tokenizer in the format Android consumes
    .tokenizer.sha256            One-line hex digest of tokenizer.json bytes
    train_stats.json             Per-class accuracies, split sizes, seed, etc.

The tokenizer.save_pretrained call also writes tokenizer_config.json,
special_tokens_map.json, vocab.txt as side files; only tokenizer.json is
copied to the Android app by `convert/to_litert_ptq.py`.
"""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np

from jarvis_training.intents import INTENT_ORDER, INTENT_SCHEMA_VERSION, Intent
from jarvis_training.train.data import (
    extract_texts,
    load_jsonl,
    stratified_split,
    to_label_ids,
)
from jarvis_training.train.model import MAX_SEQ_LENGTH, build_model, build_tokenizer


class TrainingGateError(RuntimeError):
    """Raised when a class's validation accuracy falls below the threshold."""

    def __init__(self, per_class_acc: dict[str, float], threshold: float) -> None:
        self.per_class_acc = per_class_acc
        self.threshold = threshold
        worst = min(per_class_acc.items(), key=lambda kv: kv[1])
        super().__init__(
            f"Per-class val accuracy gate failed: "
            f"worst class {worst[0]}={worst[1]:.3f} < threshold {threshold:.3f}. "
            f"Full table: {per_class_acc}"
        )


@dataclass
class TrainStats:
    seed: int
    epochs: int
    batch_size: int
    per_class_val_accuracy: dict[str, float]
    overall_val_accuracy: float
    overall_test_accuracy: float
    split_sizes: dict[str, int]
    intent_schema_version: str = INTENT_SCHEMA_VERSION
    tokenizer_sha256: str = ""
    artifacts_dir: str = ""
    classes_below_threshold: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return asdict(self)


def _seed_everything(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf

        tf.random.set_seed(seed)
    except ImportError:  # pragma: no cover - tested only with [train] extras
        pass


def _tokenize(tokenizer, texts: list[str]) -> dict:
    encoded = tokenizer(
        texts,
        padding="max_length",
        truncation=True,
        max_length=MAX_SEQ_LENGTH,
        return_tensors="np",
    )
    return {
        "input_ids": encoded["input_ids"].astype(np.int32),
        "attention_mask": encoded["attention_mask"].astype(np.int32),
    }


def _per_class_accuracy(
    y_true: np.ndarray, y_pred: np.ndarray
) -> dict[str, float]:
    out: dict[str, float] = {}
    for ordinal, intent in enumerate(INTENT_ORDER):
        mask = y_true == ordinal
        n = int(mask.sum())
        if n == 0:
            out[intent.value] = 0.0
            continue
        out[intent.value] = float((y_pred[mask] == ordinal).sum()) / n
    return out


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def train(
    data_path: Path,
    artifacts_dir: Path,
    *,
    epochs: int = 4,
    batch_size: int = 16,
    seed: int = 42,
    min_per_class_val_acc: float = 0.85,
) -> TrainStats:
    """Run 1.3 fine-tune. See module docstring for I/O contract."""
    import tensorflow as tf

    _seed_everything(seed)
    data_path = Path(data_path)
    artifacts_dir = Path(artifacts_dir)
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    records = load_jsonl(data_path)
    if not records:
        raise ValueError(f"No records found in {data_path}")

    train_records, val_records, test_records = stratified_split(records, seed=seed)
    split_sizes = {
        "train": len(train_records),
        "val": len(val_records),
        "test": len(test_records),
    }

    tokenizer = build_tokenizer()

    x_train = _tokenize(tokenizer, extract_texts(train_records))
    x_val = _tokenize(tokenizer, extract_texts(val_records))
    x_test = _tokenize(tokenizer, extract_texts(test_records))

    y_train = to_label_ids(train_records)
    y_val = to_label_ids(val_records)
    y_test = to_label_ids(test_records)

    model = build_model(num_labels=len(INTENT_ORDER))

    model.fit(
        x=x_train,
        y=y_train,
        validation_data=(x_val, y_val),
        epochs=epochs,
        batch_size=batch_size,
        verbose=2,
    )

    val_logits = model.predict(x_val, batch_size=batch_size, verbose=0).logits
    val_pred = np.argmax(val_logits, axis=-1).astype(np.int32)
    per_class_val_acc = _per_class_accuracy(y_val, val_pred)
    overall_val_acc = float((val_pred == y_val).mean())

    classes_below = [
        intent for intent, acc in per_class_val_acc.items() if acc < min_per_class_val_acc
    ]
    if classes_below:
        raise TrainingGateError(per_class_val_acc, min_per_class_val_acc)

    test_logits = model.predict(x_test, batch_size=batch_size, verbose=0).logits
    test_pred = np.argmax(test_logits, axis=-1).astype(np.int32)
    overall_test_acc = float((test_pred == y_test).mean())

    keras_path = artifacts_dir / "mobilebert_intent.keras"
    model.save(keras_path)

    tokenizer.save_pretrained(artifacts_dir)
    tokenizer_path = artifacts_dir / "tokenizer.json"
    if not tokenizer_path.exists():
        raise RuntimeError(
            f"Expected tokenizer.json to be written by save_pretrained at {tokenizer_path}"
        )
    tokenizer_hash = _sha256_hex(tokenizer_path.read_bytes())
    (artifacts_dir / ".tokenizer.sha256").write_text(tokenizer_hash + "\n", encoding="utf-8")

    stats = TrainStats(
        seed=seed,
        epochs=epochs,
        batch_size=batch_size,
        per_class_val_accuracy=per_class_val_acc,
        overall_val_accuracy=overall_val_acc,
        overall_test_accuracy=overall_test_acc,
        split_sizes=split_sizes,
        tokenizer_sha256=tokenizer_hash,
        artifacts_dir=str(artifacts_dir),
    )
    (artifacts_dir / "train_stats.json").write_text(
        json.dumps(stats.as_dict(), indent=2), encoding="utf-8"
    )

    # Silence unused-import in environments where TF is the gate for failures elsewhere.
    _ = tf
    _ = Intent
    return stats
