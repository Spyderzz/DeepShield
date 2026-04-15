from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List

from loguru import logger

from models.model_loader import get_model_loader

FAKE_TOKENS = ("fake", "false", "unreliable", "misinformation")

# --- Sensationalism patterns ---
CLICKBAIT_PATTERNS = [
    (r"\byou won'?t believe\b", "clickbait"),
    (r"\bbreaking\s*:", "clickbait"),
    (r"\bshocking\s*:", "clickbait"),
    (r"\bexclusive\s*:", "clickbait"),
    (r"\bjust\s+in\s*:", "clickbait"),
    (r"\burgent\s*:", "clickbait"),
    (r"\bwhat\s+happens\s+next\b", "clickbait"),
    (r"\bthis\s+will\s+change\b", "clickbait"),
    (r"\b(?:everyone|nobody)\s+(?:is|was)\s+talking\b", "clickbait"),
]
EMOTIONAL_WORDS = {
    "outrage", "shocking", "horrifying", "disgusting", "amazing", "incredible",
    "unbelievable", "devastating", "terrifying", "explosive", "bombshell",
    "jaw-dropping", "heartbreaking", "furious", "scandal", "crisis",
    "chaos", "destroyed", "slammed", "blasted", "exposed", "revealed",
}
SUPERLATIVES = {
    "best", "worst", "greatest", "biggest", "most", "least",
    "fastest", "deadliest", "largest", "smallest", "ultimate",
}

# --- Manipulation indicator patterns ---
MANIPULATION_PATTERNS = [
    # Unverified claims
    (r"\bsources?\s+(?:say|said|claim|report)\b", "unverified_claim", "medium",
     "Unverified source attribution without specific citation"),
    (r"\ballegedly\b", "unverified_claim", "low",
     "Hedging language suggests unverified information"),
    (r"\breports?\s+suggest\b", "unverified_claim", "medium",
     "Vague report attribution"),
    (r"\baccording\s+to\s+(?:some|many|several)\b", "unverified_claim", "medium",
     "Non-specific source attribution"),
    (r"\brunconfirmed\b", "unverified_claim", "medium",
     "Explicitly unconfirmed information"),
    # Emotional manipulation
    (r"\boutrage\b", "emotional_manipulation", "medium",
     "Emotional trigger word designed to provoke reaction"),
    (r"\bshocking\s+truth\b", "emotional_manipulation", "high",
     "Sensationalist phrase designed to manipulate reader emotion"),
    (r"\bwake\s+up\b", "emotional_manipulation", "medium",
     "Call-to-action implying hidden knowledge"),
    (r"\bthey\s+don'?t\s+want\s+you\s+to\s+know\b", "emotional_manipulation", "high",
     "Conspiracy framing language"),
    (r"\bopen\s+your\s+eyes\b", "emotional_manipulation", "medium",
     "Implies audience ignorance"),
    # False authority
    (r"\bexperts?\s+(?:confirm|say|agree|warn)\b", "false_authority", "medium",
     "Unnamed expert citation without specific attribution"),
    (r"\bscientists?\s+(?:confirm|prove|say)\b", "false_authority", "medium",
     "Unnamed scientist citation"),
    (r"\bstudies?\s+(?:show|prove|confirm)\b", "false_authority", "low",
     "Vague study reference without citation"),
    (r"\beveryone\s+knows\b", "false_authority", "medium",
     "Appeal to common knowledge fallacy"),
    (r"\bit'?s\s+(?:a\s+)?(?:well-?known|proven)\s+fact\b", "false_authority", "medium",
     "Assertion of fact without evidence"),
]


@dataclass
class TextClassification:
    label: str
    confidence: float
    fake_prob: float
    all_scores: dict[str, float]


@dataclass
class SensationalismResult:
    score: int  # 0-100
    level: str  # Low / Medium / High
    exclamation_count: int
    caps_word_count: int
    clickbait_matches: int
    emotional_word_count: int
    superlative_count: int


@dataclass
class ManipulationIndicator:
    pattern_type: str       # unverified_claim / emotional_manipulation / false_authority
    matched_text: str
    start_pos: int
    end_pos: int
    severity: str           # low / medium / high
    description: str


def classify_text(text: str) -> TextClassification:
    pipe = get_model_loader().load_text_model()
    text = (text or "").strip()
    if not text:
        return TextClassification("unknown", 0.0, 0.0, {})
    out = pipe(text[:2000], truncation=True, top_k=None)
    items = out[0] if isinstance(out[0], list) else out
    scores = {i["label"]: float(i["score"]) for i in items}
    top_label, top_conf = max(scores.items(), key=lambda kv: kv[1])
    
    # Extract fake probability: check mapping for LABEL_0 (fake) or literal fake tokens
    fake_prob = 0.0
    if "LABEL_0" in scores:
        fake_prob = scores["LABEL_0"]
    else:
        fake_prob = max((p for lbl, p in scores.items() if any(t in lbl.lower() for t in FAKE_TOKENS)), default=0.0)
        
    logger.info(f"Text classify → {top_label} @ {top_conf:.3f} fake_p={fake_prob:.3f}")
    return TextClassification(top_label, top_conf, fake_prob, scores)


def score_sensationalism(text: str) -> SensationalismResult:
    """Compute a 0-100 sensationalism score from structural/linguistic signals."""
    if not text:
        return SensationalismResult(0, "Low", 0, 0, 0, 0, 0)

    words = text.split()
    total_words = max(len(words), 1)

    # Count signals
    excl = text.count("!")
    caps = sum(1 for w in words if w.isupper() and len(w) > 2)
    clickbait = sum(
        1 for pat, _ in CLICKBAIT_PATTERNS
        if re.search(pat, text, re.IGNORECASE)
    )
    emotional = sum(1 for w in words if w.lower().strip(".,!?;:") in EMOTIONAL_WORDS)
    superlative = sum(1 for w in words if w.lower().strip(".,!?;:") in SUPERLATIVES)

    # Weighted score (each normalized to ~0-25 range, sum capped at 100)
    raw = (
        min(excl * 8, 25)
        + min(caps / total_words * 200, 25)
        + min(clickbait * 12, 25)
        + min(emotional * 6, 15)
        + min(superlative * 5, 10)
    )
    score = int(min(100, max(0, raw)))
    level = "Low" if score < 30 else ("Medium" if score < 60 else "High")

    logger.info(f"Sensationalism → {score} ({level}) excl={excl} caps={caps} cb={clickbait} emo={emotional}")
    return SensationalismResult(score, level, excl, caps, clickbait, emotional, superlative)


def detect_manipulation_indicators(text: str) -> List[ManipulationIndicator]:
    """Scan text for manipulation linguistic patterns with positions."""
    if not text:
        return []
    indicators: List[ManipulationIndicator] = []
    for pattern, ptype, severity, description in MANIPULATION_PATTERNS:
        for m in re.finditer(pattern, text, re.IGNORECASE):
            indicators.append(ManipulationIndicator(
                pattern_type=ptype,
                matched_text=m.group(),
                start_pos=m.start(),
                end_pos=m.end(),
                severity=severity,
                description=description,
            ))
    # Sort by position
    indicators.sort(key=lambda i: i.start_pos)
    logger.info(f"Manipulation indicators → {len(indicators)} found")
    return indicators


def extract_keywords(text: str, max_k: int = 6) -> List[str]:
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
