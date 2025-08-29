from google.cloud import aiplatform as vertexai
from vertexai.preview.generative_models import GenerativeModel
from dotenv import load_dotenv
from pathlib import Path
from utils.config import REGIONS
import random
import os

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_model():
    vertexai.init(project=os.getenv("PROJECT_ID"), location=REGIONS[random.randint(0, 25)])  
    model = GenerativeModel("gemini-2.0-flash") 
    return model

