"""FastAPI server for VIBE-Eyes."""

import asyncio
import time
import logging
import nltk
import concurrent.futures
import numpy as np

from collections import deque
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .extractor import VIBEExtractor
from .amplifier import CinematicAmplifier
from .ollama_anchor import OllamaAnchor
from .blender import VIBEBlender
from .output import VIBEOutput


# --------------------------------------------------
# Ensure NLTK tokenizer availability
# --------------------------------------------------
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="VIBE-Eyes", version="1.0.0")


# --------------------------------------------------
# Global Configuration
# --------------------------------------------------
PASSION = 2.25
DRAMA = 0.65
BASELINE_WINDOW_WORDS = 100


# --------------------------------------------------
# Runtime Globals
# --------------------------------------------------
fast_extractor = None
amplifier = None
slow_anchor = None
blender = None
device = None

context_buffer: deque = deque(maxlen=200)
last_vibe = [0.5, 0.5, 0.5, 0.5, 0.8]
transcript_count = 0

# Slow integration state
_slow_pending: bool = False
_slow_in_flight: bool = False

executor = concurrent.futures.ThreadPoolExecutor(
    max_workers=1,
    thread_name_prefix="ollama",
)


# --------------------------------------------------
# Models
# --------------------------------------------------
class TranscriptPayload(BaseModel):
    text: str
    influence: Optional[float] = None


# --------------------------------------------------
# Helpers
# --------------------------------------------------
def require_ready():
    if not all([fast_extractor, amplifier, slow_anchor, blender, device]):
        raise HTTPException(status_code=503, detail="VIBE-Eyes not ready")


def _get_recent_context_text(max_words: int = BASELINE_WINDOW_WORDS) -> str:
    if not context_buffer:
        return ""
    window_words = list(context_buffer)[-max_words:]
    return " ".join(window_words)


def _has_settled_to_baseline(threshold: float = 0.02) -> bool:
    diff = np.abs(blender.current - blender.baseline)
    return np.all(diff < threshold)


# --------------------------------------------------
# Startup
# --------------------------------------------------
@app.on_event("startup")
async def startup():
    global fast_extractor, amplifier, slow_anchor, blender, device

    logger.info("Initializing VIBE-Eyes components...")

    try:
        fast_extractor = VIBEExtractor()
        amplifier = CinematicAmplifier(verbose=False)
        slow_anchor = OllamaAnchor()
        blender = VIBEBlender()
        device = VIBEOutput(dry_run=False)

        if device.connect():
            logger.info("Device connected")
        else:
            logger.warning("Device not connected — dry run")

        logger.info("VIBE-Eyes ready")

        asyncio.create_task(_startup_warm_baseline())
        asyncio.create_task(decay_loop())

    except Exception as e:
        logger.exception(f"Startup failed: {e}")


# --------------------------------------------------
# Decay Loop (State Driven)
# --------------------------------------------------
async def decay_loop():
    global _slow_pending, _slow_in_flight

    while True:
        vibe = blender.tick()
        device.send(vibe)

        if (
            _slow_pending
            and not _slow_in_flight
            and _has_settled_to_baseline()
        ):
            context_text = _get_recent_context_text(BASELINE_WINDOW_WORDS)
            if context_text:
                _slow_in_flight = True
                asyncio.create_task(_trigger_slow_baseline(context_text))

        await asyncio.sleep(0.1)


async def _trigger_slow_baseline(context_text: str):
    """
    Requests a slow baseline, then applies/logs it here (the true "integration" moment).
    """
    global _slow_pending, _slow_in_flight, last_vibe

    try:
        ollama_vibe = await _update_baseline_async(context_text)

        if ollama_vibe:
            blender.apply_baseline(ollama_vibe)

            final_vibe = blender.current.tolist()
            last_vibe = final_vibe

            try:
                device.send(final_vibe)
            except Exception as e:
                logger.warning(f"Device send failed during baseline apply: {e}")

            ts_apply = time.strftime("%H:%M:%S")
            logger.info(
                f"[{ts_apply}] 🔮 NEW baseline → "
                f"V:{final_vibe[0]:.2f} A:{final_vibe[1]:.2f} "
                f"D:{final_vibe[2]:.2f} Cx:{final_vibe[3]:.2f} "
                f"Co:{final_vibe[4]:.2f}"
            )
        else:
            logger.warning("🔮 BAD baseline request!")

    finally:
        _slow_pending = False
        _slow_in_flight = False


# --------------------------------------------------
# Health
# --------------------------------------------------
@app.get("/health")
async def health():
    return {"status": "ok"}


# --------------------------------------------------
# Status
# --------------------------------------------------
@app.get("/status")
async def status() -> Dict[str, Any]:
    require_ready()

    current = blender.current.tolist()

    return {
        "context_words": len(context_buffer),
        "transcript_count": transcript_count,
        "slow_pending": _slow_pending,
        "slow_in_flight": _slow_in_flight,
        "last_vibe": {
            "valence": current[0],
            "arousal": current[1],
            "dominance": current[2],
            "complexity": current[3],
            "coherence": current[4],
        },
    }


