import os
from dotenv import load_dotenv
from googleapiclient.discovery import build

# Load API key
load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Keywords that suggest virality
#use open ai to find the most popular key words at a given time **
VIRAL_KEYWORDS = [
    "funniest", "insane", "rage", "rant", "roast", "explosive",
    "fails", "awkward", "called out", "drama", "craziest"
]

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
        print(f"\n Searching: {keyword}")
        results = search_youtube(keyword)
        #searching for 5 videos related to keyword we specify and then looping through them
        for item in results:
            #getting all video data to sort through to rank
            vid = item["id"]["videoId"]
            meta = fetch_video_metadata(vid)
            stats = meta["statistics"]
            title = meta["snippet"]["title"]

            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 1))  # avoid div-by-zero
            ratio = likes / max(1, views)

            print(f"\n VIDEO: {title} has a ratio of: {ratio}")
            # Simple filters
            if views > 10000 and ratio > 0.01:
                candidates.append({
                    "video_id": vid,
                    "title": title,
                    "views": views,
                    "like_ratio": ratio,
                    "url": f"https://www.youtube.com/watch?v={vid}"
                })
    #this will be full of videos that are "popular"
    return candidates

if __name__ == "__main__":
    discovered = discover_viral_candidates()
    print("\n✅ Discovered Candidates:")
    for vid in discovered:
        print(f"- {vid['title']} ({vid['views']} views) → {vid['url']}")
