from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Segment:
    number: int
    start: float
    end: float
    english: str
    hindi: str = ""
    fit_status: str = "Waiting"
    rate_used: str = ""
    problem: str = ""
    generated_audio: str = ""
    final_duration: float = 0.0
    speed_ratio: float = 1.0

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


def seconds_to_srt_time(seconds: float) -> str:
    millis = int(round(seconds * 1000))
    hours, remainder = divmod(millis, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def srt_time_to_seconds(value: str) -> float:
    hours, minutes, rest = value.split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def write_srt(path: Path, segments: list[Segment], language: str = "english") -> None:
    lines: list[str] = []
    for index, segment in enumerate(segments, start=1):
        text = segment.hindi if language == "hindi" else segment.english
        lines.extend(
            [
                str(index),
                f"{seconds_to_srt_time(segment.start)} --> {seconds_to_srt_time(segment.end)}",
                text.strip(),
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_srt(path: Path) -> list[Segment]:
    if not path.exists():
        return []
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return []

    blocks = re.split(r"\n\s*\n", content)
    segments: list[Segment] = []
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start_text, end_text = [part.strip() for part in lines[1].split("-->")]
        text = " ".join(lines[2:])
        segments.append(
            Segment(
                number=int(lines[0]) if lines[0].isdigit() else len(segments) + 1,
                start=srt_time_to_seconds(start_text),
                end=srt_time_to_seconds(end_text),
                english=text,
            )
        )
    return segments


def segments_to_rows(segments: list[Segment]) -> list[dict[str, object]]:
    return [
        {
            "Segment": segment.number,
            "Start": seconds_to_srt_time(segment.start).replace(",", "."),
            "End": seconds_to_srt_time(segment.end).replace(",", "."),
            "English text": segment.english,
            "Hindi text": segment.hindi,
            "Fit status": segment.fit_status,
            "Final duration": round(segment.final_duration, 2) if segment.final_duration else "",
        }
        for segment in segments
    ]


def segment_to_dict(segment: Segment) -> dict[str, object]:
    return {
        "number": segment.number,
        "start": segment.start,
        "end": segment.end,
        "duration": segment.duration,
        "english": segment.english,
        "hindi": segment.hindi,
        "fit_status": segment.fit_status,
        "rate_used": segment.rate_used,
        "problem": segment.problem,
        "generated_audio": segment.generated_audio,
        "final_duration": segment.final_duration,
        "speed_ratio": segment.speed_ratio,
    }


def dict_to_segment(data: dict[str, object]) -> Segment:
    return Segment(
        number=int(data["number"]),
        start=float(data["start"]),
        end=float(data["end"]),
        english=str(data.get("english", "")),
        hindi=str(data.get("hindi", "")),
        fit_status=str(data.get("fit_status", "Waiting")),
        rate_used=str(data.get("rate_used", "")),
        problem=str(data.get("problem", "")),
        generated_audio=str(data.get("generated_audio", "")),
        final_duration=float(data.get("final_duration") or 0.0),
        speed_ratio=float(data.get("speed_ratio") or 1.0),
    )
