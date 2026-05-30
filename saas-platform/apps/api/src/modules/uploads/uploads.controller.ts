import { Body, Controller, Post } from "@nestjs/common";
import { UploadsService } from "./uploads.service";

@Controller("uploads")
export class UploadsController {
  constructor(private readonly uploads: UploadsService) {}

  @Post("presign")
  createPresignedUpload(@Body() body: { projectId: string; fileName: string; contentType: string }) {
    return this.uploads.createPresignedUpload(body);
  }
}

