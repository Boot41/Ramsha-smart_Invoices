from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import time
from threading import Lock
from datetime import datetime

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class SimpleRateLimiter:
    """Simple rate limiter with configurable delay between requests"""
    
    def __init__(self, requests_per_minute=60):
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute  # Seconds between requests
        self.last_request_time = 0
        self.lock = Lock()
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limit"""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.min_delay:
                wait_time = self.min_delay - time_since_last
                print(f"⏳ Rate limiting: waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()

# Global rate limiter
_simple_limiter = SimpleRateLimiter(requests_per_minute=50)  # Conservative limit

def get_model_simple():
    """Get Gemini model with simple rate limiting"""
    if not os.environ.get("GOOGLE_API_KEY"):
        raise ValueError("GOOGLE_API_KEY environment variable is required")
    
    # Apply rate limiting
    _simple_limiter.wait_if_needed()
    
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=os.environ.get("GOOGLE_API_KEY"),
        temperature=0.1,
        max_output_tokens=4000
    )
    
    return model