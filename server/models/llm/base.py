from dotenv import load_dotenv
from pathlib import Path
from vertexai.generative_models import GenerativeModel

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

def get_model(model_name: str = "gemini-2.5-pro", temperature: float = 0.1, max_output_tokens: int = 4000):
    """Get Gemini model."""
    return GenerativeModel(
        model_name,
        generation_config={
            "max_output_tokens": max_output_tokens,
            "temperature": temperature,
        }
    )