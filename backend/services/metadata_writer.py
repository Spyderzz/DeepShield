"""Optional ExifTool metadata writer — embeds DeepShield verdict into analyzed file metadata.

Gated behind EXIFTOOL_PATH env var. Silently skips if ExifTool is not configured.
Install ExifTool: https://exiftool.org/ — set EXIFTOOL_PATH in .env to enable.
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional

from loguru import logger

from config import settings


def _exiftool_path() -> Optional[str]:
    path = getattr(settings, "EXIFTOOL_PATH", "")
    if path and Path(path).is_file():
        return path
    return None


def write_verdict_metadata(
    file_path: str,
    verdict: str,
    authenticity_score: int,
    models_used: list[str],
    analysis_id: str,
) -> bool:
    """Embed DeepShield analysis verdict into the file's EXIF/metadata via ExifTool.

    Returns True if metadata was written, False if ExifTool is not configured or write failed.
    """
    exiftool = _exiftool_path()
    if not exiftool:
        return False

    comment = (
        f"DeepShield verdict: {verdict} | "
        f"score: {authenticity_score} | "
        f"models: {','.join(models_used)} | "
        f"id: {analysis_id}"
    )

    try:
        result = subprocess.run(
            [
                exiftool,
                f"-Comment={comment}",
                f"-UserComment={comment}",
                "-overwrite_original",
                file_path,
            ],
            capture_output=True,
            text=True,
            timeout=15,
        )
        if result.returncode == 0:
            logger.info(f"ExifTool wrote verdict metadata to {file_path}")
            return True
        else:
            logger.warning(f"ExifTool failed (rc={result.returncode}): {result.stderr.strip()}")
            return False
    except FileNotFoundError:
        logger.warning(f"ExifTool not found at {exiftool}")
        return False
    except subprocess.TimeoutExpired:
        logger.warning("ExifTool timed out writing metadata")
        return False
    except Exception as e:
        logger.warning(f"ExifTool metadata write failed: {e}")
        return False
