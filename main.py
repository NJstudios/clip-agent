from dotenv import load_dotenv
import os

load_dotenv()

def main():
    print("Env loaded:", os.getenv("OPENAI_API_KEY"))

if __name__ == "__main__":
    main()
