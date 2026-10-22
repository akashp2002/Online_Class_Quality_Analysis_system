from __future__ import annotations

import re
from dataclasses import dataclass


TIMESTAMP = re.compile(
    r"^(?:(\d+):)?([0-5]?\d):([0-5]\d)\.(\d{3})\s+-->\s+"
    r"(?:(\d+):)?([0-5]?\d):([0-5]\d)\.(\d{3})(?:\s+.*)?$"
)
SENTENCE_BOUNDARY = re.compile(r"(?<=[.!?])\s+")


class TranscriptError(ValueError):
    pass


@dataclass(frozen=True)
class TranscriptSegment:
    segment_id: str
    text: str
    start_seconds: float | None = None
    end_seconds: float | None = None


def _seconds(match: re.Match[str], offset: int) -> float:
    hours = int(match.group(offset) or 0)
    minutes = int(match.group(offset + 1))
    seconds = int(match.group(offset + 2))
    milliseconds = int(match.group(offset + 3))
    return hours * 3600 + minutes * 60 + seconds + milliseconds / 1000


def parse_transcript(content: str, transcript_format: str) -> list[TranscriptSegment]:
    if not content.strip():
        raise TranscriptError("Transcript is empty.")

    if transcript_format == "text":
        sentences = [
            text.strip()
            for text in SENTENCE_BOUNDARY.split(content.strip())
            if text.strip()
        ]
        if not sentences:
            raise TranscriptError("Transcript does not contain readable text.")
        return [
            TranscriptSegment(segment_id=f"text-{index:04d}", text=sentence)
            for index, sentence in enumerate(sentences, start=1)
        ]

    if transcript_format != "vtt":
        raise TranscriptError("Transcript format must be text or vtt.")

    normalized = content.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", normalized)
    segments: list[TranscriptSegment] = []

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines or lines[0] == "WEBVTT" or lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue

        timestamp_line_index = next(
            (index for index, line in enumerate(lines) if "-->" in line), None
        )
        if timestamp_line_index is None:
            continue

        timestamp_match = TIMESTAMP.fullmatch(lines[timestamp_line_index])
        if timestamp_match is None:
            raise TranscriptError("VTT contains an invalid cue timestamp.")

        start = _seconds(timestamp_match, 1)
        end = _seconds(timestamp_match, 5)
        cue_text = " ".join(lines[timestamp_line_index + 1 :]).strip()
        if not cue_text:
            continue
        if end < start:
            raise TranscriptError("VTT cue end time must not precede its start time.")

        segments.append(
            TranscriptSegment(
                segment_id=f"vtt-{len(segments) + 1:04d}",
                text=cue_text,
                start_seconds=start,
                end_seconds=end,
            )
        )

    if not segments:
        raise TranscriptError("No timestamped transcript cues were found in the VTT.")
    return segments
