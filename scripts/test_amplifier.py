#!/usr/bin/env python3
"""
Test script for CinematicAmplifier

Demonstrates:
- Natural vs amplified extraction
- Different amplification levels
- Mood matching
- Edge cases
"""

import sys
from pathlib import Path

# Add parent directory to path so we can import vibe_eyes
sys.path.insert(0, str(Path(__file__).parent.parent))

from vibe_eyes.extractor import VIBEExtractor
import numpy as np


def print_header(title: str):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80)


def print_vibe(label: str, vibe: list, indent: str = ""):
    """Print VIBE values with labels"""
    dims = ["Valence", "Arousal", "Dominance", "Complexity", "Coherence"]
    print(f"{indent}{label}")
    for dim, val in zip(dims, vibe):
        bar = "█" * int(val * 20)
        print(f"{indent}  {dim:11s}: {val:.3f} {bar}")


def test_amplification_levels():
    """Test different amplification levels on the same text"""
    print_header("TEST 1: Amplification Levels")
    
    extractor = VIBEExtractor(enable_amplification=True)
    
    test_cases = [
        "I'm feeling anxious about the presentation tomorrow.",
        "This makes me absolutely furious!",
        "I'm so happy and excited about this!",
        "The sky is blue today.",
        "Feeling melancholy as autumn leaves fall."
    ]
    
    amp_levels = [0.0, 0.5, 0.9, 1.0, 1.5]
    
    for text in test_cases:
        print(f"\n📝 Text: \"{text}\"")
        print("-" * 80)
        
        for amp in amp_levels:
            vibe = extractor.extract(text, amp=amp)
            
            # Calculate intensity (distance from neutral 0.5)
            intensity = np.mean([abs(v - 0.5) for v in vibe[:3]])  # VAD only
            
            print(f"\n  amp={amp:.1f} | intensity={intensity:.3f}")
            print(f"    VAD+CC: [{', '.join(f'{v:.3f}' for v in vibe)}]")


def test_mood_matching():
    """Test which cinematic moods texts match to"""
    print_header("TEST 2: Mood Matching")
    
    extractor = VIBEExtractor(enable_amplification=True)
    
    test_cases = [
        ("I'm terrified and can't think straight", 0.9),
        ("Feeling peaceful and content", 0.9),
        ("This is so exciting and fun!", 0.9),
        ("I'm deeply sad about what happened", 0.9),
        ("Curious about how this works", 0.7),
        ("Absolutely enraged by this injustice", 1.2),
    ]
    
    for text, amp in test_cases:
        print(f"\n📝 Text: \"{text}\"")
        print(f"   Amplification: {amp}")
        print("-" * 80)
        
        vibe = extractor.extract(text, amp=amp)
        print(f"   VIBE: [{', '.join(f'{v:.2f}' for v in vibe)}]")
        
        # Get nearest moods
        moods = extractor.get_nearest_mood(text, amp=amp, k=3)
        print(f"\n   Nearest cinematic moods:")
        for i, (name, source, dist) in enumerate(moods, 1):
            print(f"     {i}. '{name}' from {source}")
            print(f"        (distance: {dist:.3f})")


def test_natural_vs_cinematic():
    """Compare natural and cinematic readings side-by-side"""
    print_header("TEST 3: Natural vs Cinematic Comparison")
    
    extractor = VIBEExtractor(enable_amplification=True)
    
    test_cases = [
        "I'm happy",
        "I'm sad",
        "I'm angry",
        "I'm scared",
        "I'm calm and relaxed",
    ]
    
    for text in test_cases:
        print(f"\n📝 Text: \"{text}\"")
        print("-" * 80)
        
        natural = extractor.extract(text, amp=0.0)
        cinematic = extractor.extract(text, amp=0.9)
        
        print_vibe("Natural (amp=0.0):", natural, indent="  ")
        print()
        print_vibe("Cinematic (amp=0.9):", cinematic, indent="  ")
        
        # Calculate delta
        delta = [c - n for c, n in zip(cinematic, natural)]
        print(f"\n  Delta: [{', '.join(f'{d:+.3f}' for d in delta)}]")


