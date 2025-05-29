import json
import os
import random
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

USE_REAL_API = os.getenv("ENABLE_REAL_API_CALLS", "false").lower() == "true"
if USE_REAL_API:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))



SEGMENT_LENGTH = 30 # seconds, change for real clips

def load_transcript(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    
def segment_transcript(transcript, window=SEGMENT_LENGTH):
    segments = transcript["segments"]
    chunks = []
    current = []
    start_time = None
    for seg in segments:
        if start_time is None: 
            start_time = seg["start"]

        current.append(seg)
        duration = seg["end"] - start_time
        if duration >= window:
            text = " ".join(s["text"].strip() for s in current)
            chunks.append({
                "start": start_time,
                "end": seg["end"],
                "text": text
            })
            current = []
            start_time = None

    return chunks 

def score_segment(segment_text): 
    if not USE_REAL_API:
        # ✅ Mock mode (safe during development)
        return {
            "score": random.randint(6, 10),
            "reason": "Simulated score for testing"
        }

    # 🔁 Real OpenAI call
    prompt = f"""
You are an expert in short-form video virality. Given the following transcript segment, rate how likely it is to go viral on a scale of 1–10. Look for humor, emotion, drama, or compelling delivery. Then briefly explain why.

Transcript:
\"\"\"{segment_text}\"\"\"

Respond as JSON: {{ "score": <1–10>, "reason": "<why>" }}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # or "gpt-3.5-turbo"
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    content = response.choices[0].message.content
    try:
        return json.loads(content)
    except Exception:
        return {"score": 0, "reason": "parse failed"}
    
def select_best_clip(chunks):
    results=[]
    for chunk in chunks:
        print(f"Scoring clip: {chunk['start']}–{chunk['end']}...")
        result = score_segment(chunk["text"])
        chunk.update(result)
        results.append(chunk)

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[0]

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python reasoning/clip_selector.py <transcript.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    transcript = load_transcript(path)
    chunks = segment_transcript(transcript)
    best = select_best_clip(chunks)

    out_path = path.parent / "clip_selection.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(best, f, indent=2)

    print(f"\n✅ Best clip: {best['start']} → {best['end']}")
    print(f"📄 Saved: {out_path}")