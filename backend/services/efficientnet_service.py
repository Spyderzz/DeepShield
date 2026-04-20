"""EfficientNetAutoAttB4 adapter — wraps ICPR2020 DFDC model into DeepShield service interface."""
from __future__ import annotations

import pickle
import sys
from pathlib import Path
from typing import List, Optional

import numpy as np
import torch
from loguru import logger
from PIL import Image
from scipy.special import expit
from torch.utils.model_zoo import load_url

# Resolve ICPR2020 repo root and patch sys.path so its modules are importable.
_ICPR_ROOT = (Path(__file__).resolve().parent.parent / "models" / "icpr2020dfdc").resolve()
_NOTEBOOK_DIR = str(_ICPR_ROOT / "notebook")
if str(_ICPR_ROOT) not in sys.path:
    sys.path.insert(0, str(_ICPR_ROOT))
if _NOTEBOOK_DIR not in sys.path:
    sys.path.insert(0, _NOTEBOOK_DIR)

# These imports are valid only after the sys.path patch above.
from blazeface import BlazeFace, FaceExtractor  # noqa: E402
from architectures import fornet, weights  # noqa: E402
from isplutils import utils as ispl_utils  # noqa: E402

# Default calibrator path — populated by scripts/fit_calibrator.py.
_CALIBRATOR_PATH = Path(__file__).resolve().parent.parent / "models" / "efficientnet_calibrator.pkl"


def _load_calibrator(path: Path = _CALIBRATOR_PATH):
    """Load isotonic calibrator if it exists. Returns None otherwise."""
    if not path.exists():
        return None
    try:
        with path.open("rb") as f:
            cal = pickle.load(f)
        logger.info(f"Isotonic calibrator loaded from {path}")
        return cal
    except Exception as e:
        logger.warning(f"Failed to load calibrator ({e}) — using raw sigmoid scores")
        return None


