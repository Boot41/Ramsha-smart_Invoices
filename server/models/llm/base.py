from dotenv import load_dotenv
from pathlib import Path
from langchain.chat_models import init_chat_model
from utils.config import REGIONS
import random
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_model():
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    random_region = REGIONS[random.randint(0, len(REGIONS) - 1)]
    model = init_chat_model(
        "gemini-2.0-flash", 
        model_provider="google_genai",
        region=random_region
    )
    return model

