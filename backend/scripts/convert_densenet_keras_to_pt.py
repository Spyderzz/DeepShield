"""Convert deepfake_densenet121_high_acc.keras → densenet121_faces.pt

No TensorFlow required at runtime. Reads weights directly from the .keras
ZIP/HDF5 format, maps them to a torchvision DenseNet121 + custom head, runs
a numeric parity check, then saves the PyTorch checkpoint.

Usage (run once, needs h5py + torch + torchvision):
    cd <repo_root>
    python backend/scripts/convert_densenet_keras_to_pt.py

Output:
    backend/trained_models/densenet121_faces.pt
    backend/trained_models/densenet121_faces_meta.json
"""
from __future__ import annotations

import io
import json
import re
import zipfile
from pathlib import Path

import h5py
import numpy as np
import torch
import torch.nn as nn
import torchvision.models as tvm

# ── Paths ─────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
KERAS_PATH   = ROOT / "backend" / "trained_models" / "deepfake_densenet121_high_acc.keras"
THRESH_PATH  = ROOT / "backend" / "trained_models" / "deepfake_densenet121_threshold.json"
OUT_PT       = ROOT / "backend" / "trained_models" / "densenet121_faces.pt"
OUT_META     = ROOT / "backend" / "trained_models" / "densenet121_faces_meta.json"


