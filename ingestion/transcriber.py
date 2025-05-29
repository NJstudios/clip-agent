import sys
import os
import json
from pathlib import Path
import whisper

def transcribe_video(video_path: str, model_size="base") -> dict:
    """Transcribes video using Open AI Whispher and returns it in a table"""
    model = whisper.load_model(model_size)

    print(f"[Transcriber] Loading Video: {video_path}")
    result = model.transcribe(video_path, verbose=True)

    return result 

def save_transcript(result:dict, output_dir: Path):
    """Saves transcript to both JSON and SRT."""
    output_dir.mkdir(parents=True, exist_ok=True)

    #save transcript in JSON
    json_path = output_dir / "transcript.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)

    print(f"[Transcriber] Saved JSON transcript: {json_path}")

    # Convert to SRT
    srt_path = output_dir / "transcript.srt"
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, segment in enumerate(result["segments"], 1):
            start = format_timestamp(segment["start"])
            end = format_timestamp(segment["end"])
            text = segment["text"].strip()

            f.write(f"{i}\n{start} --> {end}\n{text}\n\n")

    print(f"[Transcriber] Saved SRT: {srt_path}")

def format_timestamp(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python ingestion/transcriber.py <video_path> [model_size]")
        sys.exit(1)

    video_path = Path(sys.argv[1])
    if not video_path.exists():
        print(f"[ERROR] File does not exist: {video_path}")
        sys.exit(1)

    model_size = sys.argv[2] if len(sys.argv) > 2 else "base"

    result = transcribe_video(str(video_path), model_size)

    output_dir = video_path.parent
    save_transcript(result, output_dir)