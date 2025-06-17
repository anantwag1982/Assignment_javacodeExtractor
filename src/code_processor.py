import re

class CodeProcessor:
    def __init__(self, logger, exception_handler):
        self.logger = logger
        self.exception_handler = exception_handler

    def split_into_classes(self, code: str) -> list:
        """Split Java code into class-level chunks with better parsing"""
        # Remove block comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        # Remove line comments
        code = re.sub(r'//.*', '', code)
        
        # Pattern to detect class/interface/enum/record declarations
        class_pattern = re.compile(
            r'^\s*(public\s+|protected\s+|private\s+|abstract\s+|final\s+|static\s+)*'
            r'(class|interface|enum|record)\s+(\w+)'
        )
        
        chunks = []
        current_chunk = []
        brace_count = 0
        in_class = False
        
        for line in code.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
                
            # Check for class declaration
            class_match = class_pattern.match(stripped)
            if class_match and not in_class:
                if current_chunk:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                current_chunk.append(line)
                in_class = True
                brace_count = 0
                self.logger.debug(f"Found class: {class_match.group(3)}")
            elif in_class:
                current_chunk.append(line)
            
            # Track braces
            if in_class:
                brace_count += line.count('{')
                brace_count -= line.count('}')
                
                # End of class when braces balance
                if brace_count <= 0:
                    chunks.append('\n'.join(current_chunk))
                    current_chunk = []
                    in_class = False
                    brace_count = 0
        
        # Add any remaining content
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
        
        return chunks