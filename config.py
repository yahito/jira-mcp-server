import os
from dataclasses import dataclass
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

@dataclass
class JiraConfig:
    base_url: str = os.getenv("JIRA_BASE_URL", "https://yaporyadin.atlassian.net")
    username: str = os.getenv("JIRA_USERNAME", "")
    api_token: str = os.getenv("JIRA_API_TOKEN", "")
    timeout: timedelta = timedelta(seconds=30)
    
    @property
    def timeout_seconds(self) -> float:
        return self.timeout.total_seconds()

# Create a single instance to import elsewhere
jira_config = JiraConfig()
