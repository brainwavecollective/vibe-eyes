"""VIBE extraction: Valence, Arousal, Dominance, Complexity, Coherence."""

import numpy as np
from pathlib import Path
from typing import List, Tuple
from sentence_transformers import SentenceTransformer
from textstat import flesch_kincaid_grade
import nltk


class VIBEExtractor:
    """Extract natural psychological VIBE from text."""

    def __init__(
        self,
        lexicon_path: str = "data/NRC-VAD-Lexicon-v2.1/NRC-VAD-Lexicon-v2.1.txt",
        model_name: str = "all-MiniLM-L6-v2"
    ):
        self.vad_lexicon = self._load_nrc_vad(lexicon_path)
        self.embedder = SentenceTransformer(model_name)

        # Ensure tokenizer availability
        try:
            nltk.data.find("tokenizers/punkt")
        except LookupError:
            nltk.download("punkt", quiet=True)

    def _load_nrc_vad(self, path: str) -> dict:
        """Load NRC-VAD lexicon: word -> [v, a, d]"""
        lexicon = {}
        lexicon_file = Path(path)

        if not lexicon_file.exists():
            raise FileNotFoundError(f"NRC-VAD lexicon not found at {path}")

        with open(lexicon_file, encoding="utf-8") as f:
            next(f)  # skip header
            for line in f:
                parts = line.strip().split("\t")
                if len(parts) < 4:
                    continue

                word = parts[0].lower()
                try:
                    v = (float(parts[1]) + 1.0) / 2.0
                    a = (float(parts[2]) + 1.0) / 2.0
                    d = (float(parts[3]) + 1.0) / 2.0
                    lexicon[word] = [v, a, d]
                except ValueError:
                    continue

        return lexicon

    def extract(self, text: str) -> List[float]:
        """
        Extract natural psychological VIBE from text.

        Returns:
            [Valence, Arousal, Dominance, Complexity, Coherence]
            Each value scaled 0.0–1.0
        """

        v, a, d = self._get_vad(text)
        complexity = self._get_complexity(text)
        coherence = self._get_coherence(text)

        return [
            float(np.clip(v, 0, 1)),
            float(np.clip(a, 0, 1)),
            float(np.clip(d, 0, 1)),
            float(np.clip(complexity, 0, 1)),
            float(np.clip(coherence, 0, 1)),
        ]

    def _get_vad(self, text: str) -> Tuple[float, float, float]:
        words = nltk.word_tokenize(text.lower())

        vad_values = []
        weights = []

        for w in words:
            if w in self.vad_lexicon:
                vad = self.vad_lexicon[w]
                vad_values.append(vad)

                intensity = (
                    abs(vad[0] - 0.5)
                    + abs(vad[1] - 0.5)
                    + abs(vad[2] - 0.5)
                )
                weights.append((intensity + 0.01) ** 2)
            else:
                vad_values.append([0.5, 0.5, 0.5])
                weights.append(0.01)

        if not vad_values:
            return 0.5, 0.5, 0.5

        vad_array = np.array(vad_values)
        weights_array = np.array(weights)

        weighted_vad = np.average(
            vad_array, axis=0, weights=weights_array
        )

        return tuple(weighted_vad)

    def _get_complexity(self, text: str) -> float:
        try:
            fk_grade = flesch_kincaid_grade(text)
            return min(1.0, max(0.0, fk_grade / 20.0))
        except Exception:
            return 0.5

    def _get_coherence(self, text: str) -> float:
        sentences = nltk.sent_tokenize(text)

        if len(sentences) < 2:
            return 0.8

        embeddings = self.embedder.encode(sentences)

        similarities = [
            np.dot(embeddings[i], embeddings[i + 1])
            for i in range(len(embeddings) - 1)
        ]

        coherence = (np.mean(similarities) + 1) / 2
        return float(coherence)

