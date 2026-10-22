from __future__ import annotations

import re
from dataclasses import dataclass

from app.services.transcript import TranscriptSegment


@dataclass(frozen=True)
class Cue:
    pattern: re.Pattern[str]
    excerpt: str


@dataclass(frozen=True)
class DimensionRule:
    key: str
    name: str
    weight: int
    positive: tuple[Cue, ...]
    improvement: tuple[Cue, ...]
    modality: str


def _cues(*phrases: str) -> tuple[Cue, ...]:
    return tuple(
        Cue(re.compile(re.escape(phrase), re.IGNORECASE), phrase)
        for phrase in phrases
    )


RULES = (
    DimensionRule(
        "rapport",
        "Rapport building",
        18,
        _cues("good morning", "good afternoon", "how are you", "welcome to class", "welcome everyone"),
        _cues("we will skip introductions", "no time for introductions"),
        "transcript",
    ),
    DimensionRule(
        "engagement",
        "Student engagement and individual attention",
        20,
        _cues("what do you think", "can you tell me", "raise your hand", "does anyone have a question", "tell me your answer"),
        _cues("you do not need to answer", "no questions are allowed"),
        "transcript",
    ),
    DimensionRule(
        "teaching_clarity",
        "Teaching clarity",
        17,
        _cues("let me explain", "for example", "step by step", "does that make sense", "any doubts"),
        _cues("I will not explain", "it does not matter if you understand"),
        "transcript",
    ),
    DimensionRule(
        "class_structure",
        "Class structure",
        15,
        _cues("today we will", "let us begin", "let's begin", "to conclude", "before we finish"),
        _cues("we will skip the introduction", "we have no conclusion"),
        "transcript",
    ),
    DimensionRule(
        "communication",
        "Communication style",
        12,
        _cues("well done", "thank you", "please", "great job"),
        _cues("shut up", "you are stupid", "you are foolish"),
        "transcript",
    ),
    DimensionRule(
        "visual_setup",
        "Visual setup",
        10,
        (),
        (),
        "video",
    ),
    DimensionRule(
        "homework",
        "Homework and follow-up",
        8,
        _cues("homework", "assignment", "for next class", "complete this before our next class"),
        _cues("there will be no follow-up", "I will not give you any homework"),
        "transcript",
    ),
)

def _find_evidence(
    segments: list[TranscriptSegment], cues: tuple[Cue, ...], polarity: str, dimension: str
) -> list[dict]:
    evidence: list[dict] = []
    seen: set[tuple[str, str]] = set()

    for segment in segments:
        for cue in cues:
            match = cue.pattern.search(segment.text)
            if match is None:
                continue
            excerpt = segment.text.strip()
            identity = (segment.segment_id, polarity)
            if identity in seen:
                continue
            seen.add(identity)
            evidence.append(
                {
                    "evidence_id": f"{dimension}-{polarity}-{segment.segment_id}",
                    "segment_id": segment.segment_id,
                    "start_seconds": segment.start_seconds,
                    "end_seconds": segment.end_seconds,
                    "excerpt": excerpt,
                    "matched_text": match.group(0),
                    "polarity": polarity,
                }
            )
            break
    return evidence


def _dimension_result(rule: DimensionRule, segments: list[TranscriptSegment]) -> dict:
    positive = _find_evidence(segments, rule.positive, "positive", rule.key)
    improvement = _find_evidence(segments, rule.improvement, "improvement", rule.key)
    evidence = positive + improvement
    if positive and improvement:
        evidence_pattern = "mixed_cues"
    elif positive:
        evidence_pattern = "positive_cues"
    elif improvement:
        evidence_pattern = "improvement_cues"
    else:
        evidence_pattern = "no_cues_found"

    return {
        "key": rule.key,
        "name": rule.name,
        "weight": rule.weight,
        "modality": rule.modality,
        "score": None,
        "status": "cues_found" if evidence else "insufficient_evidence",
        "evidence_pattern": evidence_pattern,
        "rationale": (
            "Exact phrase cues are shown below; this prototype has not evaluated their context or effectiveness."
            if evidence
            else "No matching phrase was found; this is not evidence that the behavior was absent."
        ),
        "evidence": evidence,
    }


def _recommendation(dimension: dict) -> str | None:
    if not any(item["polarity"] == "improvement" for item in dimension["evidence"]):
        return None
    recommendations = {
        "rapport": "Reserve a brief opening for greetings and student introductions before starting the activity.",
        "engagement": "Invite students to participate and allow time for their responses.",
        "teaching_clarity": "Pause to check understanding and explain again when students signal confusion.",
        "class_structure": "Set a clear opening and leave time to summarize the session before it ends.",
        "communication": "Use respectful, encouraging language when addressing students.",
        "homework": "State any follow-up task and when students should complete it.",
    }
    return recommendations.get(dimension["key"])


def analyze_transcript(segments: list[TranscriptSegment]) -> dict:
    dimensions = [_dimension_result(rule, segments) for rule in RULES]
    dimensions_with_cues = sum(item["status"] == "cues_found" for item in dimensions)

    observations = []
    for dimension in dimensions:
        for item in dimension["evidence"]:
            observations.append(
                {
                    "observation": (
                        f"Positive cue for {dimension['name'].lower()}."
                        if item["polarity"] == "positive"
                        else f"Potential improvement cue for {dimension['name'].lower()}."
                    ),
                    "evidence_id": item["evidence_id"],
                    "segment_id": item["segment_id"],
                    "start_seconds": item["start_seconds"],
                    "end_seconds": item["end_seconds"],
                    "excerpt": item["excerpt"],
                    "interpretation": (
                        "This exact phrase matched a predefined transcript cue. Context and teaching effectiveness "
                        "have not been evaluated."
                    ),
                    "recommendation": _recommendation(dimension)
                    if item["polarity"] == "improvement"
                    else None,
                }
            )

    return {
        "category": None,
        "overall_score": None,
        "rating_status": "not_assessed",
        "evidence_coverage": {
            "dimensions_with_cues": dimensions_with_cues,
            "total_dimensions": len(dimensions),
        },
        "summary": (
            "This first-stage prototype finds exact transcript phrases only. It does not assess teaching quality "
            "or assign a quality category."
        ),
        "dimensions": dimensions,
        "observations": observations,
        "limitations": [
            "The prototype matches a small set of explicit phrases; it does not understand context or reliably detect paraphrases.",
            "A phrase match is evidence that the phrase appears, not proof that the teaching behavior was effective.",
            "A missing phrase is not evidence that a behavior did not occur.",
            "Visual setup cannot be assessed from a transcript and is marked insufficient.",
            "Weights and category thresholds are not applied in this stage; any future values require review and are not official Humaniti standards.",
        ],
        "transcript_segments": [
            {
                "segment_id": segment.segment_id,
                "start_seconds": segment.start_seconds,
                "end_seconds": segment.end_seconds,
                "text": segment.text,
            }
            for segment in segments
        ],
    }
