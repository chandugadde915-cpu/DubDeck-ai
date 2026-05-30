import { GetObjectCommand, PutObjectCommand, S3Client } from "@aws-sdk/client-s3";
import { createReadStream, createWriteStream } from "node:fs";
import { pipeline } from "node:stream/promises";

export class StorageService {
  private client: S3Client | null = null;

  private getClient() {
    this.client ??= new S3Client({
      region: process.env.S3_REGION ?? "us-east-1",
      endpoint: process.env.S3_ENDPOINT || undefined,
      forcePathStyle: process.env.S3_FORCE_PATH_STYLE === "true",
      credentials: process.env.S3_ACCESS_KEY_ID
        ? {
            accessKeyId: process.env.S3_ACCESS_KEY_ID,
            secretAccessKey: process.env.S3_SECRET_ACCESS_KEY ?? ""
          }
        : undefined
    });
    return this.client;
  }

  async uploadFile(key: string, filePath: string, contentType: string) {
    await this.getClient().send(
      new PutObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: key,
        Body: createReadStream(filePath),
        ContentType: contentType
      })
    );
    return key;
  }

  async downloadFile(key: string, destinationPath: string) {
    const result = await this.getClient().send(
      new GetObjectCommand({
        Bucket: process.env.S3_BUCKET,
        Key: key
      })
    );
    if (!result.Body) throw new Error(`Storage object not found: ${key}`);
    await pipeline(result.Body as NodeJS.ReadableStream, createWriteStream(destinationPath));
    return destinationPath;
  }
}

