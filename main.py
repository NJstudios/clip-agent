import os
import subprocess
from dotenv import load_dotenv
from pathlib import Path
from ingestion.youtube_discoverer import discover_viral_candidates
from ingestion.youtube_scraper import download_youtube_video
from ingestion.transcriber import transcribe_video, save_transcript
from reasoning.clip_selector import load_transcript, segment_transcript, select_best_clip

load_dotenv()

ENABLE_REAL_API_CALLS = os.getenv("ENABLE_REAL_API_CALLS", "false").lower() == "true"
TRANSCRIBE_MODEL = os.getenv("WHISPER_MODEL", "base")

MAX_VIDEOS = 3  # How many candidate videos to download and process per run

def run_pipeline():
    print("\n Discovering viral candidates...")
    candidates = discover_viral_candidates()

    for i, video in enumerate(candidates[:MAX_VIDEOS]):
        print(f"\n[{i+1}] ▶️ Processing video: {video['title']}")
        try:
            #downloading the candidate and then saving the output directory
            result = download_youtube_video(video['url'], "data/raw")
            video_path = Path(result["video_path"])
            output_dir = video_path.parent

            #getting the transcript
            transcript = transcribe_video(str(video_path), model_size=TRANSCRIBE_MODEL)
            #saving the transcript into a file
            save_transcript(transcript, output_dir)

            #finding the best 30s clip 
            transcript_json = load_transcript(output_dir / "transcript.json")
            chunks = segment_transcript(transcript_json)
            best = select_best_clip(chunks)

            #saving best clip as a json file
            out_path = output_dir / "clip_selection.json"
            with open (out_path, "w", encoding="utf-8") as f:
                import json 
                json.dump(best, f, indent=2)

            
            print(f"✅ Selected clip: {best['start']} → {best['end']}")
            print(f"📄 Saved: {out_path}")

        except Exception as e:
            print(f"❌ Failed on video {video['url']}: {e}")

if __name__ == "__main__":
    run_pipeline()