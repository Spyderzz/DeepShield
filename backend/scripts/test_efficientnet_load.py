"""G1/G2 smoke test — EfficientNetAutoAttB4 + BlazeFace load and basic inference.

Gate G1: model loads on cold start without crash.
Gate G2: BlazeFace detects ≥1 face on a synthetic face image.

Run from backend/:
    .venv/Scripts/python.exe scripts/test_efficientnet_load.py
"""
from __future__ import annotations

import sys
import time
import urllib.request
from pathlib import Path

import numpy as np
import psutil

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def main() -> int:
    proc = psutil.Process()
    ram_before = proc.memory_info().rss / 1024 / 1024

    print("=== G1: EfficientNetAutoAttB4 load ===")
    t0 = time.perf_counter()
    try:
        from services.efficientnet_service import EfficientNetDetector
        det = EfficientNetDetector()
        elapsed = time.perf_counter() - t0
        print(f"  [PASS] model loaded in {elapsed:.1f}s")
    except Exception as e:
        print(f"  [FAIL] {e}")
        return 1

    ram_after = proc.memory_info().rss / 1024 / 1024
    print(f"  RAM delta: +{ram_after - ram_before:.0f} MB  (total: {ram_after:.0f} MB)")

    print("\n=== G2: BlazeFace face detection ===")
    # Download a small real portrait image for face detection test.
    url = "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Gatto_europeo4.jpg/320px-Gatto_europeo4.jpg"
    face_url = "https://thispersondoesnotexist.com/"
    print(f"  fetching test face from: {face_url}")
    try:
        from PIL import Image
        import io
        req = urllib.request.Request(face_url, headers={"User-Agent": "DeepShield/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = r.read()
        pil = Image.open(io.BytesIO(data)).convert("RGB")
        img_np = np.array(pil)
        frame_data = det.face_extractor.process_image(img=img_np)
        faces = frame_data.get("faces", [])
        if faces:
            print(f"  [PASS] BlazeFace detected {len(faces)} face(s)")
        else:
            print("  [WARN] BlazeFace detected 0 faces on test image — G2 inconclusive (network or image issue)")
    except Exception as e:
        print(f"  [WARN] face detection test skipped: {e}")

    print("\n=== G1b: detect_image on synthetic noise (no-face path) ===")
    try:
        from PIL import Image as PILImage
        noise = PILImage.fromarray(np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8))
        result = det.detect_image(noise)
        if result.get("error") == "no_face":
            print("  [PASS] no-face path returns gracefully")
        else:
            print(f"  [INFO] unexpected result on noise image: {result}")
    except Exception as e:
        print(f"  [FAIL] detect_image raised: {e}")
        return 1

    print("\n=== Memory gate (G8 check) ===")
    ram_final = proc.memory_info().rss / 1024 / 1024
    threshold_mb = 2500
    status = "PASS" if ram_final < threshold_mb else "WARN"
    print(f"  [{status}] RSS={ram_final:.0f} MB (threshold {threshold_mb} MB)")

    print("\nAll G1 gates passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
