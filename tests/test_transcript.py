import pytest

from app.services.transcript import TranscriptError, parse_transcript


def test_parse_plain_text_into_sentence_segments():
    segments = parse_transcript("Good morning. How are you?", "text")

    assert [segment.segment_id for segment in segments] == ["text-0001", "text-0002"]
    assert segments[0].text == "Good morning."
    assert segments[0].start_seconds is None


def test_parse_vtt_preserves_cue_timestamps_and_text():
    content = """WEBVTT

00:00:01.000 --> 00:00:03.500
Good morning, everyone.

00:01:02.000 --> 00:01:04.000
What do you think?
"""

    segments = parse_transcript(content, "vtt")

    assert len(segments) == 2
    assert segments[1].start_seconds == 62
    assert segments[1].end_seconds == 64
    assert segments[1].text == "What do you think?"


def test_reject_vtt_without_timestamped_cues():
    with pytest.raises(TranscriptError, match="No timestamped"):
        parse_transcript("WEBVTT\n\nJust some text.", "vtt")


def test_reject_vtt_with_invalid_timestamp():
    with pytest.raises(TranscriptError, match="invalid cue timestamp"):
        parse_transcript("WEBVTT\n\n00:70.000 --> 00:80.000\nHello.", "vtt")