def test_edge_cases():
    """Test edge cases and boundary conditions"""
    print_header("TEST 4: Edge Cases")
    
    extractor = VIBEExtractor(enable_amplification=True)
    
    edge_cases = [
        ("Empty-ish", ".", 0.9),
        ("Single word", "happy", 0.9),
        ("Neutral", "The table is wooden.", 0.9),
        ("Extreme positive", "I'm ecstatic, overjoyed, thrilled, delighted!", 1.5),
        ("Extreme negative", "Devastated, heartbroken, miserable, hopeless.", 1.5),
        ("Mixed emotions", "I'm happy but also worried and uncertain.", 0.9),
        ("Very long", "This is a longer text with multiple sentences. " * 10, 0.9),
    ]
    
    for label, text, amp in edge_cases:
        print(f"\n{label}: \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
        print(f"Amplification: {amp}")
        
        try:
            vibe = extractor.extract(text, amp=amp)
            print(f"  VIBE: [{', '.join(f'{v:.3f}' for v in vibe)}]")
            
            if amp > 0:
                moods = extractor.get_nearest_mood(text, amp=amp, k=1)
                print(f"  Nearest: '{moods[0][0]}' from {moods[0][1]}")
        except Exception as e:
            print(f"  ❌ Error: {e}")


def test_verbose_mode():
    """Demonstrate verbose diagnostic output"""
    print_header("TEST 5: Verbose Diagnostics")
    
    print("\nInitializing with verbose mode...")
    extractor = VIBEExtractor(enable_amplification=True, amplifier_verbose=True)
    
    text = "I'm feeling anxious and overwhelmed by everything."
    print(f"\n📝 Text: \"{text}\"")
    print("\nExtracting with amp=0.9, verbose=True:")
    print("-" * 80)
    
    vibe = extractor.extract(text, amp=0.9, verbose=True)
    
    print("\n" + "-" * 80)
    print(f"Final output: [{', '.join(f'{v:.3f}' for v in vibe)}]")


def test_amplification_sweep():
    """Sweep through amplification range to show progression"""
    print_header("TEST 6: Amplification Sweep (0.0 → 2.0)")
    
    extractor = VIBEExtractor(enable_amplification=True)
    
    text = "I'm excited about this project!"
    print(f"\n📝 Text: \"{text}\"")
    print("\nAmplification sweep:")
    print("-" * 80)
    
    print(f"{'amp':>5s} | {'V':>5s} {'A':>5s} {'D':>5s} {'Cx':>5s} {'Co':>5s} | {'Intensity':>9s}")
    print("-" * 80)
    
    for amp in np.arange(0.0, 2.1, 0.2):
        vibe = extractor.extract(text, amp=amp)
        intensity = np.mean([abs(v - 0.5) for v in vibe[:3]])
        
        v, a, d, cx, co = vibe
        print(f"{amp:5.1f} | {v:5.3f} {a:5.3f} {d:5.3f} {cx:5.3f} {co:5.3f} | {intensity:9.3f}")


def test_without_amplification():
    """Test that natural extraction still works without amplifier"""
    print_header("TEST 7: Natural Extraction (No Amplifier)")
    
    print("\nInitializing without amplification...")
    extractor = VIBEExtractor(enable_amplification=False)
    
    test_cases = [
        "I'm happy",
        "I'm sad",
        "I'm angry",
    ]
    
    for text in test_cases:
        vibe = extractor.extract(text)
        print(f"\n📝 \"{text}\"")
        print(f"   Natural VIBE: [{', '.join(f'{v:.3f}' for v in vibe)}]")
        print(f"   (amp parameter ignored when amplification disabled)")


def main():
    """Run all tests"""
    print("\n" + "█" * 80)
    print("  CINEMATIC AMPLIFIER TEST SUITE")
    print("█" * 80)
    
    tests = [
        ("Amplification Levels", test_amplification_levels),
        ("Mood Matching", test_mood_matching),
        ("Natural vs Cinematic", test_natural_vs_cinematic),
        ("Edge Cases", test_edge_cases),
        ("Verbose Diagnostics", test_verbose_mode),
        ("Amplification Sweep", test_amplification_sweep),
        ("Without Amplification", test_without_amplification),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
        except KeyboardInterrupt:
            print("\n\n⚠️  Test interrupted by user")
            break
        except Exception as e:
            print(f"\n❌ Test '{name}' failed with error:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "█" * 80)
    print("  TEST SUITE COMPLETE")
    print("█" * 80 + "\n")


if __name__ == "__main__":
    main()
