from __future__ import annotations

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_convert_form_to_payload_minimal():
    resp = client.post(
        "/api/convert-form-to-payload",
        json={"form_type": "annual_leave", "form_data": {"title": "t"}},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("success") is True
    assert data.get("form_type") == "annual_leave"
    assert isinstance(data.get("api_payload"), dict)
