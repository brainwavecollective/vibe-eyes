"""Output handler for VIBE values using reachy-eyes package."""

import logging
from typing import List

logger = logging.getLogger(__name__)


class VIBEOutput:
    """Send VIBE values to Reachy Eyes via reachy_eyes package."""
    
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.eyes = None
        
    def connect(self) -> bool:
        """Initialize connection to Reachy Eyes device."""
        if self.dry_run:
            logger.info("Dry-run mode: no device connection")
            return True
        
        try:
            import reachy_eyes
            self.eyes = reachy_eyes.create({"simulation": False})
            
            if self.eyes:
                logger.info("Connected to Reachy Eyes device")
                return True
            else:
                logger.warning("Reachy Eyes not available - using dry-run mode")
                self.dry_run = True
                return True
                
        except Exception as e:
            logger.warning(f"Failed to connect to Reachy Eyes: {e} (using dry-run mode)")
            self.dry_run = True
            return True
    
    def send(self, vibe: List[float]) -> bool:
        """
        Send VIBE values to device.
        
        Format: "VIBE V A D Cx Ch" (space-delimited floats 0.0-1.0)
        
        Args:
            vibe: [Valence, Arousal, Dominance, Complexity, Coherence]
        """
        # Format: VIBE v a d cx ch
        message = f"VIBE {vibe[0]:.1f} {vibe[1]:.1f} {vibe[2]:.1f} {vibe[3]:.1f} {vibe[4]:.1f}"
        
        if self.dry_run:
            logger.debug(f"DRY-RUN: {message}")
            return True
        
        if self.eyes is None:
            logger.warning("Eyes not connected")
            return False
        
        try:
            # Send VIBE command directly to device
            self.eyes._device.send_command(message)
            logger.debug(f"Sent: {message}")
            return True
        except Exception as e:
            logger.error(f"Failed to send VIBE: {e}")
            return False
    
    def close(self) -> None:
        """Close connection to device."""
        if self.eyes:
            try:
                self.eyes.cleanup()
                logger.info("Eyes connection closed")
            except Exception as e:
                logger.error(f"Error closing eyes: {e}")