class EfficientNetDetector:
    """Thin adapter that loads EfficientNetAutoAttB4 (DFDC-trained) and exposes
    detect_image() / detect_video_frames() matching DeepShield's service interface.

    If backend/models/efficientnet_calibrator.pkl exists (produced by
    scripts/fit_calibrator.py), raw sigmoid scores are passed through an isotonic
    regression calibrator before being returned. Set calibrator=None to disable.
    """

    def __init__(
        self,
        model_name: str = "EfficientNetAutoAttB4",
        train_db: str = "DFDC",
        device: str = "cpu",
        calibrator_path: Optional[Path] = None,
    ) -> None:
        self.device = torch.device(device)
        self.model_name = model_name
        self.train_db = train_db

        weight_key = f"{model_name}_{train_db}"
        if weight_key not in weights.weight_url:
            raise KeyError(f"Unknown model/DB combination: {weight_key}")

        self.net = getattr(fornet, model_name)().eval().to(self.device)
        # check_hash=False — the ISPL mirror occasionally has stale sha256 hashes in URLs.
        state = load_url(weights.weight_url[weight_key], map_location=self.device, check_hash=False)
        self.net.load_state_dict(state)

        self.transf = ispl_utils.get_transformer(
            "scale", 224, self.net.get_normalizer(), train=False
        )

        blazeface_dir = _ICPR_ROOT / "blazeface"
        weights_path = blazeface_dir / "blazeface.pth"
        anchors_path = blazeface_dir / "anchors.npy"
        if not weights_path.exists() or not anchors_path.exists():
            raise FileNotFoundError(
                f"BlazeFace assets missing: expected {weights_path} and {anchors_path}. "
                "Ensure icpr2020dfdc is cloned into backend/models/ with its blazeface/ subdirectory."
            )

        self.facedet = BlazeFace().to(self.device)
        self.facedet.load_weights(str(weights_path))
        self.facedet.load_anchors(str(anchors_path))
        self.face_extractor = FaceExtractor(facedet=self.facedet)

        self.calibrator = _load_calibrator(calibrator_path or _CALIBRATOR_PATH)
        self.calibrator_applied = self.calibrator is not None

        logger.info(
            f"EfficientNetDetector ready: {model_name}/{train_db} on {self.device} "
            f"| calibrator={'yes' if self.calibrator_applied else 'no'}"
        )

    def _face_tensor(self, face_np: np.ndarray) -> torch.Tensor:
        """Apply albumentations transform to a cropped face array and return a CHW tensor."""
        result = self.transf(image=face_np)
        return result["image"]

    def _calibrate(self, score: float) -> float:
        """Apply isotonic calibration if available; otherwise return score unchanged."""
        if self.calibrator is None:
            return score
        try:
            return float(self.calibrator.predict([[score]])[0])
        except Exception:
            return score

    def _calibrate_batch(self, scores: np.ndarray) -> np.ndarray:
        """Apply isotonic calibration to a 1-D array of scores."""
        if self.calibrator is None:
            return scores
        try:
            return self.calibrator.predict(scores.reshape(-1, 1)).flatten()
        except Exception:
            return scores

    def raw_logit(self, face_tensor: torch.Tensor) -> float:
        """Return raw logit for a single face tensor — used by fit_calibrator.py."""
        with torch.inference_mode():
            return float(self.net(face_tensor.unsqueeze(0).to(self.device)).item())

    def detect_image(self, pil_image: Image.Image) -> dict:
        """Run EfficientNet on a single PIL image.

        Returns:
            {"score": float|None, "result": "FAKE"|"REAL"|None, "model": str,
             "error": str|None, "calibrator_applied": bool}
        """
        if pil_image.mode != "RGB":
            pil_image = pil_image.convert("RGB")
        img_array = np.array(pil_image)

        frame_data = self.face_extractor.process_image(img=img_array)
        faces: list = frame_data.get("faces", [])
        if not faces:
            logger.debug("EfficientNetDetector.detect_image: no face detected")
            return {
                "error": "no_face",
                "score": None,
                "result": None,
                "model": f"{self.model_name}_{self.train_db}",
                "calibrator_applied": False,
            }

        face_t = self._face_tensor(faces[0])
        with torch.inference_mode():
            logit = self.net(face_t.unsqueeze(0).to(self.device))
            raw_score = float(torch.sigmoid(logit).item())

        score = self._calibrate(raw_score)
        return {
            "score": score,
            "result": "FAKE" if score > 0.5 else "REAL",
            "model": f"{self.model_name}_{self.train_db}",
            "error": None,
            "calibrator_applied": self.calibrator_applied,
        }

    def detect_video_frames(self, frames: List[np.ndarray]) -> dict:
        """Run EfficientNet on a list of BGR/RGB numpy frames (as extracted by OpenCV).

        Returns:
            {"mean_score": float|None, "per_frame": list[float], "model": str,
             "error": str|None, "calibrator_applied": bool}
        """
        face_tensors: list[torch.Tensor] = []
        for frame in frames:
            # Ensure RGB — OpenCV yields BGR, PIL already RGB.
            if frame.ndim == 3 and frame.shape[2] == 3:
                frame_rgb = frame[..., ::-1].copy() if frame.dtype == np.uint8 else frame
            else:
                frame_rgb = frame
            frame_data = self.face_extractor.process_image(img=frame_rgb)
            faces: list = frame_data.get("faces", [])
            if faces:
                face_tensors.append(self._face_tensor(faces[0]))

        if not face_tensors:
            logger.debug("EfficientNetDetector.detect_video_frames: no faces in any frame")
            return {
                "error": "no_faces",
                "mean_score": None,
                "per_frame": [],
                "model": f"{self.model_name}_{self.train_db}",
                "calibrator_applied": False,
            }

        batch = torch.stack(face_tensors).to(self.device)
        with torch.inference_mode():
            logits = self.net(batch).cpu().numpy().flatten()

        raw_per_frame = expit(logits)
        per_frame = self._calibrate_batch(raw_per_frame).tolist()
        mean_score = float(self._calibrate(float(expit(np.mean(logits)))))
        return {
            "mean_score": mean_score,
            "per_frame": per_frame,
            "model": f"{self.model_name}_{self.train_db}",
            "error": None,
            "calibrator_applied": self.calibrator_applied,
        }
