
import sys
import json
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip # type: ignore

from openai import OpenAI
from typing import List, Tuple
from pathlib import Path

MOCK = True  # Set to False for real OpenAI caption generation
OPENAI_MODEL = "gpt-4o-mini"

# === INITIALIZATION ===
client = OpenAI() if not MOCK else None


# === FUNCTIONS ===

#loads entire transcript
def load_transcript(path: str) -> List[dict]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, dict) or "segments" not in data:
            raise ValueError("Transcript must be a dict with a 'segments' list.")
        return data["segments"]

#loads viral section of clip
def load_selection(path: str) -> Tuple[float, float, str]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["start"], data["end"], data["text"]

def generate_viral_caption(text: str) -> str:
    if MOCK:
        return "He wasn’t ready..."
    
    #use chat gpt to generate a accurate caption for video
    prompt = f"""You're a short-form video editor. Generate a viral caption (5–10 words max) based on this transcript:
    
    Transcript:
    "{text}"

    Caption:"""
    
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=1.0,
    )
    return response.choices[0].message.content.strip('" \n')


#taking subtitles from video
def extract_subtitles(transcript: List[dict], start: float, end: float) -> List[Tuple[float, float, str]]:
    subs = []
    for segment in transcript:
        t0, t1 = float(segment["start"]), float(segment["end"])
        if t1 < start or t0 > end:
            continue
        # Clamp to range
        t0 = max(t0, start)
        t1 = min(t1, end)
        subs.append((t0 - start, t1 - start, segment["text"]))
    return subs

#displaying viral caption
def render_caption(text: str, size: Tuple[int, int], duration: float):
    return (
        TextClip(
            txt=text,
            fontsize=64,
            color="white",
            font="Arial-Bold",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(size[0] - 100, None),
        )
        .set_duration(duration)
        .set_position(("center", "top"))
    )

#rendering subtitles at correct time using srt file
def render_subtitles(subs: List[Tuple[float, float, str]], size: Tuple[int, int]) -> List[TextClip]:
    clips = []
    for start, end, line in subs:
        txt = TextClip(
            txt=line,
            fontsize=48,
            color="white",
            font="Arial-Bold",
            stroke_color="black",
            stroke_width=2,
            method="caption",
            size=(size[0] - 100, None),
        ).set_start(start).set_end(end).set_position(("center", "bottom"))
        clips.append(txt)
    return clips

#putting all of it together to format the final clip 
def render_clip():

    if len(sys.argv) < 2:
        print("Usage: python render_clip.py data/raw/<video_folder>")
        sys.exit(1)

    base_dir = Path(sys.argv[1])
    video_id = base_dir.name
    print(f"🎬 Rendering video: {video_id}")

    # Load data
    source_path = base_dir / "source.mp4"
    transcript_path = base_dir / "transcript.json"
    selection_path = base_dir / "clip_selection.json"
    output_path = base_dir / "final_clip.mp4"

    transcript = load_transcript(str(transcript_path))
    start, end, text = load_selection(str(selection_path))
    duration = end - start
    print(f"⏱ Clip range: {start:.2f}s to {end:.2f}s")

    video = VideoFileClip(str(source_path)).subclip(start, end)
    viral_caption = generate_viral_caption(text)
    print(f"📢 Caption: {viral_caption}")

    subs = extract_subtitles(transcript, start, end)

    overlay_caption = render_caption(viral_caption, video.size, duration)
    subtitle_clips = render_subtitles(subs, video.size)

    final = CompositeVideoClip([video, overlay_caption] + subtitle_clips)
    final.write_videofile(str(output_path), fps=30, codec="libx264", audio_codec="aac")
    print(f"✅ Done: {str(output_path)}")

# === RUN ===
if __name__ == "__main__":
    render_clip()