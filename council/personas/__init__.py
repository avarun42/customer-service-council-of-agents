"""Persona blocks for each council agent.

Imported by `council/personas.py` (the legacy single-file location) so
existing code keeps working, while the per-persona files in this
package serve as the canonical, individually-readable source.
"""
from .mira import MIRA
from .bex import BEX
from .doro import DORO
from .pria import PRIA
from .cass import CASS
from .crier import CRIER

ALL_PERSONAS = {
    "mira": MIRA,
    "bex": BEX,
    "doro": DORO,
    "pria": PRIA,
    "cass": CASS,
    "crier": CRIER,
}
