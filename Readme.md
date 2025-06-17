Java Codebase Analyzer with LLM Integration   **

Overview

The Java Codebase Analyzer is a sophisticated tool that leverages Large Language Models (LLMs) to analyze Java codebases, extract structured information, and generate comprehensive documentation. The system clones repositories, processes Java files, and uses Cohere's LLM to extract key architectural information about classes, methods, and project structure.


Architecture Overview

<img width="602" alt="Screenshot 2025-06-18 at 2 00 56 AM" src="https://github.com/user-attachments/assets/9ba6f0f2-d31e-4891-91f8-58ade93b0228" />




Key Components:

    GitManager: Handles repository cloning

    DataLoader: Manages file discovery and reading

    CodeProcessor: Splits Java files into class-level chunks

    AsyncLLMAnalyzer: Integrates with Cohere LLM for code analysis

    OutputWriter: Generates timestamped JSON output files

    RagasEvaluator: (Optional) Evaluates analysis quality against gold standards

Documentation
Approach & Methodologies

    Modular Architecture: The system follows a clean separation of concerns with dedicated modules for each functionality

    Asynchronous Processing: Uses Python's asyncio for efficient concurrent processing of code files

    LLM-Powered Analysis: Leverages Cohere's Command-R+ model for intelligent code understanding

    Structured Output: Uses Pydantic models to ensure consistent JSON output

    Chunk Processing: Splits large Java files into manageable chunks for LLM processing

Best Practices

    Error Handling: Comprehensive exception handling with contextual logging

    Resource Management: Configurable concurrency limits to prevent API overload

    Truncation Handling: Automatically truncates large code segments to fit LLM context windows

    Retry Mechanism: Implements retry logic for LLM API calls

    Timestamped Outputs: Generates unique output files to prevent overwriting

    Normalization: Standardizes names for consistent matching during evaluation

Assumptions

    Target repositories are Java-based projects

    README.md or similar files exist for project overview extraction

    Java files follow standard class declaration conventions

    LLM API (Cohere) is available and properly configured

    Sufficient system resources for concurrent processing

Limitations

    Large Codebases: Processing time increases significantly with large projects

    Complex Classes: Nested classes or unconventional structures may not parse correctly

    LLM Context Limits: Code chunks beyond 3000 characters are truncated

    Annotation Handling: Complex annotations might not be fully captured

   This is currently Half baked sort of -** Evaluation Dependency: RAGAS evaluation requires a gold standard for comparison

  

Getting Started
Prerequisites

    Python 3.9+

    Cohere API key

    Git

Installation
bash

git clone https://github.com/your-repo/java-codebase-analyzer.git
cd java-codebase-analyzer
pip install -r requirements.txt
export COHERE_API_KEY=your_api_key_here

Configuration

Edit config.py to customize:
python

@dataclass
class AppConfig:
    codebase_repo: str = "https://github.com/your-target-repo"
    output_json: str = "outputs/analysis.json"
    project_name: str = "YourProject"
    max_concurrent: int = 5
    log_level: str = "INFO"

Usage
bash

python main.py

Output

Analysis results are saved in outputs/ directory with timestamped JSON files containing:

    Project overview

    Class-level analysis

    Method signatures and descriptions

    Dependencies

    Complexity assessments

Evaluation(HALF BAKED)

To enable quality evaluation:

    Set eval_config.enable_evaluation = True in config.py

    Place gold standard analysis in gold_standard/gold_javacode_analysis.json

    Run analysis to automatically trigger RAGAS evaluation

Dependencies

    Cohere (LLM integration)

    LangChain (prompt engineering)

    GitPython (repository handling)

    Ragas (evaluation framework)(HALF BAKED)

    Pydantic (data modeling)

    Asyncio (concurrent processing)

Logging

Detailed logs are available in logs/analysis.log with different verbosity levels controlled by log_level configuration.

    

License  @author Anant Waghmare