# --------------------------------------------------
# Transcript Endpoint (FULL TELEMETRY RESTORED)
# --------------------------------------------------
@app.post("/transcript")
async def receive_transcript(payload: TranscriptPayload) -> Dict[str, Any]:
    require_ready()

    global last_vibe, transcript_count, _slow_pending

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Empty text")

    if payload.influence is not None and not 0 <= payload.influence <= 1:
        raise HTTPException(status_code=400, detail="influence must be between 0.0 and 1.0")

    words = text.split()
    context_buffer.extend(words)
    transcript_count += 1

    sentences = nltk.sent_tokenize(text)
    timestamp = time.strftime("%H:%M:%S")

    logger.info(
        f"[{timestamp}] 📝 Transcript #{transcript_count}: "
        f"\"{text[:80]}{'...' if len(text) > 80 else ''}\""
    )

    influence_used = (
        payload.influence
        if payload.influence is not None
        else VIBEBlender.DEFAULT_INFLUENCE
    )

    for sentence in sentences:
        # 1) NATURAL
        natural = np.array(fast_extractor.extract(sentence))

        # 2) PASSION
        post_passion = amplifier.amplify_passion(natural, PASSION)

        # 3) DRAMA
        post_drama = amplifier.snap_drama(post_passion, DRAMA)

        # Identify cinematic target (for logging only)
        cinema_state = None
        if DRAMA > 0:
            nearest = amplifier.get_nearest_exemplar(post_passion, k=1)[0]
            cinema_state = {
                "name": nearest[0],
                "source": nearest[1],
                "distance": nearest[2],
            }

        # 4) APPLY BURST
        blender.apply_burst(post_drama, influence=influence_used)

        baseline = blender.baseline.copy()
        last_vibe = blender.current.tolist()

        try:
            device.send(last_vibe)
        except Exception as e:
            logger.warning(f"Device send failed: {e}")

        # TELEMETRY
        logger.info("--------------------------------------------------")
        logger.info(f"[{timestamp}] TEXT     : \"{sentence}\"")

        logger.info(
            f"[{timestamp}] NATURAL  : "
            f"V:{natural[0]:.3f} A:{natural[1]:.3f} D:{natural[2]:.3f} "
            f"Cx:{natural[3]:.3f} Co:{natural[4]:.3f}"
        )

        logger.info(
            f"[{timestamp}] PASSION  : "
            f"V:{post_passion[0]:.3f} A:{post_passion[1]:.3f} D:{post_passion[2]:.3f} "
            f"Cx:{post_passion[3]:.3f} Co:{post_passion[4]:.3f}"
        )

        if cinema_state:
            logger.info(
                f"[{timestamp}] DRAMA    : "
                f"V:{post_drama[0]:.3f} A:{post_drama[1]:.3f} D:{post_drama[2]:.3f} "
                f"Cx:{post_drama[3]:.3f} Co:{post_drama[4]:.3f} "
                f"→ {cinema_state['name']} "
                f"(src: {cinema_state['source']}, dist:{cinema_state['distance']:.3f})"
            )
        else:
            logger.info(
                f"[{timestamp}] DRAMA    : "
                f"V:{post_drama[0]:.3f} A:{post_drama[1]:.3f} D:{post_drama[2]:.3f} "
                f"Cx:{post_drama[3]:.3f} Co:{post_drama[4]:.3f}"
            )

        logger.info(
            f"[{timestamp}] BASELINE : "
            f"V:{baseline[0]:.3f} A:{baseline[1]:.3f} D:{baseline[2]:.3f} "
            f"Cx:{baseline[3]:.3f} Co:{baseline[4]:.3f}"
        )

        logger.info("--------------------------------------------------")

    # ✅ One slow integration per transcript payload (not per sentence)
    _slow_pending = True

    return {
        "vibe": last_vibe,
        "influence_used": influence_used,
        "sentences_processed": len(sentences),
        "transcript_count": transcript_count,
        "context_words": len(context_buffer),
    }


# --------------------------------------------------
# Slow Baseline Update (REQUEST ONLY)
# --------------------------------------------------
async def _update_baseline_async(context_text: str):
    """
    Requests a baseline from Ollama and returns it.
    Applying/logging happens in _trigger_slow_baseline().
    """
    timestamp = time.strftime("%H:%M:%S")
    window_words = len(context_text.split())

    logger.info(f"[{timestamp}] 🔮 Request new baseline (window_words={window_words})")

    try:
        loop = asyncio.get_event_loop()
        ollama_vibe = await loop.run_in_executor(
            executor,
            slow_anchor.extract_baseline,
            context_text,
        )

        logger.info(f"[{timestamp}] 🔮 raw response: {ollama_vibe}")
        return ollama_vibe

    except Exception as e:
        logger.warning(f"[{timestamp}] 🔮 BASELINE UPDATE ERROR: {e}")
        return None


async def _startup_warm_baseline():
    logger.info("🔥 Startup baseline warmup triggered")
    try:
        # warmup requests + applies immediately (fine; it's startup)
        context = "Say hello to Reachy."
        ollama_vibe = await _update_baseline_async(context)

        if ollama_vibe:
            blender.apply_baseline(ollama_vibe)
            final_vibe = blender.current.tolist()
            global last_vibe
            last_vibe = final_vibe

            try:
                device.send(final_vibe)
            except Exception as e:
                logger.warning(f"Device send failed during startup warm apply: {e}")

            ts_apply = time.strftime("%H:%M:%S")
            logger.info(
                f"[{ts_apply}] 🔮 NEW baseline → "
                f"V:{final_vibe[0]:.2f} A:{final_vibe[1]:.2f} "
                f"D:{final_vibe[2]:.2f} Cx:{final_vibe[3]:.2f} "
                f"Co:{final_vibe[4]:.2f}"
            )
        else:
            logger.warning("🔥 Startup warmup got no baseline")

        logger.info("🔥 Startup baseline warmup complete")
    except Exception as e:
        logger.warning(f"🔥 Startup warmup failed: {e}")

