from dataclasses import dataclass
import os

@dataclass
class LLMConfig:
    model_name: str = "command-r-plus"
    api_key: str = os.getenv("COHERE_API_KEY", "QPc13bRgD2BzrsnnLR0Z7TRYUXHEN9EDK5dGA7dE")
    temperature: float = 0.7
    max_tokens: int = 2048
    max_retries: int = 3
    timeout: int = 60
@dataclass
class EvalConfig:
    enable_evaluation: bool = False
    predictions_path: str = "outputs/javacode_analysis.json"
    gold_path: str = "gold_standard/gold_javacode_analysis.json"
   # evaluation_output_path: str = "evaluation_results/evaluation_report.txt"
  
    evaluation_output_path = "output/evaluation_result.csv"
    metrics = ["answer_correctness", "context_precision", "context_recall", "faithfulness"]

    
    def __post_init__(self):
        # Define default metrics if not provided
        if self.metrics is None:
            self.metrics = ["answer_correctness", "precision", "recall", "f1"]
    

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
eval_config = EvalConfig()