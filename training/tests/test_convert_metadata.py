"""Tests for the metadata + size-gate helpers in convert.to_litert_ptq.

We do NOT exercise the real Keras→LiteRT path (it needs TF + ai-edge-litert
and a real `.keras` checkpoint). Instead, we test the deterministic helpers
and stub the heavy converter to validate the fail-closed size gate.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from jarvis_training.convert import to_litert_ptq
from jarvis_training.convert.to_litert_ptq import (
    CONVERSION_MODE,
    ConvertSizeError,
    _build_metadata,
    _sha256_hex,
    convert,
)
from jarvis_training.intents import INTENT_ORDER, INTENT_SCHEMA_VERSION


def test_sha256_hex_is_deterministic():
    payload = b'{"hello": "world"}'
    expected = hashlib.sha256(payload).hexdigest()
    assert _sha256_hex(payload) == expected
    assert _sha256_hex(payload) == _sha256_hex(payload)


def test_build_metadata_schema_and_intent_order():
    md = _build_metadata(
        tokenizer_hash="a" * 64,
        training_data_hash="b" * 64,
        size_mb=23.45,
    )
    assert set(md.keys()) == {
        "schema_version",
        "intent_order",
        "tokenizer_hash",
        "training_data_hash",
        "conversion_mode",
        "size_mb",
        "max_seq_length",
        "model_name",
    }
    assert md["schema_version"] == INTENT_SCHEMA_VERSION
    assert md["conversion_mode"] == CONVERSION_MODE
    assert md["max_seq_length"] == 128
    assert md["model_name"] == "google/mobilebert-uncased"
    assert md["intent_order"] == [i.value for i in INTENT_ORDER]
    # And critically, the order matches the load-bearing tuple verbatim:
    assert md["intent_order"] == [
        "device.action",
        "draft.email",
        "draft.reply",
        "schedule.event",
        "escalate.burst",
        "note.capture",
        "dismiss",
    ]


def test_build_metadata_size_mb_is_rounded():
    md = _build_metadata(
        tokenizer_hash="x" * 64,
        training_data_hash="y" * 64,
        size_mb=23.456789,
    )
    assert md["size_mb"] == 23.4568


def _stub_converter(byte_count: int):
    """Return a stand-in for _convert_keras_to_litert_int8 that writes N bytes."""

    def _fake(keras_path: Path, out_path: Path) -> None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_bytes(b"\0" * byte_count)

    return _fake


def _prep_paths(tmp_path: Path) -> dict[str, Path]:
    keras = tmp_path / "mobilebert_intent.keras"
    keras.write_bytes(b"fake-keras-bytes")  # convert() only checks existence
    tokenizer = tmp_path / "tokenizer.json"
    tokenizer.write_text('{"model":{"type":"WordPiece"}}', encoding="utf-8")
    data = tmp_path / "intents.jsonl"
    data.write_text('{"text":"x","intent":"dismiss"}\n', encoding="utf-8")
    artifacts = tmp_path / "artifacts"
    assets = tmp_path / "android_assets"
    return {
        "keras": keras,
        "tokenizer": tokenizer,
        "data": data,
        "artifacts": artifacts,
        "assets": assets,
    }


def test_convert_writes_artifacts_and_copies_to_assets(monkeypatch, tmp_path):
    paths = _prep_paths(tmp_path)
    # Tiny model: 1024 bytes ≈ 0.001 MB, well under the default 30 MB limit.
    monkeypatch.setattr(to_litert_ptq, "_convert_keras_to_litert_int8", _stub_converter(1024))

    stats = convert(
        keras_path=paths["keras"],
        tokenizer_path=paths["tokenizer"],
        data_path=paths["data"],
        artifacts_dir=paths["artifacts"],
        android_assets_dir=paths["assets"],
    )

    tflite = paths["artifacts"] / "intent_router.tflite"
    metadata_path = paths["artifacts"] / "model_metadata.json"
    assert tflite.exists()
    assert metadata_path.exists()
    assert (paths["assets"] / "intent_router.tflite").exists()
    assert (paths["assets"] / "tokenizer.json").exists()
    assert (paths["assets"] / "model_metadata.json").exists()

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["tokenizer_hash"] == _sha256_hex(paths["tokenizer"].read_bytes())
    assert metadata["training_data_hash"] == _sha256_hex(paths["data"].read_bytes())
    assert metadata["intent_order"] == [i.value for i in INTENT_ORDER]
    assert stats.size_mb < 1.0


def test_convert_fails_closed_when_oversized(monkeypatch, tmp_path):
    paths = _prep_paths(tmp_path)
    # 2 MB stub under a 1 MB size limit → must raise.
    monkeypatch.setattr(
        to_litert_ptq, "_convert_keras_to_litert_int8", _stub_converter(2 * 1024 * 1024)
    )
    with pytest.raises(ConvertSizeError) as exc:
        convert(
            keras_path=paths["keras"],
            tokenizer_path=paths["tokenizer"],
            data_path=paths["data"],
            artifacts_dir=paths["artifacts"],
            android_assets_dir=paths["assets"],
            size_limit_mb=1.0,
        )
    assert exc.value.size_mb >= 1.0
    assert exc.value.limit_mb == 1.0
    # Fail closed: no metadata, no copy to assets.
    assert not (paths["artifacts"] / "model_metadata.json").exists()
    assert not (paths["assets"] / "intent_router.tflite").exists()
    assert not (paths["assets"] / "tokenizer.json").exists()
    assert not (paths["assets"] / "model_metadata.json").exists()


def test_convert_rejects_missing_inputs(tmp_path):
    paths = _prep_paths(tmp_path)
    paths["tokenizer"].unlink()
    with pytest.raises(FileNotFoundError):
        convert(
            keras_path=paths["keras"],
            tokenizer_path=paths["tokenizer"],
            data_path=paths["data"],
            artifacts_dir=paths["artifacts"],
            android_assets_dir=paths["assets"],
        )
