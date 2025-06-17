
import asyncio
import os
from datetime import datetime
from pathlib import Path


from config.config import app_config, llm_config  # Top-level config
from utils.logger import Logger
from utils.exception_handler import ExceptionHandler
from utils.git_tool import GitManager
from src.data_loader import DataLoader
from src.code_processor import CodeProcessor
from src.llm_integration import AsyncLLMAnalyzer
from src.output_generator import OutputWriter

class CodebaseAnalyzer:
    def __init__(self):
        # Initialize dependencies
        self.logger = Logger(app_config.log_level, app_config.log_file)
        self.exception_handler = ExceptionHandler(self.logger)
        self.git_manager = GitManager(self.logger, self.exception_handler)
        self.data_loader = DataLoader(self.logger, self.exception_handler)
        self.code_processor = CodeProcessor(self.logger, self.exception_handler)
        self.llm_analyzer = AsyncLLMAnalyzer(self.logger, self.exception_handler)
        self.output_writer = OutputWriter(self.logger, self.exception_handler)
    
    async def run_analysis(self):
        self.logger.info("Starting SakilaProject analysis")
        
        # Create required directories
        Path("cloned_repo").mkdir(exist_ok=True)
        Path(app_config.output_json).parent.mkdir(parents=True, exist_ok=True)
        Path(app_config.log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # Clone repository
        repo_dir = await self.git_manager.clone_repository(
            app_config.codebase_repo, 
            "cloned_repo"
        )
        
        # Find and process overview file
        overview_file = self.data_loader.find_project_overview_file(repo_dir)
        overview_text = ""
        if overview_file:
            self.logger.info(f"Using overview file: {overview_file}")
            overview_text = self.data_loader.read_file(overview_file)
        else:
            self.logger.warning("No overview file found")
        
        # Analyze project overview
        project_overview = await self.llm_analyzer.analyze_project_overview(
            overview_text, app_config.project_name
        )
        self.logger.info("Project overview analysis complete")
        
        # Find Java files
        java_files = self.data_loader.list_code_files(repo_dir, [".java"])
        self.logger.info(f"Found {len(java_files)} Java files for analysis")
        
        # Process files concurrently with semaphore
        semaphore = asyncio.Semaphore(app_config.max_concurrent)
        components = []
        
        async def process_file(file_path):
            async with semaphore:
                self.logger.debug(f"Processing file: {file_path}")
                try:
                    code = self.data_loader.read_file(file_path)
                    if not code.strip():
                        self.logger.warning(f"Skipping empty file: {file_path}")
                        return
                    
                    class_chunks = self.code_processor.split_into_classes(code)
                    if not class_chunks:
                        self.logger.warning(f"No classes found in file: {file_path}")
                        return
                    
                    self.logger.debug(f"Processing {len(class_chunks)} classes in {file_path}")
                    
                    # Batch process all classes in this file
                    analyses = await self.llm_analyzer.analyze_classes_batch(class_chunks)
                    for analysis in analyses:
                        analysis["source_file"] = str(file_path)
                        components.append(analysis)
                except Exception as ex:
                    await self.exception_handler.handle(ex, f"process_file: {file_path}")
        
        # Execute all file processing tasks
        tasks = [process_file(file) for file in java_files]
        await asyncio.gather(*tasks)
        
        self.logger.info(f"Analyzed {len(components)} classes")
        
        # Prepare final output structure
        output = {
            "project": app_config.project_name,
            "analysis_date": datetime.now().isoformat(),
            "project_overview": project_overview.dict(),
            "components": components
        }
        
        # Write output
        await self.output_writer.write_output(output)
        self.logger.info("Analysis complete. Output saved")
        if eval_config.enable_evaluation:
            self.logger.info("Triggering RAGAS evaluation")
            try:
                # Fire-and-forget approach
                subprocess.Popen([
                    sys.executable, 
                    "evaluation_main.py"
                ])
                self.logger.info("Evaluation process started in background")
            except Exception as ex:
                self.logger.error(f"Failed to start evaluation: {str(ex)}")

async def main():
    analyzer = CodebaseAnalyzer()
    await analyzer.run_analysis()

if __name__ == "__main__":
    asyncio.run(main())
