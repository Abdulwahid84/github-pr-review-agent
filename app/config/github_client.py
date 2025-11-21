import os
from dotenv import load_dotenv

load_dotenv()

class GitHubConfig:
    """
    GitHub API configuration
    """
    
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        
        if not self.token:
            raise ValueError(
                "GITHUB_TOKEN not found in environment variables. "
                "Please set it in your .env file."
            )
    
    @property
    def is_configured(self) -> bool:
        return bool(self.token)