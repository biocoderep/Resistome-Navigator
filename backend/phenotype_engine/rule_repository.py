"""Rule repository loader and validator - Module 1E v1.0.0"""

import json
from pathlib import Path
from typing import Dict, List, Any

class RuleRepository:
    """Loads and validates rules from JSON repository."""
    
    def __init__(self, json_path: Path):
        self.path = json_path
        self._raw_data = {}
        self.gene_rules = []
        self.mutation_rules = []
        self.mechanism_rules = []
        self.combo_rules = []
        self.load()
        
    def load(self):
        """Load and partition rules into respective engines."""
        if not self.path.exists():
            raise FileNotFoundError(f"Rule repo not found: {self.path}")
            
        with open(self.path, "r", encoding="utf-8") as f:
            self._raw_data = json.load(f)
            
        rules = self._raw_data.get("rules", [])
        
        self.gene_rules = [r for r in rules if r["rule_type"] in ("gene", "gene_family")]
        self.mutation_rules = [r for r in rules if r["rule_type"].startswith("mutation")]
        self.mechanism_rules = [r for r in rules if r["rule_type"] == "mechanism"]
        self.combo_rules = [r for r in rules if r["rule_type"] == "combinatorial"]
