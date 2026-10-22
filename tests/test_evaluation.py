from app.services.evaluation import analyze_transcript
from app.services.transcript import parse_transcript


def test_evidence_quotes_are_exact_and_refer_to_existing_segments():
    segments = parse_transcript(
        "Good morning. What do you think? Let me explain step by step. "
        "Today we will learn fractions. Well done. For homework, read chapter two.",
        "text",
    )

    report = analyze_transcript(segments)
    segment_ids = {segment.segment_id for segment in segments}
    for observation in report["observations"]:
        assert observation["segment_id"] in segment_ids
        source = next(item.text for item in segments if item.segment_id == observation["segment_id"])
        assert observation["excerpt"] == source

    assert report["category"] is None
    assert report["overall_score"] is None
    assert report["rating_status"] == "not_assessed"
    assert report["evidence_coverage"]["dimensions_with_cues"] > 0


def test_missing_visual_evidence_is_not_scored_as_negative():
    report = analyze_transcript(parse_transcript("Good morning.", "text"))
    visual = next(item for item in report["dimensions"] if item["key"] == "visual_setup")

    assert visual["score"] is None
    assert visual["status"] == "insufficient_evidence"
    assert report["category"] is None


def test_conflicting_cues_remain_visible_without_inventing_a_score():
    report = analyze_transcript(
        parse_transcript("Good morning. We will skip introductions.", "text")
    )
    rapport = next(item for item in report["dimensions"] if item["key"] == "rapport")

    assert rapport["score"] is None
    assert rapport["evidence_pattern"] == "mixed_cues"
    assert {item["polarity"] for item in rapport["evidence"]} == {"positive", "improvement"}


def test_improvement_recommendation_requires_matching_evidence():
    report = analyze_transcript(
        parse_transcript("We will skip introductions. Today we will learn. What do you think?", "text")
    )
    rapport_observation = next(
        item for item in report["observations"] if item["evidence_id"].startswith("rapport-improvement")
    )

    assert rapport_observation["recommendation"] is not None
