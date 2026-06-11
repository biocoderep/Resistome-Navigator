import pytest
import uuid
from unittest.mock import patch, MagicMock
from backend.tasks.batch_tasks import run_single_isolate_pipeline

def test_run_single_isolate_pipeline_string_id():
    """Regression test for Error 1: String IDs raise ValueError instead of crashing with UnboundLocalError."""
    # Use a string ID instead of a UUID object
    string_id = "12345678-1234-5678-1234-567812345678"
    
    # We mock SessionLocal to simulate a DB where the sample is not found
    with patch('backend.tasks.batch_tasks.SessionLocal') as mock_session_local:
        mock_db = MagicMock()
        # Mock db.scalars(...).first() to return None
        mock_db.scalars.return_value.first.return_value = None
        mock_session_local.return_value = mock_db
        
        # When passed a string, it should catch the ValueError and return an error dict
        result = run_single_isolate_pipeline(string_id)
        assert result == {"sample_id": string_id, "status": "error", "error": f"sample {string_id} not found"}
