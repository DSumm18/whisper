"""Application utilities for the Whisper-style voice typing workflow."""

from .output import OutputManager, InjectionError, normalise_transcript

__all__ = ["OutputManager", "InjectionError", "normalise_transcript"]
