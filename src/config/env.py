from dotenv import load_dotenv
from pathlib import Path
import os

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path = ENV_PATH)

def get_env(key = str, default = None):
    return os.getenv(key, default)