import type { ProgressEvent } from "@dubdeck/shared";
import { FfmpegService } from "../workers/ffmpeg.service";
import { OpenAiMediaService } from "../workers/openai-media.service";
import { QaService } from "../workers/qa.service";

export class DubbingPipeline {
  private readonly ffmpeg = new FfmpegService();
  private readonly openai = new OpenAiMediaService();
  private readonly qa = new QaService();

  async processProject(projectId: string, progress: (event: ProgressEvent) => Promise<void>) {
    await progress({ projectId, step: "extract-audio", percent: 8, message: "Extracting source audio." });
    const audio = await this.ffmpeg.extractAudio(projectId);

    await progress({ projectId, step: "transcribe", percent: 18, message: "Generating timestamped transcript." });
    const transcript = await this.openai.transcribe(audio);

    await progress({ projectId, step: "translate", percent: 32, message: "Translating transcript." });
    const translated = await this.openai.translateSegments(transcript, "target language");

    await progress({ projectId, step: "duration-fit", percent: 44, message: "Checking segment durations." });
    const fit = await this.openai.durationFit(translated);

    await progress({ projectId, step: "rewrite-long-segments", percent: 54, message: "Rewriting only long segments." });
    const optimized = await this.openai.rewriteLongSegments(fit);

    await progress({ projectId, step: "generate-tts", percent: 68, message: "Generating target-language TTS." });
    const tts = await this.openai.generateTtsSegments(optimized);

    await progress({ projectId, step: "sync-audio", percent: 78, message: "Synchronizing audio to timestamps." });
    const mixedAudio = await this.ffmpeg.syncAudio(projectId, tts);

    await progress({ projectId, step: "qa", percent: 88, message: "Running automated QA." });
    await this.qa.validate(projectId, optimized, mixedAudio);

    await progress({ projectId, step: "export-video", percent: 96, message: "Exporting final MP4." });
    await this.ffmpeg.exportVideo(projectId, mixedAudio);

    await progress({ projectId, step: "completed", percent: 100, message: "Completed." });
  }
}