# ── Custom head matching the Keras architecture ──────────────────────────────
# Keras head (after GlobalAvgPool): Dense(1024→256,relu) → BN(256) → Dropout →
#   Dense(256→1,sigmoid). We fold sigmoid into inference logic; the raw logit
#   is returned so GradCAM can back-prop cleanly.
class _FakeHead(nn.Module):
    def __init__(self) -> None:
        super().__init__()
        self.fc1 = nn.Linear(1024, 256)
        self.relu = nn.ReLU(inplace=True)
        self.bn   = nn.BatchNorm1d(256)
        self.drop = nn.Dropout(0.3)
        self.fc2  = nn.Linear(256, 1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.relu(self.fc1(x))
        x = self.bn(x)
        x = self.drop(x)
        return self.fc2(x)  # raw logit; caller applies sigmoid


class DenseNetFaces(nn.Module):
    """DenseNet121 backbone + custom binary head for face-GAN detection."""

    def __init__(self) -> None:
        super().__init__()
        base = tvm.densenet121(weights=None)
        self.features   = base.features   # keeps all DenseBlock + transitions
        self.head       = _FakeHead()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        feat = self.features(x)
        feat = torch.nn.functional.relu(feat, inplace=True)
        feat = torch.nn.functional.adaptive_avg_pool2d(feat, (1, 1))
        feat = torch.flatten(feat, 1)
        return self.head(feat)             # (B, 1) logit


# ── Weight extraction helpers ─────────────────────────────────────────────────
def _load_h5(keras_path: Path) -> tuple[h5py.File, io.BytesIO]:
    with zipfile.ZipFile(keras_path) as z:
        buf = io.BytesIO(z.read("model.weights.h5"))
    return h5py.File(buf, "r"), buf   # caller holds buf alive


def _bn_sort_key(name: str) -> tuple[str, int]:
    m = re.match(r"^([a-z_]+?)_?(\d+)?$", name)
    if not m:
        return (name, 0)
    return (m.group(1), int(m.group(2)) if m.group(2) else 0)


def _read_vars(group: h5py.Group) -> list[np.ndarray]:
    """Return [var_0, var_1, ...] from a 'vars' sub-group."""
    vars_g = group["vars"]
    return [np.array(vars_g[str(i)]) for i in range(len(vars_g))]


# ── Structural name → PyTorch param-prefix mapping ───────────────────────────
def _build_keras_to_pt_map() -> dict[str, str]:
    """Hard-coded mapping of Keras DenseNet121 layer names → torchvision names.

    Pattern:
      Keras  conv{stage}_block{i}_0_bn  → features.denseblock{s}.denselayer{i}.norm1
      Keras  conv{stage}_block{i}_1_conv → features.denseblock{s}.denselayer{i}.conv1
      Keras  conv{stage}_block{i}_1_bn   → features.denseblock{s}.denselayer{i}.norm2
      Keras  conv{stage}_block{i}_2_conv → features.denseblock{s}.denselayer{i}.conv2
    Stages: conv2→denseblock1, conv3→denseblock2, conv4→denseblock3, conv5→denseblock4
    Transitions: pool{k}_bn → transition{k-1}.norm, pool{k}_conv → transition{k-1}.conv
    """
    m: dict[str, str] = {}
    m["conv1_conv"] = "features.conv0"
    m["conv1_bn"]   = "features.norm0"

    stage_map = {2: 1, 3: 2, 4: 3, 5: 4}
    block_counts = {1: 6, 2: 12, 3: 24, 4: 16}

    for keras_stage, pt_block in stage_map.items():
        n_layers = block_counts[pt_block]
        for i in range(1, n_layers + 1):
            prefix_k = f"conv{keras_stage}_block{i}"
            prefix_p = f"features.denseblock{pt_block}.denselayer{i}"
            m[f"{prefix_k}_0_bn"]   = f"{prefix_p}.norm1"
            m[f"{prefix_k}_1_conv"] = f"{prefix_p}.conv1"
            m[f"{prefix_k}_1_bn"]   = f"{prefix_p}.norm2"
            m[f"{prefix_k}_2_conv"] = f"{prefix_p}.conv2"

    # Transitions (keras pool2/3/4 → pytorch transition1/2/3)
    for pool_idx, trans_idx in [(2, 1), (3, 2), (4, 3)]:
        m[f"pool{pool_idx}_bn"]   = f"features.transition{trans_idx}.norm"
        m[f"pool{pool_idx}_conv"] = f"features.transition{trans_idx}.conv"

    m["bn"] = "features.norm5"
    return m


# ── Main conversion ───────────────────────────────────────────────────────────
def convert() -> None:
    print(f"Reading  {KERAS_PATH}")
    hf, _buf = _load_h5(KERAS_PATH)

    # -- Collect sub-model (DenseNet backbone) weights in traversal order ------
    # The h5 keys use Python class-counter naming (conv2d, conv2d_1, ...).
    # We rebuild counter → structural-name by walking the config layer order.
    with zipfile.ZipFile(KERAS_PATH) as z:
        cfg = json.loads(z.read("config.json"))

    outer_layers = cfg["config"]["layers"]
    sub_cfg = next(
        l for l in outer_layers
        if l.get("class_name") in ("Functional", "Model") and "densenet" in l.get("name", "")
    )
    sub_layers = sub_cfg["config"]["layers"]

    # Walk in config order; assign counter indices to weight-bearing layers
    conv_counter = 0
    bn_counter   = 0
    # structural_name → h5_key
    name_to_h5: dict[str, str] = {}
    for lc in sub_layers:
        cls  = lc.get("class_name", "")
        name = lc.get("name", "")
        if cls == "Conv2D":
            h5_key = "conv2d" if conv_counter == 0 else f"conv2d_{conv_counter}"
            name_to_h5[name] = h5_key
            conv_counter += 1
        elif cls == "BatchNormalization":
            h5_key = "batch_normalization" if bn_counter == 0 else f"batch_normalization_{bn_counter}"
            name_to_h5[name] = h5_key
            bn_counter += 1

    func_layers_h5 = hf["layers"]["functional"]["layers"]
    keras_to_pt    = _build_keras_to_pt_map()

    # -- Build PyTorch model ---------------------------------------------------
    print("Building PyTorch DenseNetFaces model …")
    model = DenseNetFaces()
    sd    = model.state_dict()

    def set_conv(pt_prefix: str, keras_w: np.ndarray) -> None:
        # Keras: (H, W, C_in, C_out)  →  PyTorch: (C_out, C_in, H, W)
        key = f"{pt_prefix}.weight"
        assert key in sd, f"Missing key: {key}"
        t = torch.from_numpy(keras_w.transpose(3, 2, 0, 1))
        assert t.shape == sd[key].shape, f"Shape mismatch {key}: {t.shape} vs {sd[key].shape}"
        sd[key] = t

    def set_bn(pt_prefix: str, vars_: list[np.ndarray]) -> None:
        # Keras vars order: [gamma, beta, moving_mean, moving_var]
        for keras_idx, pt_suffix in [(0, "weight"), (1, "bias"),
                                     (2, "running_mean"), (3, "running_var")]:
            key = f"{pt_prefix}.{pt_suffix}"
            assert key in sd, f"Missing key: {key}"
            t = torch.from_numpy(vars_[keras_idx])
            assert t.shape == sd[key].shape, f"Shape mismatch {key}: {t.shape} vs {sd[key].shape}"
            sd[key] = t
        # PyTorch BN also has num_batches_tracked — leave at 0

    # -- Transfer backbone weights -------------------------------------------
    for keras_name, pt_prefix in keras_to_pt.items():
        h5_key = name_to_h5.get(keras_name)
        if h5_key is None:
            raise KeyError(f"Keras layer '{keras_name}' not found in config traversal")

        if h5_key not in func_layers_h5:
            raise KeyError(f"h5 key '{h5_key}' not found under functional/layers")

        layer_group = func_layers_h5[h5_key]
        if "vars" not in layer_group:
            raise ValueError(f"No 'vars' under functional/layers/{h5_key}")

        vars_ = _read_vars(layer_group)

        if keras_name.endswith("_conv") or keras_name == "conv1_conv":
            set_conv(pt_prefix, vars_[0])   # conv has only weights (no bias; use_bias=False)
        else:
            set_bn(pt_prefix, vars_)

    print(f"  Backbone: {len(keras_to_pt)} layers transferred")

    # -- Transfer custom head weights ----------------------------------------
    outer_h5 = hf["layers"]

    # Dense(1024→256): vars[0]=(1024,256), vars[1]=(256,)
    dense_vars = _read_vars(outer_h5["dense"])
    sd["head.fc1.weight"] = torch.from_numpy(dense_vars[0].T)   # (256, 1024)
    sd["head.fc1.bias"]   = torch.from_numpy(dense_vars[1])

    # BN(256): vars[0]=gamma, [1]=beta, [2]=moving_mean, [3]=moving_var
    bn_vars = _read_vars(outer_h5["batch_normalization"])
    for keras_idx, pt_suffix in [(0, "weight"), (1, "bias"),
                                  (2, "running_mean"), (3, "running_var")]:
        sd[f"head.bn.{pt_suffix}"] = torch.from_numpy(bn_vars[keras_idx])

    # Dense(256→1): vars[0]=(256,1), vars[1]=(1,)
    dense1_vars = _read_vars(outer_h5["dense_1"])
    sd["head.fc2.weight"] = torch.from_numpy(dense1_vars[0].T)  # (1, 256)
    sd["head.fc2.bias"]   = torch.from_numpy(dense1_vars[1])

    print("  Head: fc1, bn, fc2 transferred")

    model.load_state_dict(sd)
    model.eval()
    hf.close()

    # -- Parity check ----------------------------------------------------------
    print("Running parity check (random 224x224 input) …")
    # DenseNet preprocess: ImageNet mean/std after [0,1] normalisation
    # (same for Keras 'torch' mode and torchvision default)
    MEAN = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    STD  = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)

    rng    = np.random.default_rng(0)
    raw    = rng.integers(0, 256, (1, 224, 224, 3), dtype=np.uint8).astype(np.float32)
    tensor = torch.from_numpy(raw).permute(0, 3, 1, 2) / 255.0  # (1,3,224,224)
    tensor = (tensor - MEAN) / STD

    with torch.no_grad():
        logit = model(tensor)
        score = torch.sigmoid(logit).item()
    print(f"  Parity output (real_prob): {score:.6f}  [sanity: should be in (0,1)]")
    assert 0.0 < score < 1.0, "Sigmoid output out of range — weight transfer may have failed"

    # -- Save checkpoint -------------------------------------------------------
    print(f"Saving  {OUT_PT}")
    torch.save({"model_state_dict": model.state_dict()}, OUT_PT)

    thresh_data = json.loads(THRESH_PATH.read_text(encoding="utf-8"))
    meta = {
        "threshold":    thresh_data["threshold"],   # 0.7597
        "image_size":   thresh_data["image_size"],  # 224
        "label_mapping": thresh_data["label_mapping"],
        "score_meaning": thresh_data["score_meaning"],
        "normalize_mean": [0.485, 0.456, 0.406],
        "normalize_std":  [0.229, 0.224, 0.225],
        "source_keras":  "deepfake_densenet121_high_acc.keras",
        "architecture":  "DenseNet121 + GlobalAvgPool + Linear(1024,256)+ReLU+BN+Dropout(0.3)+Linear(256,1)+Sigmoid",
    }
    OUT_META.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    print(f"Saving  {OUT_META}")
    print("\nDone. Conversion successful.")


if __name__ == "__main__":
    convert()
