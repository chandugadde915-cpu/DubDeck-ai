import OpenAI from "openai";
import type { SegmentDto } from "@dubdeck/shared";

export class OpenAiMediaService {
  private client: OpenAI | null = null;

  private getClient() {
    this.client ??= new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
    return this.client;
  }

  async transcribe(audioPath: string): Promise<SegmentDto[]> {
    // For long videos, chunk audio before calling transcription APIs and merge timestamps.
    // Keep OpenAI audio upload limits in mind when choosing chunk duration.
    console.log("transcribe", audioPath, this.getClient() ? "openai-ready" : "missing-client");
    return [];
  }

  async translateSegments(segments: SegmentDto[], targetLanguage: string): Promise<SegmentDto[]> {
    console.log("translate", segments.length, targetLanguage);
    return segments;
  }

  async durationFit(segments: SegmentDto[]): Promise<SegmentDto[]> {
    return segments.map((segment) => ({
      ...segment,
      availableMs: segment.endMs - segment.startMs,
      estimatedSpeechMs: estimateSpeechMs(segment.translatedText ?? segment.sourceText)
    }));
  }

  async rewriteLongSegments(segments: SegmentDto[]): Promise<SegmentDto[]> {
    // Only rewrite segments whose estimated duration exceeds available timing.
    return segments.map((segment) => {
      if ((segment.estimatedSpeechMs ?? 0) <= segment.availableMs) return segment;
      return { ...segment, fitStatus: "needs_review" };
    });
  }

  async generateTtsSegments(segments: SegmentDto[]): Promise<SegmentDto[]> {
    console.log("tts", segments.length);
    return segments;
  }
}

function estimateSpeechMs(text: string) {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.ceil((words / 2.4) * 1000);
}

