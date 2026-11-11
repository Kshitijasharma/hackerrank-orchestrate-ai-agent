from dotenv import load_dotenv
load_dotenv()

from processor import run_pipeline

if __name__ == "__main__":
    print("DEBUG: Starting main.py...")
    run_pipeline()
