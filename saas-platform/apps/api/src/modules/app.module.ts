import { Module } from "@nestjs/common";
import { ConfigModule } from "@nestjs/config";
import { ProjectsModule } from "./projects/projects.module";
import { UploadsModule } from "./uploads/uploads.module";
import { JobsModule } from "./jobs/jobs.module";

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    ProjectsModule,
    UploadsModule,
    JobsModule
  ]
})
export class AppModule {}

