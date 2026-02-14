#!/bin/bash

cd ~/github/brainwavecollective/vibe-eyes

echo "========================================"
echo "VIBE-Eyes Influence Parameter Test"
echo "========================================"
echo ""

# Test 1: Establish baseline
echo "=== TEST 1: Establish Neutral Baseline ==="
echo "Sending neutral text to establish starting point..."
for i in {1..3}; do
  curl -s -X POST http://localhost:8001/transcript \
    -H "Content-Type: application/json" \
    -d '{"text": "The system is operating normally with standard parameters and configurations."}' \
    > /dev/null
  sleep 0.3
done
echo "Baseline established"
echo ""

# Check current state
echo "Current VIBE:"
curl -s http://localhost:8001/status | jq '.last_vibe'
echo ""
sleep 2

# Test 2: Gentle influence (default 0.15)
echo "=== TEST 2: Gentle Influence (α=0.15, default) ==="
echo "Sending positive text with default gentle influence..."
for i in {1..5}; do
  echo "  Burst $i/5"
  curl -s -X POST http://localhost:8001/transcript \
    -H "Content-Type: application/json" \
    -d '{"text": "I am incredibly happy and excited! This is wonderful and amazing!"}' | jq '.vibe'
  sleep 0.5
done
echo "→ Should see gradual drift toward positive (slow accumulation)"
echo ""
sleep 2

# Test 3: Medium influence (0.5)
echo "=== TEST 3: Medium Influence (α=0.5) ==="
echo "Sending negative text with medium influence..."
for i in {1..3}; do
  echo "  Burst $i/3"
  curl -s -X POST http://localhost:8001/transcript \
    -H "Content-Type: application/json" \
    -d '{"text": "This is terrible and frustrating! I hate this awful situation!", "influence": 0.5}' | jq '.vibe'
  sleep 0.5
done
echo "→ Should see faster shift toward negative (50/50 blend)"
echo ""
sleep 2

# Test 4: Strong influence (0.7 - turn change)
echo "=== TEST 4: Strong Influence (α=0.7, turn change) ==="
echo "Sending positive text with strong influence (simulating speaker change)..."
for i in {1..3}; do
  echo "  Burst $i/3"
  curl -s -X POST http://localhost:8001/transcript \
    -H "Content-Type: application/json" \
    -d '{"text": "Actually, I absolutely love this! So thrilled and delighted!", "influence": 0.7}' | jq '.vibe'
  sleep 0.5
done
echo "→ Should see rapid shift toward positive (70% new, 30% old)"
echo ""
sleep 2

# Test 5: Near-full reset (0.95)
echo "=== TEST 5: Near-Full Reset (α=0.95) ==="
echo "Sending neutral text with near-full reset..."
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "The parameters are nominal and systems are functioning adequately.", "influence": 0.95}' | jq '.vibe'
echo "→ Should snap almost immediately to neutral"
echo ""
sleep 2

# Test 6: Full reset (1.0)
echo "=== TEST 6: Full Reset (α=1.0) ==="
echo "Sending excited text with full reset..."
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "AMAZING! INCREDIBLE! FANTASTIC! BRILLIANT!", "influence": 1.0}' | jq '.vibe'
echo "→ Should snap completely to very positive (100% new, 0% old)"
echo ""
sleep 2

# Test 7: Comparison - Same text, different influences
echo "=== TEST 7: Same Text, Varying Influence ==="
echo "Sending identical angry text with different influence values..."
echo ""

echo "α=0.1 (very gentle):"
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "I am extremely frustrated and angry about this!", "influence": 0.1}' | jq '.vibe'
sleep 1

echo "α=0.3 (gentle-medium):"
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "I am extremely frustrated and angry about this!", "influence": 0.3}' | jq '.vibe'
sleep 1

echo "α=0.5 (medium):"
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "I am extremely frustrated and angry about this!", "influence": 0.5}' | jq '.vibe'
sleep 1

echo "α=0.7 (strong):"
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "I am extremely frustrated and angry about this!", "influence": 0.7}' | jq '.vibe'
sleep 1

echo "α=0.9 (very strong):"
curl -s -X POST http://localhost:8001/transcript \
  -H "Content-Type: application/json" \
  -d '{"text": "I am extremely frustrated and angry about this!", "influence": 0.9}' | jq '.vibe'
echo ""
echo "→ Should see increasing magnitude of shift with higher influence"
echo ""
sleep 2

# Test 8: Momentum visualization
echo "=== TEST 8: Momentum State ==="
curl -s http://localhost:8001/status | jq '{
  current_vibe: .last_vibe,
  baseline: .blender.baseline,
  momentum: .blender.momentum,
  momentum_magnitude: .blender.momentum_magnitude
}'
echo ""

# Summary
echo "========================================"
echo "INFLUENCE TEST COMPLETE"
echo "========================================"
echo ""
echo "Key Observations:"
echo "  - α=0.15 (default): Gentle drift, builds slowly"
echo "  - α=0.5: Medium blend, noticeable shifts"
echo "  - α=0.7: Strong blend, rapid transitions"
echo "  - α=0.95-1.0: Near/full snap, immediate change"
echo ""
echo "Check server logs for detailed VIBE values!"
