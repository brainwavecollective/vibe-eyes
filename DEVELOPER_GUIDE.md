## Technical Development Guide

This guide covers software, API use, and related integration. For setting up the hardware and configuring the environment to run the service, see the [Edge Setup Guide](EDGE_SETUP.md)

### Send transcript text
```bash
curl -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "I am feeling really excited about this project!"}'
```

## Influence Parameter

The `influence` parameter controls how much each new burst affects accumulated momentum:

**Value Range:** 0.0 - 1.0

**Behavior:**
- `0.0` - No influence (momentum only decays, new burst ignored)
- `0.15` - **Default** - Gentle accumulation (conversational drift)
- `0.7` - Strong blend (typical for turn changes)
- `1.0` - Full reset (100% new burst, 0% old momentum)

**Formula:**
```
new_momentum = old_momentum × (1 - influence) + delta × influence
```

**Usage Examples:**
```bash
# Gentle accumulation (default)
curl -X POST http://localhost:8001/transcript \
  -d '{"text": "continuing the conversation..."}'

# Strong blend for speaker change
curl -X POST http://localhost:8001/transcript \
  -d '{"text": "new topic!", "influence": 0.7}'

# Custom blend
curl -X POST http://localhost:8001/transcript \
  -d '{"text": "moderate shift", "influence": 0.4}'
```

**App Integration:**
```python
# Define constants
INFLUENCE_GENTLE = 0.15
INFLUENCE_MODERATE = 0.5
INFLUENCE_STRONG = 0.7
INFLUENCE_FULL = 0.95

# Use based on context
if speaker_changed:
    influence = INFLUENCE_STRONG
elif topic_changed:
    influence = INFLUENCE_MODERATE
else:
    influence = None  # Use default (0.15)
```

### Check status
```bash
curl http://localhost:8001/status
```

## Configuration

Edit `vibe_eyes/output.py` to change serial port:
```python
device = VIBEOutput(port='/dev/ttyUSB0', baudrate=115200)
```

## Output Format

Serial output: `VIBE 0.7 0.8 0.6 0.5 0.9\n`

Values are space-delimited floats (0.0-1.0):
- Valence (negative → positive emotion)
- Arousal (calm → excited)
- Dominance (submissive → dominant)
- Complexity (simple → complex ideas)
- Coherence (scattered → well-organized)

## Integration

Add to conversation app:
```python
# In openai_realtime.py
import httpx

vadcc_client = httpx.AsyncClient()

# When transcript received:
await vadcc_client.post(
    "http://localhost:8001/transcript",
    json={"text": transcript}
)
```

## Testing
```bash
# Test extraction only
python scripts/test_extraction.py

# Test serial output
python scripts/test_serial.py
```
