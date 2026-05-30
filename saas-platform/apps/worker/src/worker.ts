import { Worker } from "bullmq";
import { DubbingPipeline } from "./workflow/dubbing-pipeline";

const pipeline = new DubbingPipeline();

const worker = new Worker(
  "dub-job",
  async (job) => {
    if (job.name !== "process-project") return;
    await pipeline.processProject(job.data.projectId, (progress) => job.updateProgress(progress));
  },
  {
    connection: { url: process.env.REDIS_URL ?? "redis://localhost:6379" },
    concurrency: Number(process.env.WORKER_CONCURRENCY ?? 1),
    lockDuration: 30 * 60 * 1000
  }
);

worker.on("completed", (job) => console.log(`completed ${job.id}`));
worker.on("failed", (job, err) => console.error(`failed ${job?.id}`, err));

