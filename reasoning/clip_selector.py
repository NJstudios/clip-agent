import json
import os
import openai
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

SEGMENT_LENGTH = 15 # seconds, change for real clips