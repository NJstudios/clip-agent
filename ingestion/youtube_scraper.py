import os
import json
from yt_dlp import YoutubeDL
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def extract_video_id(url:str) -> str:
    """take youtube video id from url"""
    query = urlparse(url).query
    params = parse_qs(query)
    return params.get("v", [None])[0] or url.split("/")[-1]

def download_youtube_video(url: str, output_dir: Path) -> dict:
    video_id = extract_video_id(url)
    if not video_id:
        raise ValueError("Invalid Video Url")
    
    target_dir = Path(output_dir) / video_id
    target_dir.mkdir(parents=True, exist_ok=True)

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4",
        "outtmpl": str(target_dir / "source.%(ext)s"),
        "merge_output_format": "mp4",
        "quiet": False,
        "no_warnings": True,
        "writeinfojson": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)

    # meta data
    metadata = {
        "id": info.get("id"),
        "title": info.get("title"),
        "description": info.get("description"),
        "duration": info.get("duration"),
        "upload_date": info.get("upload_date"),
        "uploader": info.get("uploader"),
        "webpage_url": info.get("webpage_url"),
    }

    with open(target_dir / "metadata.json", "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return {
        "video_path": str(target_dir / "source.mp4"),
        "metadata_path": str(target_dir / "metadata.json"),
        "video_id": video_id,
        "metadata": metadata,
    }

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ingestion/youtube_scraper.py <YouTube URL>")
        sys.exit(1)

    result = download_youtube_video(sys.argv[1], "data/raw")
    print(f"\n✅ Downloaded: {result['video_path']}")
    print(f"📝 Metadata: {result['metadata_path']}")