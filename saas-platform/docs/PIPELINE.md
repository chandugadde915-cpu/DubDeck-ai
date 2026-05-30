# Processing Pipeline

## Segment Contract

Every transcript segment stores:

```json
{
  "id": "segment-id",
  "index": 1,
  "startMs": 5200,
  "endMs": 8900,
  "sourceText": "Check the vessel permit before entry.",
  "translatedText": "प्रवेश से पहले vessel permit जांचें।",
  "optimizedText": "प्रवेश से पहले vessel permit जांचें।",
  "availableMs": 3700,
  "estimatedSpeechMs": 3400,
  "ttsAssetKey": "projects/.../segment-0001.wav",
  "fitStatus": "fits"
}
```

## Duration Optimization

1. Estimate duration for translated text.
2. If the segment fits, do not rewrite.
3. If it exceeds available timing, rewrite only that segment.
4. Preserve meaning, proper nouns, glossary terms, and natural speech.
5. Mark status:
   - `fits`
   - `rewritten`
   - `needs_review`

## QA Checks

QA must not re-translate content. It validates generated artifacts:

- Missing transcript segments
- Missing TTS clips
- Segment audio longer than timing window
- Clipped audio
- Silent gaps above threshold
- Placeholder text such as `[music]`, `TODO`, empty translations
- Final MP4 missing audio/video streams
- FFmpeg render failure
- Sync drift above threshold

