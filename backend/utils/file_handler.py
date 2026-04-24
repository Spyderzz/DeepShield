from __future__ import annotations

import asyncio
import io
import os
import tempfile
from typing import Iterable

from fastapi import HTTPException, UploadFile, status

IMAGE_MAGIC_BYTES: dict[bytes, str] = {
    b"\xff\xd8\xff": "image/jpeg",
    b"\x89PNG\r\n\x1a\n": "image/png",
    b"RIFF": "image/webp",  # partial; WEBP has 'RIFF....WEBP'
}


def _detect_mime_by_magic(head: bytes) -> str | None:
    for sig, mime in IMAGE_MAGIC_BYTES.items():
        if head.startswith(sig):
            if mime == "image/webp" and b"WEBP" not in head[:16]:
                continue
            return mime
    return None


async def read_upload_bytes(
    file: UploadFile,
    allowed_mimes: Iterable[str],
    max_size_mb: int,
) -> tuple[bytes, str]:
    """Read an UploadFile into memory after validating type and size.
    Returns (raw_bytes, detected_mime). Raises HTTPException on failure.
    """
    data = await file.read()
    if not data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Empty file — no bytes received",
        )
    size_mb = len(data) / (1024 * 1024)
    if size_mb > max_size_mb:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large ({size_mb:.1f} MB > {max_size_mb} MB)",
        )

    mime = _detect_mime_by_magic(data[:16]) or (file.content_type or "")
    if mime not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported type '{mime}'. Allowed: {list(allowed_mimes)}",
        )
    return data, mime


def bytes_to_buffer(data: bytes) -> io.BytesIO:
    return io.BytesIO(data)


async def save_upload_to_tempfile(
    file: UploadFile,
    allowed_mimes: Iterable[str],
    max_size_mb: int,
    suffix: str = ".mp4",
) -> tuple[str, str]:
    """Stream an UploadFile to a temp file on disk. Returns (path, mime).
    MIME is taken from the client's content_type (no magic-byte check for videos).
    Caller is responsible for deleting the temp file.
    """
    mime = (file.content_type or "").lower()
    if mime not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported type '{mime}'. Allowed: {list(allowed_mimes)}",
        )

    max_bytes = max_size_mb * 1024 * 1024
    fd, path = tempfile.mkstemp(suffix=suffix, prefix="ds_vid_")
    written = 0
    try:
        with os.fdopen(fd, "wb") as out:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                written += len(chunk)
                if written > max_bytes:
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"File too large (> {max_size_mb} MB)",
                    )
                await asyncio.to_thread(out.write, chunk)
    except Exception:
        try:
            os.unlink(path)
        except OSError:
            pass
        raise
    return path, mime
