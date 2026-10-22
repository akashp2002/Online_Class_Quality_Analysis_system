from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    assert client.get("/health").json() == {"status": "ok"}


def test_analysis_endpoint_returns_report_with_valid_evidence_references():
    response = client.post(
        "/api/analyses",
        json={
            "transcript": "Good morning. What do you think? Let me explain step by step. "
            "Today we will begin. Well done. Homework is to read page ten.",
            "transcript_format": "text",
        },
    )

    assert response.status_code == 200
    report = response.json()
    segment_ids = {segment["segment_id"] for segment in report["transcript_segments"]}
    assert report["analysis_id"]
    assert report["category"] is None
    assert report["overall_score"] is None
    assert report["rating_status"] == "not_assessed"
    assert all(item["segment_id"] in segment_ids for item in report["observations"])


def test_analysis_endpoint_rejects_vtt_without_cues():
    response = client.post(
        "/api/analyses",
        json={"transcript": "WEBVTT\n\nNo cues.", "transcript_format": "vtt"},
    )

    assert response.status_code == 422


def test_vtt_analysis_includes_recording_time_for_evidence():
    response = client.post(
        "/api/analyses",
        json={
            "transcript": "WEBVTT\n\n00:00:12.000 --> 00:00:14.000\nGood morning, everyone.",
            "transcript_format": "vtt",
        },
    )

    assert response.status_code == 200
    evidence = response.json()["observations"][0]
    assert evidence["start_seconds"] == 12
