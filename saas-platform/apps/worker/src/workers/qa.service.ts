import type { SegmentDto } from "@dubdeck/shared";

export class QaService {
  async validate(projectId: string, segments: SegmentDto[], finalAudioPath: string) {
    const findings = [
      ...this.findMissingText(segments),
      ...this.findTimingProblems(segments),
      ...this.findPlaceholderText(segments)
    ];
    return {
      projectId,
      finalAudioPath,
      passed: findings.length === 0,
      findings
    };
  }

  private findMissingText(segments: SegmentDto[]) {
    return segments
      .filter((segment) => !(segment.optimizedText || segment.translatedText || segment.sourceText).trim())
      .map((segment) => ({ severity: "error", segmentId: segment.id, message: "Missing segment text." }));
  }

  private findTimingProblems(segments: SegmentDto[]) {
    return segments
      .filter((segment) => (segment.estimatedSpeechMs ?? 0) > segment.availableMs * 1.1)
      .map((segment) => ({ severity: "warning", segmentId: segment.id, message: "Segment may exceed timing window." }));
  }

  private findPlaceholderText(segments: SegmentDto[]) {
    return segments
      .filter((segment) => /\b(todo|placeholder|\[.*?\])\b/i.test(segment.optimizedText ?? segment.translatedText ?? ""))
      .map((segment) => ({ severity: "error", segmentId: segment.id, message: "Placeholder text detected." }));
  }
}

