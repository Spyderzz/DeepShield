"""Phase 19.2 — object storage with thumbnails.

Persists analyzed media under MEDIA_ROOT/{sha[:2]}/{sha}.{ext} so that records
can be rehydrated and re-analyzed without re-uploading. Generates a 400px
thumbnail at MEDIA_ROOT/thumbs/{sha}_400.jpg for history UIs.

Local-disk implementation only; an S3 adapter can slot in at the same API.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

from PIL import Image
from loguru import logger

MEDIA_ROOT = Path(os.environ.get("MEDIA_ROOT", "./media")).resolve()
THUMB_DIR = MEDIA_ROOT / "thumbs"
THUMB_MAX = 400


def _ensure_dirs() -> None:
    MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
    THUMB_DIR.mkdir(parents=True, exist_ok=True)


def sha256_bytes(data: bytes) -> str:
    h = hashlib.sha256()
    # Process in 64KB chunks per spec
    view = memoryview(data)
    for i in range(0, len(view), 65536):
        h.update(view[i : i + 65536])
    return h.hexdigest()


def sha256_file(path: str | os.PathLike) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _media_path_for(sha: str, ext: str) -> Path:
    ext = (ext or "").lstrip(".").lower() or "bin"
    return MEDIA_ROOT / sha[:2] / f"{sha}.{ext}"


def save_bytes(data: bytes, sha: str, ext: str) -> str:
    """Write raw bytes to the content-addressed path. Returns relative media path."""
    _ensure_dirs()
    dest = _media_path_for(sha, ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        dest.write_bytes(data)
    return str(dest.relative_to(MEDIA_ROOT.parent)) if MEDIA_ROOT.parent in dest.parents else str(dest)


def save_file(src_path: str, sha: str, ext: str) -> str:
    """Copy an existing file (e.g. temp video) into object storage."""
    _ensure_dirs()
    dest = _media_path_for(sha, ext)
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        with open(src_path, "rb") as src, open(dest, "wb") as dst:
            while True:
                chunk = src.read(65536)
                if not chunk:
                    break
                dst.write(chunk)
    return str(dest)


def make_image_thumbnail(pil: Image.Image, sha: str) -> str | None:
    """Write a 400px-max JPEG thumbnail. Returns URL-style path or None on failure."""
    try:
        _ensure_dirs()
        dest = THUMB_DIR / f"{sha}_400.jpg"
        if dest.exists():
            return f"/media/thumbs/{sha}_400.jpg"
        im = pil.convert("RGB").copy()
        im.thumbnail((THUMB_MAX, THUMB_MAX))
        im.save(dest, "JPEG", quality=82, optimize=True)
        return f"/media/thumbs/{sha}_400.jpg"
    except Exception as e:  # noqa: BLE001
        logger.warning(f"thumbnail generation failed for {sha}: {e}")
        return None


def make_video_thumbnail(video_path: str, sha: str) -> str | None:
    """Grab a frame ~1s in as the video thumbnail."""
    try:
        import cv2  # lazy import — heavy

        _ensure_dirs()
        dest = THUMB_DIR / f"{sha}_400.jpg"
        if dest.exists():
            return f"/media/thumbs/{sha}_400.jpg"
        cap = cv2.VideoCapture(video_path)
        try:
            fps = cap.get(cv2.CAP_PROP_FPS) or 25
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps))
            ok, frame = cap.read()
            if not ok:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
            if not ok:
                return None
        finally:
            cap.release()
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        im = Image.fromarray(rgb)
        im.thumbnail((THUMB_MAX, THUMB_MAX))
        im.save(dest, "JPEG", quality=82, optimize=True)
        return f"/media/thumbs/{sha}_400.jpg"
    except Exception as e:  # noqa: BLE001
        logger.warning(f"video thumbnail failed for {sha}: {e}")
        return None
