"""FM-Index engine stub for fast sequence lookup."""

class FMIndex:
    """Stub for FMIndex search engine."""
    
    def __init__(self, sequence: str):
        self.sequence = sequence
        
    def count(self, pattern: str) -> int:
        """Count occurrences of pattern."""
        return self.sequence.count(pattern)
        
    def locate(self, pattern: str) -> list[int]:
        """Locate start positions of pattern (1-based)."""
        positions = []
        start = 0
        while True:
            idx = self.sequence.find(pattern, start)
            if idx == -1:
                break
            positions.append(idx + 1)
            start = idx + 1
        return positions
