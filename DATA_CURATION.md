# Musings on Cinematic Mood Data for the VIBE engine

## The Problem

Generative conversational language is broad and varied. VAD scores derived from real dialogue cluster near neutral, as most conversation is emotionally understated. This creates a hard problem for expressive display: how do you find reliable anchor points in that space without exhaustive coverage?

The supposition was that anchoring references could stand in place of comprehensive coverage.

## Why Cinema

Filmmakers are by definition obsessed with visual representations of emotion. Color grading, lighting design, and composition are mature artistic disciplines with deep, consistent conventions. A horror scene and a romance scene don't accidentally look different because those choices are deliberate, studied, and culturally legible. 

Why formalize color theory from scratch when we can borrow existing understanding?*  

*These particular mappings are a limited reflection of predominantly Western cinematic conventions and are not intended to be universal emotional truths.

## How It Was Built

Using a similar approach to the slow loop in the emotion engine (asking an LLM to interpret scenes through a VAD+CC lens) a curated set of cinematically representative scenes were mapped to emotional coordinates and color parameters. An LLM's non-deterministic interpretation provides both a reasonable approximation and a breadth of consideration that is difficult to replicate with rigid rules. Artists often operate through tacit knowledge that is difficult to define. Leveraging LLM interpretation is a cheap way of accessing that understanding without having to formalize it.

Additional anchor points were added to improve color range and coverage. The dataset was iterated until the downstream model could reliably express emotionally meaningful colors.

The result is a small [dataset](https://huggingface.co/datasets/danielritchie/cinematic-mood-palette) of ~80 curated mappings which produces the desired results.

## How It Is Used

The same dataset serves two distinct roles within VIBE-Eyes: A gravitational field for interpolation at the edge, and as a training signal for deriving color from emotion at the embedded tier.

**At the edge (cinematic amplification):**
The engine applies amplification in two stages. First, a nonlinear radial gain (passion) increases the magnitude of Valence, Arousal, and Dominance. Second, the amplified vector is compared to the cinematic dataset using weighted Euclidean distance (default k=1) to find the nearest exemplar. The vector is then linearly interpolated toward that exemplar by a configurable drama factor. A value of 0.0 applies no cinematic shift, and 1.0 produces a full snap. This provides independent control over amplification of weak emotional signals (passion) and alignment to cinematic refernces (drama).

**At the embedded device (color model training):**
The same dataset was used to train the on-device color generating [model](https://huggingface.co/danielritchie/vibe-color-model) to generalize the relationship between emotional coordinates and cinematographic color expression, enabling color generation for any incoming VAD+CC vector.

## What This Claims

The dataset is a pragmatic artifact built to solve a specific problem; it works well enough. The goal was fitness for purpose, not empirical superiority.

There are no claims that this approach is more robust or theoretically grounded than alternatives. The claim is narrower and more transparent: using extremely limited compute resources and a deliberately small reference structure, the system produces subjectively satisfying color output in real time.

That it achieves this effectively is the definitive measure of its success.

---

Dataset: [danielritchie/cinematic-mood-palette](https://huggingface.co/datasets/danielritchie/cinematic-mood-palette)  
Model trained on this data: [danielritchie/vibe-color-model](https://huggingface.co/danielritchie/vibe-color-model)
