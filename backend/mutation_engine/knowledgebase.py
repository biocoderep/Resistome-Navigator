"""Knowledgebase loader for curated resistance mutations."""

import json
from pathlib import Path
from functools import lru_cache
from typing import Optional


class KnowledgebaseLoader:
    """Load and cache mutation knowledgebase."""
    
    def __init__(self, kb_path: Optional[Path] = None):
        """Initialize loader with optional path override."""
        if kb_path is None:
            kb_path = Path(__file__).parent / "data" / "mutation_knowledgebase.json"
        
        self.kb_path = kb_path
        self._kb_data = None
    
    @property
    def kb(self) -> dict:
        """Lazy-load knowledgebase."""
        if self._kb_data is None:
            self.load()
        return self._kb_data
    
    def load(self) -> dict:
        """Load knowledgebase from JSON file."""
        if not self.kb_path.exists():
            raise FileNotFoundError(f"Knowledgebase not found: {self.kb_path}")
        
        with open(self.kb_path) as f:
            self._kb_data = json.load(f)
        
        return self._kb_data
    
    def get_entries(self, gene_name: Optional[str] = None) -> list:
        """Get KB entries, optionally filtered by gene."""
        entries = self.kb.get("entries", [])
        
        if gene_name:
            return [e for e in entries if e.get("gene") == gene_name]
        
        return entries
    
    def lookup_mutation(self, gene: str, protein_pos: int, 
                       alt_aa: str) -> Optional[dict]:
        """Find exact mutation match in KB."""
        for entry in self.get_entries(gene):
            if (entry.get("protein_position") == protein_pos and
                entry.get("alt_amino_acid") == alt_aa):
                return entry
        return None
    
    def lookup_position(self, gene: str, protein_pos: int) -> list:
        """Find all mutations at a given position."""
        return [e for e in self.get_entries(gene)
                if e.get("protein_position") == protein_pos]
    
    def get_version(self) -> str:
        """Get knowledgebase version."""
        return self.kb.get("schema_version", "unknown")
