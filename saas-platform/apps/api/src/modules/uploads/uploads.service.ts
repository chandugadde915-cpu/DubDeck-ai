import { Injectable } from "@nestjs/common";

@Injectable()
export class UploadsService {
  async createPresignedUpload(body: { projectId: string; fileName: string; contentType: string }) {
    const key = `projects/${body.projectId}/source/${Date.now()}-${body.fileName}`;
    return {
      key,
      uploadUrl: `/api/mock-upload/${encodeURIComponent(key)}`,
      method: "PUT",
      headers: { "content-type": body.contentType }
    };
  }
}

