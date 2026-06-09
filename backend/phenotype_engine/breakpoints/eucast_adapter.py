"""EUCAST Breakpoint Adapter - Module 1E v1.0.0"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict, Tuple

@dataclass
class BreakpointRecord:
    drug: str
    species_group: str
    s_threshold: Optional[float]
    r_threshold: Optional[float]
    i_range: Optional[str]
    version: str
    source: str
    notes: Optional[str] = None

class EUCASTAdapter:
    def __init__(self, version: str = "v13.0"):
        self.version = version
        self.table: Dict[Tuple[str, Optional[str]], BreakpointRecord] = {}
        # We inject a mock breakpoint for testing
        self._load_stub_data()

    def _load_stub_data(self):
        # drug, scope -> BreakpointRecord
        self.table[("ciprofloxacin", "Enterobacterales")] = BreakpointRecord(
            drug="ciprofloxacin", species_group="Enterobacterales",
            s_threshold=0.25, r_threshold=0.5, i_range="0.25 < MIC <= 0.5",
            version=self.version, source="EUCAST", notes="Expert rules apply"
        )
        self.table[("ceftriaxone", "Enterobacterales")] = BreakpointRecord(
            drug="ceftriaxone", species_group="Enterobacterales",
            s_threshold=1.0, r_threshold=2.0, i_range="1.0 < MIC <= 2.0",
            version=self.version, source="EUCAST"
        )

    def get_breakpoint(self, drug: str, species: Optional[str] = None, organism_group: Optional[str] = None) -> Optional[BreakpointRecord]:
        for scope in [species, organism_group, "Enterobacterales", "All streptococci", None]:
            bp = self.table.get((drug.lower(), scope))
            if bp:
                return bp
        return None
