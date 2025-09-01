from dotenv import load_dotenv
from pathlib import Path
from langchain_google_genai import ChatGoogleGenerativeAI
import os
import time
from threading import Lock
from collections import defaultdict, deque
from datetime import datetime, timedelta

env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class GeminiRateLimiter:
    """Rate limiter for Google Gemini API with multiple API keys"""
    
    def __init__(self):
        self.api_keys = self._get_api_keys()
        self.request_counts = defaultdict(deque)  # Track requests per API key
        self.lock = Lock()
        self.rpm_limit = 60  # Requests per minute per API key
        
    def _get_api_keys(self):
        """Get all available Google API keys from environment"""
        keys = []
        
        # Primary key
        primary_key = os.environ.get("GOOGLE_API_KEY")
        if primary_key:
            keys.append(primary_key)
            
        # Additional keys (GOOGLE_API_KEY_2, GOOGLE_API_KEY_3, etc.)
        i = 2
        while True:
            additional_key = os.environ.get(f"GOOGLE_API_KEY_{i}")
            if additional_key:
                keys.append(additional_key)
                i += 1
            else:
                break
                
        if not keys:
            raise ValueError("At least one GOOGLE_API_KEY environment variable is required")
            
        print(f"✅ Loaded {len(keys)} Google API keys for rate limiting")
        return keys
    
    def get_available_key(self):
        """Get an API key that hasn't exceeded RPM limit"""
        with self.lock:
            current_time = datetime.now()
            one_minute_ago = current_time - timedelta(minutes=1)
            
            # Clean old requests and find available key
            for api_key in self.api_keys:
                # Remove requests older than 1 minute
                while (self.request_counts[api_key] and 
                       self.request_counts[api_key][0] < one_minute_ago):
                    self.request_counts[api_key].popleft()
                
                # Check if this key is under the rate limit
                if len(self.request_counts[api_key]) < self.rpm_limit:
                    # Record this request
                    self.request_counts[api_key].append(current_time)
                    return api_key
            
            # If all keys are at limit, wait and retry with least used key
            least_used_key = min(self.api_keys, 
                                key=lambda k: len(self.request_counts[k]))
            
            # Wait until we can use the least used key
            if self.request_counts[least_used_key]:
                wait_time = 61 - (current_time - self.request_counts[least_used_key][0]).seconds
                if wait_time > 0:
                    print(f"⏳ Rate limit reached, waiting {wait_time} seconds...")
                    time.sleep(wait_time)
            
            # Record the request and return the key
            self.request_counts[least_used_key].append(datetime.now())
            return least_used_key

# Global rate limiter instance
_rate_limiter = None

def get_rate_limiter():
    """Get singleton rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = GeminiRateLimiter()
    return _rate_limiter

def get_model():
    """Get Gemini model with rate limiting and API key rotation"""
    rate_limiter = get_rate_limiter()
    api_key = rate_limiter.get_available_key()
    
    # Use ChatGoogleGenerativeAI directly for better control
    model = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=api_key,
        temperature=0.1,
        max_output_tokens=4000
    )
    
    return model

