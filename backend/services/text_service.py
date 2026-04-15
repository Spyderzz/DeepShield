from __future__ import annotations

from dataclasses import dataclass
from typing import List

from loguru import logger

from models.model_loader import get_model_loader

FAKE_TOKENS = ("fake", "false", "unreliable", "misinformation")


@dataclass
class TextClassification:
    label: str
    confidence: float
    fake_prob: float
    all_scores: dict[str, float]


def classify_text(text: str) -> TextClassification:
    pipe = get_model_loader().load_text_model()
    text = (text or "").strip()
    if not text:
        return TextClassification("unknown", 0.0, 0.0, {})
    out = pipe(text[:2000], truncation=True, top_k=None)
    items = out[0] if isinstance(out[0], list) else out
    scores = {i["label"]: float(i["score"]) for i in items}
    top_label, top_conf = max(scores.items(), key=lambda kv: kv[1])
    fake = max((p for lbl, p in scores.items() if any(t in lbl.lower() for t in FAKE_TOKENS)), default=0.0)
    logger.info(f"Text classify → {top_label} @ {top_conf:.3f} fake_p={fake:.3f}")
    return TextClassification(top_label, top_conf, fake, scores)


def extract_keywords(text: str, max_k: int = 6) -> List[str]:
    import re
    stop = {
        "the","a","an","is","are","was","were","be","been","being","to","of","and","or","but",
        "in","on","at","for","with","by","from","as","that","this","it","its","has","have","had",
        "will","would","can","could","should","may","might","do","does","did","not","no","so",
        "than","then","there","their","they","them","we","our","you","your","he","she","his","her",
    }
    words = re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text or "")
    freq: dict[str, int] = {}
    for w in words:
        wl = w.lower()
        if wl in stop:
            continue
        freq[wl] = freq.get(wl, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:max_k]]
