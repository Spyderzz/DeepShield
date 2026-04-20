"""P3: Export EfficientNetAutoAttB4 to ONNX for 2-3× CPU inference speedup.

Exports the model to backend/models/efficientnet_autoattb4_dfdc.onnx.
After export, set EFFICIENTNET_ONNX_PATH in .env to enable ONNX inference.

Requirements (install first):
    pip install onnx onnxruntime

Usage:
    .venv/Scripts/python.exe scripts/export_onnx.py [--validate]

The --validate flag runs a quick numerical comparison between PyTorch and ONNX
outputs on a random face-shaped input to verify the export is correct.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

ONNX_OUT = Path(__file__).resolve().parent.parent / "models" / "efficientnet_autoattb4_dfdc.onnx"


def export(out_path: Path, opset: int = 17) -> None:
    print("Loading EfficientNetAutoAttB4…")
    from services.efficientnet_service import EfficientNetDetector
    det = EfficientNetDetector()
    net = det.net.eval().cpu()

    dummy = torch.zeros(1, 3, 224, 224)

    print(f"Exporting to ONNX (opset {opset})…")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.onnx.export(
        net,
        dummy,
        str(out_path),
        opset_version=opset,
        input_names=["face"],
        output_names=["logit"],
        dynamic_axes={"face": {0: "batch"}, "logit": {0: "batch"}},
        do_constant_folding=True,
    )
    size_mb = out_path.stat().st_size / 1024 / 1024
    print(f"Saved: {out_path}  ({size_mb:.1f} MB)")


def validate(out_path: Path) -> None:
    try:
        import onnxruntime as ort
    except ImportError:
        print("onnxruntime not installed — skipping validation. pip install onnxruntime")
        return

    print("Validating ONNX output vs PyTorch…")
    from services.efficientnet_service import EfficientNetDetector
    det = EfficientNetDetector()
    net = det.net.eval().cpu()

    dummy = torch.randn(1, 3, 224, 224)
    with torch.inference_mode():
        pt_out = net(dummy).numpy()

    sess = ort.InferenceSession(str(out_path), providers=["CPUExecutionProvider"])
    ort_out = sess.run(None, {"face": dummy.numpy()})[0]

    max_diff = float(np.abs(pt_out - ort_out).max())
    print(f"  Max absolute diff PyTorch vs ONNX: {max_diff:.6f}")
    if max_diff < 1e-4:
        print("  [PASS] Outputs match within tolerance")
    else:
        print("  [WARN] Outputs differ more than 1e-4 — inspect export")

    # Benchmark.
    import time
    N = 20
    t0 = time.perf_counter()
    for _ in range(N):
        sess.run(None, {"face": dummy.numpy()})
    ort_ms = (time.perf_counter() - t0) / N * 1000

    t0 = time.perf_counter()
    with torch.inference_mode():
        for _ in range(N):
            net(dummy)
    pt_ms = (time.perf_counter() - t0) / N * 1000

    print(f"  PyTorch: {pt_ms:.1f} ms/img  |  ONNX: {ort_ms:.1f} ms/img  |  speedup: {pt_ms/ort_ms:.2f}×")
    print(f"\nTo enable ONNX inference, add to .env:\n  EFFICIENTNET_ONNX_PATH={out_path}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Export EfficientNetAutoAttB4 to ONNX")
    parser.add_argument("--out", type=Path, default=ONNX_OUT, help="Output .onnx file path")
    parser.add_argument("--opset", type=int, default=17, help="ONNX opset version (default 17)")
    parser.add_argument("--validate", action="store_true", help="Compare ONNX vs PyTorch outputs and benchmark")
    args = parser.parse_args()

    export(args.out, opset=args.opset)
    if args.validate:
        validate(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
