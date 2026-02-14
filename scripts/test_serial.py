"""Test serial output (dry run if device not connected)."""

from vibe_eyes.output import VIBEOutput

device = VIBEOutput(port='/dev/ttyUSB0')

if device.connect():
    print("Device connected!")
    
    # Test different emotional states
    test_vibes = [
        [0.9, 0.8, 0.7, 0.5, 0.8],  # Happy, excited
        [0.2, 0.8, 0.3, 0.4, 0.6],  # Frustrated, aroused
        [0.5, 0.3, 0.5, 0.8, 0.9],  # Neutral, complex
    ]
    
    for vibe in test_vibes:
        device.send(vibe)
        print(f"Sent: {vibe}")
    
    device.close()
else:
    print("No device - dry run mode")
