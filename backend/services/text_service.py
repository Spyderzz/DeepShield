from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from loguru import logger

from config import settings
from models.model_loader import get_model_loader

FAKE_TOKENS = ("fake", "false", "unreliable", "misinformation")

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

MANIPULATION_PATTERNS = [
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

_NER_PREFERRED = {"PERSON", "ORG", "GPE", "EVENT", "PRODUCT", "NORP"}


@dataclass
class TextClassification:
    label: str
    confidence: float
    fake_prob: float
    all_scores: dict[str, float]


@dataclass
class SensationalismResult:
    score: int
    level: str
    exclamation_count: int
    caps_word_count: int
    clickbait_matches: int
    emotional_word_count: int
    superlative_count: int


@dataclass
class ManipulationIndicator:
    pattern_type: str
    matched_text: str
    start_pos: int
    end_pos: int
    severity: str
    description: str


def detect_language(text: str) -> str:
    if not text or len(text.strip()) < 10:
        return "en"
    try:
        from langdetect import detect  # type: ignore
        lang = detect(text.strip())
        logger.info(f"Language detected: {lang}")
        return lang
    except ImportError:
        logger.debug("langdetect not installed - defaulting to 'en'")
        return "en"
    except Exception as e:
        logger.debug(f"Language detection failed: {e} - defaulting to 'en'")
        return "en"


def _scores_to_classification(items, *, allow_label0_fallback: bool = True) -> TextClassification:
    """Convert pipeline output to TextClassification.

    Prefer semantic fake labels. The bundled jy46604790 model uses
    LABEL_0=fake/LABEL_1=real, but arbitrary replacement models may not.
    """
    scores = {i["label"]: float(i["score"]) for i in items}
    top_label, top_conf = max(scores.items(), key=lambda kv: kv[1])

    fake_prob = max(
        (p for lbl, p in scores.items() if any(t in lbl.lower() for t in FAKE_TOKENS)),
        default=None,
    )
    if fake_prob is None:
        if allow_label0_fallback and "LABEL_0" in scores and "LABEL_1" in scores:
            fake_prob = scores["LABEL_0"]
        else:
            logger.warning(f"Could not infer fake label from text model labels: {list(scores)}")
            top_label = "uncertain_label_mapping"
            top_conf = 0.0
            fake_prob = 0.5

    return TextClassification(top_label, top_conf, fake_prob, scores)


def classify_text(text: str, language: Optional[str] = None) -> TextClassification:
    text = (text or "").strip()
    if not text:
        return TextClassification("unknown", 0.0, 0.0, {})

    loader = get_model_loader()
    is_non_english = bool(language and language != "en")
    if is_non_english and not settings.TEXT_MULTILANG_MODEL_ID:
        logger.warning(f"No multilingual text model configured for language={language}; returning uncertain score")
        return TextClassification("unsupported_language", 0.0, 0.5, {})

    pipe = loader.load_multilang_text_model() if is_non_english else loader.load_text_model()

    out = pipe(text[:2000], truncation=True, top_k=None)
    items = out[0] if isinstance(out[0], list) else out
    clf = _scores_to_classification(items, allow_label0_fallback=not is_non_english)
    logger.info(
        f"Text classify [{language or 'en'}] -> {clf.label} @ {clf.confidence:.3f} "
        f"fake_p={clf.fake_prob:.3f}"
    )
    return clf


def score_sensationalism(text: str) -> SensationalismResult:
    if not text:
        return SensationalismResult(0, "Low", 0, 0, 0, 0, 0)

    words = text.split()
    total_words = max(len(words), 1)
    excl = text.count("!")
    caps = sum(1 for w in words if w.isupper() and len(w) > 2)
    clickbait = sum(1 for pat, _ in CLICKBAIT_PATTERNS if re.search(pat, text, re.IGNORECASE))
    emotional = sum(1 for w in words if w.lower().strip(".,!?;:") in EMOTIONAL_WORDS)
    superlative = sum(1 for w in words if w.lower().strip(".,!?;:") in SUPERLATIVES)

    raw = (
        min(excl * 8, 25)
        + min(caps / total_words * 200, 25)
        + min(clickbait * 12, 25)
        + min(emotional * 6, 15)
        + min(superlative * 5, 10)
    )
    score = int(min(100, max(0, raw)))
    level = "Low" if score < 30 else ("Medium" if score < 60 else "High")

    logger.info(f"Sensationalism -> {score} ({level}) excl={excl} caps={caps} cb={clickbait} emo={emotional}")
    return SensationalismResult(score, level, excl, caps, clickbait, emotional, superlative)


def detect_manipulation_indicators(text: str) -> List[ManipulationIndicator]:
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
    indicators.sort(key=lambda i: i.start_pos)
    logger.info(f"Manipulation indicators -> {len(indicators)} found")
    return indicators


def extract_entities(text: str, max_k: int = 6) -> List[str]:
    if not text or len(text.strip()) < 20:
        return _extract_keywords_freq(text, max_k)

    nlp = get_model_loader().load_spacy_nlp()
    if nlp is None:
        return _extract_keywords_freq(text, max_k)

    try:
        doc = nlp(text[:5000])
        preferred: List[str] = []
        other: List[str] = []
        seen: set[str] = set()

        for ent in doc.ents:
            norm = ent.text.strip()
            norm_lower = norm.lower()
            if not norm or norm_lower in seen or len(norm) < 2:
                continue
            seen.add(norm_lower)
            if ent.label_ in _NER_PREFERRED:
                preferred.append(norm)
            else:
                other.append(norm)

        entities = preferred + other
        if len(entities) >= 2:
            logger.info(f"NER extracted {len(entities)} entities: {entities[:max_k]}")
            return entities[:max_k]

        freq_kws = _extract_keywords_freq(text, max_k)
        combined = entities + [k for k in freq_kws if k.lower() not in seen]
        return combined[:max_k]
    except Exception as e:
        logger.warning(f"spaCy NER failed: {e} - falling back to frequency extraction")
        return _extract_keywords_freq(text, max_k)


def _extract_keywords_freq(text: str, max_k: int = 6) -> List[str]:
    stop = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being", "to", "of", "and", "or", "but",
        "in", "on", "at", "for", "with", "by", "from", "as", "that", "this", "it", "its", "has", "have", "had",
        "will", "would", "can", "could", "should", "may", "might", "do", "does", "did", "not", "no", "so",
        "than", "then", "there", "their", "they", "them", "we", "our", "you", "your", "he", "she", "his", "her",
    }
    words = re.findall(r"[A-Za-z][A-Za-z\-']{2,}", text or "")
    freq: dict[str, int] = {}
    for w in words:
        wl = w.lower()
        if wl in stop:
            continue
        freq[wl] = freq.get(wl, 0) + 1
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:max_k]]


extract_keywords = extract_entities
