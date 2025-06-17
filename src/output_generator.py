import json
import os
from pathlib import Path
from datetime import datetime
from config.config import app_config  # UPDATE THIS IMPORT

class OutputWriter:
    def __init__(self, logger, exception_handler):
        self.logger = logger
        self.exception_handler = exception_handler
    
    async def write_output(self, data: dict):
        try:
            # Generate timestamped filename
            timestamp = datetime.now().strftime(app_config.timestamp_format)
            original_path = Path(app_config.output_json)
            
            # Create timestamped filename
            timestamped_path = original_path.with_name(
                f"{original_path.stem}_{timestamp}{original_path.suffix}"
            )
            
            # Create directories if needed
            timestamped_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write to file
            with timestamped_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            
            self.logger.info(f"Output written to {timestamped_path}")
            return True
        except Exception as ex:
            await self.exception_handler.handle(ex, "write_output")
            return False