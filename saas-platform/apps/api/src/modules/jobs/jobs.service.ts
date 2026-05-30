import { Injectable } from "@nestjs/common";
import { Queue } from "bullmq";

@Injectable()
export class JobsService {
  private readonly queue = new Queue("dub-job", {
    connection: { url: process.env.REDIS_URL ?? "redis://localhost:6379" }
  });

  async enqueueDubbingJob(projectId: string) {
    return this.queue.add(
      "process-project",
      { projectId },
      {
        attempts: 3,
        backoff: { type: "exponential", delay: 5000 },
        removeOnComplete: 100,
        removeOnFail: 500
      }
    );
  }
}

