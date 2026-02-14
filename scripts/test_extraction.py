"""Test VIBE extraction without serial device."""

from vibe_eyes.extractor import VIBEExtractor
from vibe_eyes.window import TranscriptWindow

extractor = VIBEExtractor()
window = TranscriptWindow()

test_texts = [
    "I am incredibly excited about this amazing project!",
    "This is very frustrating and nothing seems to work.",
    "The methodology involves sophisticated neural architectures.",
    "Yeah, um, so like, I dunno, maybe?",
]

for text in test_texts:
    vibe = extractor.extract(text)
    print(f"\nText: {text}")
    print(f"VIBE: V={vibe[0]:.2f} A={vibe[1]:.2f} D={vibe[2]:.2f} Cx={vibe[3]:.2f} Ch={vibe[4]:.2f}")
