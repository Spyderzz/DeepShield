"""Quick smoke test for sensationalism + manipulation detection."""
import sys
sys.path.insert(0, ".")

from services.text_service import score_sensationalism, detect_manipulation_indicators

# --- Sensationalism ---
text1 = "BREAKING: You wont believe this SHOCKING truth! Experts confirm the most DEVASTATING scandal exposed!!!"
s = score_sensationalism(text1)
print(f"Sensationalism: score={s.score} level={s.level}")
print(f"  excl={s.exclamation_count} caps={s.caps_word_count} clickbait={s.clickbait_matches} emotional={s.emotional_word_count} superlative={s.superlative_count}")
assert s.score > 50, f"Expected high sensationalism, got {s.score}"
assert s.level in ("Medium", "High"), f"Expected Medium/High, got {s.level}"
print("  PASS")

# --- Manipulation ---
text2 = "Sources say that experts confirm the shocking truth. Allegedly, everyone knows this is a proven fact."
m = detect_manipulation_indicators(text2)
print(f"\nManipulation indicators: {len(m)} found")
for ind in m:
    print(f"  [{ind.severity}] {ind.pattern_type}: \"{ind.matched_text}\"")
assert len(m) >= 3, f"Expected >=3 indicators, got {len(m)}"
print("  PASS")

# --- Clean text ---
text3 = "The weather today is sunny with clear skies in New Delhi."
s2 = score_sensationalism(text3)
m2 = detect_manipulation_indicators(text3)
print(f"\nClean text: sensationalism={s2.score} ({s2.level}), manipulation={len(m2)}")
assert s2.score < 20, f"Expected low sensationalism for clean text, got {s2.score}"
assert len(m2) == 0, f"Expected 0 manipulation indicators for clean text, got {len(m2)}"
print("  PASS")

print("\nAll tests passed!")
