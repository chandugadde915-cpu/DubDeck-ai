import { Injectable } from "@nestjs/common";
import { JobsService } from "../jobs/jobs.service";

@Injectable()
export class ProjectsService {
  constructor(private readonly jobs: JobsService) {}

  async listProjects() {
    return { items: [], nextCursor: null };
  }

  async getProject(id: string) {
    return { id, status: "DRAFT", progress: 0 };
  }

  async createProject(body: { title: string; sourceLanguage: string; targetLanguage: string }) {
    return {
      id: crypto.randomUUID(),
      status: "DRAFT",
      ...body
    };
  }

  async startProcessing(projectId: string) {
    await this.jobs.enqueueDubbingJob(projectId);
    return { projectId, status: "PROCESSING" };
  }
}

