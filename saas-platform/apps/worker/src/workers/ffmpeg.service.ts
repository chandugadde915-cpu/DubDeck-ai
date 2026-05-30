import { execa } from "execa";
import type { SegmentDto } from "@dubdeck/shared";

export class FfmpegService {
  async extractAudio(projectId: string) {
    console.log("extract audio", projectId);
    return `/tmp/${projectId}/source.wav`;
  }

  async syncAudio(projectId: string, segments: SegmentDto[]) {
    console.log("sync audio", projectId, segments.length);
    return `/tmp/${projectId}/final_mixed_audio.wav`;
  }

  async exportVideo(projectId: string, finalAudioPath: string) {
    const inputVideo = `/tmp/${projectId}/input.mp4`;
    const outputVideo = `/tmp/${projectId}/output_hindi.mp4`;
    await execa("ffmpeg", [
      "-y",
      "-i",
      inputVideo,
      "-i",
      finalAudioPath,
      "-map",
      "0:v",
      "-map",
      "1:a",
      "-c:v",
      "copy",
      "-c:a",
      "aac",
      "-shortest",
      outputVideo
    ]);
    return outputVideo;
  }
}

