import os
from dotenv import load_dotenv

load_dotenv()

class GeminiConfig:
    """
    Google Gemini API configuration
    """
    
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY not found in environment variables. "
                "Please set it in your .env file."
            )
    
    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)