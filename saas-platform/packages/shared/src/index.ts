export type DubbingStep =
  | "uploaded"
  | "extract-audio"
  | "transcribe"
  | "translate"
  | "duration-fit"
  | "rewrite-long-segments"
  | "generate-tts"
  | "sync-audio"
  | "qa"
  | "export-video"
  | "completed"
  | "failed";

export type FitStatus = "fits" | "rewritten" | "needs_review" | "failed";

export type SegmentDto = {
  id: string;
  index: number;
  startMs: number;
  endMs: number;
  sourceText: string;
  translatedText?: string;
  optimizedText?: string;
  availableMs: number;
  estimatedSpeechMs?: number;
  ttsAssetKey?: string;
  fitStatus: FitStatus;
};

export type ProgressEvent = {
  projectId: string;
  step: DubbingStep;
  percent: number;
  message: string;
  completedSegments?: number;
  totalSegments?: number;
};

