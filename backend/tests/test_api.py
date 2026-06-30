from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check_route():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data

def test_pipeline_missing_payloads_error():
    # Sending empty request without required file multipart raises validation error
    response = client.post("/pipeline/run")
    assert response.status_code == 422
    assert "detail" in response.json()

def test_pipeline_run_success_with_enrichment():
    csv_content = b"first_name,last_name,email\nAlex,Rivera,alex@example.com"
    
    from app.config.settings import settings
    with patch("google.genai.Client") as mock_client_cls, patch.object(settings, "gemini_api_key", "test_key"):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = """{
            "professional_summary": "Alex Rivera is a Software Engineer...",
            "core_strengths": ["Python"],
            "recommended_roles": ["Software Engineer"],
            "technical_highlights": ["Highlights"],
            "leadership_signals": ["Initiative"],
            "communication_signals": ["Articulate"],
            "interview_focus_areas": ["Focus"],
            "potential_concerns": ["None"],
            "recruiter_insights": "Recruiter thoughts"
        }"""
        mock_response.usage_metadata = MagicMock()
        mock_response.usage_metadata.total_token_count = 50
        
        from unittest.mock import AsyncMock
        mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value = mock_client

        response = client.post(
            "/pipeline/run",
            files=[("files", ("candidate.csv", csv_content, "text/csv"))],
            data={"enable_enrichment": "true"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "COMPLETED"
        assert data["candidate_id"] is not None
        
        # Verify candidate can be retrieved
        retrieved_response = client.get(f"/pipeline/candidate/{data['candidate_id']}")
        assert retrieved_response.status_code == 200
        candidate_data = retrieved_response.json()
        assert candidate_data["full_name"] == "Alex Rivera"
        assert candidate_data["metadata"]["ai_enrichment_enabled"] is True
