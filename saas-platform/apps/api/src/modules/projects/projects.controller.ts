import { Body, Controller, Get, Param, Post } from "@nestjs/common";
import { ProjectsService } from "./projects.service";

@Controller("projects")
export class ProjectsController {
  constructor(private readonly projects: ProjectsService) {}

  @Get()
  list() {
    return this.projects.listProjects();
  }

  @Get(":id")
  get(@Param("id") id: string) {
    return this.projects.getProject(id);
  }

  @Post()
  create(@Body() body: { title: string; sourceLanguage: string; targetLanguage: string }) {
    return this.projects.createProject(body);
  }

  @Post(":id/process")
  process(@Param("id") id: string) {
    return this.projects.startProcessing(id);
  }
}

