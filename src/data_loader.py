from pathlib import Path
from typing import List, Optional
from utils.logger import Logger
from utils.exception_handler import ExceptionHandler
from dataclasses import dataclass

class DataLoader:
    def __init__(self, logger, exception_handler):
        self.logger = logger
        self.exception_handler = exception_handler

    def list_code_files(self, base_dir: str, extensions: List[str]) -> List[Path]:
        files = []
        try:
            base_path = Path(base_dir)
            for ext in extensions:
                files.extend(list(base_path.rglob(f"*{ext}")))
            self.logger.info(f"Found {len(files)} code files")
        except Exception as ex:
            self.exception_handler.handle(ex, "list_code_files")
        return files

    def read_file(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as ex:
            self.exception_handler.handle(ex, f"read_file: {file_path}")
            return ""

    def find_project_overview_file(self, base_dir: str) -> Optional[Path]:
        candidates = [
            "README.md", "readme.md", "README.txt", "readme.txt",
            "OVERVIEW.md", "DESCRIPTION.md", "ABOUT.md"
        ]
        
        try:
            base_path = Path(base_dir)
            for fname in candidates:
                candidate = base_path / fname
                if candidate.exists():
                    return candidate
                    
            # Fallback to any markdown file with "readme" in name
            for f in base_path.rglob("*readme*.*"):
                if f.suffix.lower() in ['.md', '.txt']:
                    return f
                    
            # Final fallback: main class in source root
            src_dir = base_path / "src"
            if src_dir.exists():
                for f in src_dir.rglob("*.java"):
                    if "main" in f.name.lower():
                        return f
        except Exception as ex:
            self.exception_handler.handle(ex, "find_project_overview_file")
        return None