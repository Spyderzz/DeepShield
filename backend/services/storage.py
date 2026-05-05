"""Phase 19.2 — object storage with thumbnails.

Persists analyzed media under MEDIA_ROOT/{sha[:2]}/{sha}.{ext} so that records
can be rehydrated and re-analyzed without re-uploading. Generates a 400px
thumbnail at MEDIA_ROOT/thumbs/{sha}_400.jpg for history UIs.

Local-disk implementation only; an S3 adapter can slot in at the same API.
"""

from __future__ import annotations

import base64
import hashlib
import os
from pathlib import Path

from PIL import Image
from loguru import logger
from config import settings

MEDIA_ROOT = Path(settings.MEDIA_ROOT).resolve()
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
    rel = dest.relative_to(MEDIA_ROOT)
    return f"/media/{rel.as_posix()}"


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
    rel = dest.relative_to(MEDIA_ROOT)
    return f"/media/{rel.as_posix()}"


def make_image_thumbnail(pil: Image.Image, sha: str) -> tuple[str | None, str | None]:
    """Write a 400px-max JPEG thumbnail.

    Returns (url_path, data_url) where:
    - url_path is the served asset path ("/media/thumbs/{sha}_400.jpg") or None
    - data_url is a base64 JPEG data URL for inline embedding, or None on failure
    The data URL is always generated (doesn't need file storage) so thumbnails
    work even when persistent storage is unavailable.
    """
    buf = io.BytesIO()
    data_url: str | None = None
    url_path: str | None = None

    try:
        im = pil.convert("RGB").copy()
        im.thumbnail((THUMB_MAX, THUMB_MAX))
        im.save(buf, "JPEG", quality=75, optimize=True)
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        data_url = f"data:image/jpeg;base64,{b64}"
    except Exception as e:  # noqa: BLE001
        logger.warning(f"thumbnail base64 generation failed for {sha}: {e}")

    if data_url:
        try:
            _ensure_dirs()
            dest = THUMB_DIR / f"{sha}_400.jpg"
            if not dest.exists():
                dest.write_bytes(buf.getvalue())
            url_path = f"/media/thumbs/{sha}_400.jpg"
        except Exception as e:  # noqa: BLE001
            logger.warning(f"thumbnail file save failed for {sha}: {e}")

    return url_path, data_url


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


def save_overlay(data_url: str, sha: str, suffix: str) -> str | None:
    """Persist a base64 data-URL image as a PNG file for later retrieval.

    Returns a URL-style path like /media/overlays/{sha}_{suffix}.png, or None on failure.
    The suffix distinguishes overlay types: 'heatmap', 'ela', 'boxes'.
    """
    try:
        _ensure_dirs()
        overlay_dir = MEDIA_ROOT / "overlays"
        overlay_dir.mkdir(parents=True, exist_ok=True)
        dest = overlay_dir / f"{sha}_{suffix}.png"
        if dest.exists():
            return f"/media/overlays/{sha}_{suffix}.png"
        # Strip the data URL prefix (e.g. "data:image/png;base64,")
        raw_b64 = data_url.split(",", 1)[1] if "," in data_url else data_url
        dest.write_bytes(base64.b64decode(raw_b64))
        return f"/media/overlays/{sha}_{suffix}.png"
    except Exception as e:  # noqa: BLE001
        logger.warning(f"save_overlay failed for {sha}_{suffix}: {e}")
        return None
