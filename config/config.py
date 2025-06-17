from dataclasses import dataclass
import os

@dataclass
class LLMConfig:
    model_name: str = "command-r-plus"
    api_key: str = os.getenv("COHERE_API_KEY", "NDaUjGaeH6oNqLVSc6rAmpvEHl9glQjLhK751jWY")
    temperature: float = 0.7
    max_tokens: int = 2048
    max_retries: int = 3
    timeout: int = 60
   
    

@dataclass
class AppConfig:
    codebase_repo: str = "https://github.com/janjakovacevic/SakilaProject"
    output_json: str = "outputs/javacode_analysis.json"
    project_name: str = "SakilaProject"
    chunk_size: int = 3000
    chunk_overlap: int = 200
    max_concurrent: int = 5  # Increased concurrency limit
    log_level: str = "DEBUG"
    log_file: str = "logs/analysis.log"
    timestamp_format: str = "%Y%m%d_%H%M%S" 

# Initialize configuration
llm_config = LLMConfig()
app_config = AppConfig()