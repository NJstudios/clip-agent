import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
import datetime

# Load API key
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Keywords that suggest virality
#use open ai to find the most popular key words at a given time **
VIRAL_KEYWORDS = [
    "funniest", "crazy moments", "podcast clips", "angry reaction", "public freakout",
    "interview gone wrong", "thrilling stunt", "argument", "celebrity meltdown"
]

UNWANTED_KEYWORDS = [
    "music", "official video", "lyric", "album", "feat", "ft.", "remix",
    "instrumental", "cover", "song", "dj", "mv"
]

DESIRABLE_KEYWORDS = [
    "podcast", "interview", "debate", "reaction", "meltdown",
    "freakout", "fails", "argument", "stunt", "rant", "roast"
]

def keyword_score(title: str) -> int:
    lowered = title.lower()
    bad_hits = any(bad in lowered for bad in UNWANTED_KEYWORDS)
    good_hits = sum(good in lowered for good in DESIRABLE_KEYWORDS)
    return -1 if bad_hits else good_hits


def search_youtube(keyword, max_results=5):
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=YOUTUBE_API_KEY
    )

    #using youtube api to search for videos
    request = youtube.search().list(
        q=keyword,
        part="snippet",
        type="video",
        videoDuration="medium",
        order="relevance",
        maxResults=max_results
    )
    response = request.execute()
    return response.get("items", [])

def fetch_video_metadata(video_id):
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=YOUTUBE_API_KEY
    )

    #getting metadata of video using video id
    request = youtube.videos().list(
        part="snippet,statistics,contentDetails",
        id=video_id
    )

    response = request.execute()
    return response.get("items", [])[0]

def discover_viral_candidates():
    candidates = []
    for keyword in VIRAL_KEYWORDS:
        print(f"\n🔍 Searching: {keyword}")
        results = search_youtube(keyword)

        for item in results:
            vid = item["id"]["videoId"]
            meta = fetch_video_metadata(vid)
            stats = meta["statistics"]
            snippet = meta["snippet"]

            title = snippet["title"]
            channel = snippet["channelTitle"].lower()
            published = snippet.get("publishedAt", "")

            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 1))
            ratio = likes / max(1, views)
            desirability = keyword_score(title)

            if desirability == -1:
                print(f"🚫 Skipping music/irrelevant: {title}")
                continue

            try:
                published_date = datetime.datetime.fromisoformat(published.replace("Z", "+00:00"))
                days_old = (datetime.datetime.utcnow() - published_date).days
            except Exception:
                days_old = 999  # fallback if date is malformed

            score = (
                (views / 1_000) +
                (ratio * 100) +
                (desirability * 5) -
                (0.1 * days_old)
            )

            if score < 20:
                continue

            print(f"✅ Candidate: {title} | Score: {score:.2f}")

            candidates.append({
                "video_id": vid,
                "title": title,
                "channel": channel,
                "views": views,
                "like_ratio": ratio,
                "desirability": desirability,
                "published_days_ago": days_old,
                "score": score,
                "url": f"https://www.youtube.com/watch?v={vid}"
            })

    candidates.sort(key=lambda c: c["score"], reverse=True)
    return candidates

if __name__ == "__main__":
    discovered = discover_viral_candidates()
    print("\n✅ Discovered Candidates:")
    for vid in discovered:
        print(f"- {vid['title']} ({vid['views']} views) → {vid['url']}")
