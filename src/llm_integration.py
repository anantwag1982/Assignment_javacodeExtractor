import asyncio
import re
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_cohere import ChatCohere
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import List
from config.config import app_config, llm_config  # Top-level config

# Define structured output models
class MethodInfo(BaseModel):
    name: str = Field(description="Method name")
    signature: str = Field(description="Full method signature with annotations and parameters")
    description: str = Field(description="Method purpose and functionality")

class JavaClassAnalysis(BaseModel):
    class_name: str = Field(description="Class name")
    overview: str = Field(description="Class purpose overview")
    methods: list[MethodInfo] = Field(description="List of methods")
    dependencies: list[str] = Field(description="Class dependencies")
    complexity: str = Field(description="Complexity level: low, medium, high")

class ProjectOverview(BaseModel):
    project_name: str = Field(description="Project name")
    purpose: str = Field(description="Project purpose")
    core_functionality: str = Field(description="Core functionality")
    key_technologies: list[str] = Field(description="Key technologies")
    architecture: str = Field(description="System architecture")
    business_domain: str = Field(description="Business domain")

class AsyncLLMAnalyzer:
    def __init__(self, logger, exception_handler):
        self.logger = logger
        self.exception_handler = exception_handler
        self.llm = ChatCohere(
            model=llm_config.model_name,
            cohere_api_key=llm_config.api_key,
            temperature=llm_config.temperature,
            max_tokens=llm_config.max_tokens
        )
        
        # Create prompt templates
        self.class_prompt = ChatPromptTemplate.from_template(
            "You are a software architect. Analyze the following Java class and return a JSON object with the following keys:\n"
    "- class_name: The name of the class\n"
    "- overview: A brief summary of the class's purpose\n"
    "- methods: List of objects with:\n"
    "    - name: Method name\n"
    "    - signature: Full method signature with annotations\n"
    "    - description: What the method does\n"
    "- dependencies: List of external classes/imports used\n"
    "- complexity: Complexity level (low, medium, high)\n\n"
    "Return ONLY valid JSON. No explanation or markdown.\n\n"
    "Output format:\n"
    "{{{{\n"
    '  "class_name": "ExampleClass",\n'
    '  "overview": "Handles business logic for orders",\n'
    '  "methods": [\n'
    "    {{{{\n"
    '      "name": "calculateTotal",\n'
    '      "signature": "public double calculateTotal(List<Item> items)",\n'
    '      "description": "Calculates the total price for the given items."\n'
    "    }}}}\n"
    "  ],\n"
    '  "dependencies": ["java.util.List", "com.myapp.Item"],\n'
    '  "complexity": "medium"\n'
    "}}}}\n\n"
    "Use empty strings (\"\") for missing values. Maintain exact JSON key names.\n\n"
    "Code:\n{code}"
)
        
        self.overview_prompt = ChatPromptTemplate.from_template(
    "Generate a comprehensive project overview from the documentation:\n"
    "1. Project purpose and core functionality\n"
    "2. Main technologies used\n"
    "3. Key architectural components\n"
    "4. Business domain context\n\n"
    "Return ONLY pure JSON with no additional text/explanations.\n\n"
    "Output format:\n"
    "{{\n"
    '  "project_name": "SakilaProject",\n'
    '  "purpose": "string",\n'
    '  "core_functionality": "string",\n'
    '  "key_technologies": ["string"],\n'
    '  "architecture": "string",\n'
    '  "business_domain": "string"\n'
    "}}\n\n"
    "Rules:\n"
    "- Use empty string ("") for unknown or missing values\n"
    "- Never add markdown formatting\n"
    "- Maintain exact key names and structure\n\n"
    "Documentation:\n{overview_text}"
)

        
        # Create chains
        self.class_chain = self.class_prompt | self.llm | JsonOutputParser(pydantic_object=JavaClassAnalysis)
        self.overview_chain = self.overview_prompt | self.llm | JsonOutputParser(pydantic_object=ProjectOverview)

    async def analyze_classes_batch(self, code_chunks: List[str]) -> List[dict]:
        """Process multiple class chunks concurrently"""
        tasks = [self.analyze_class(chunk) for chunk in code_chunks]
        return await asyncio.gather(*tasks)

    async def analyze_class(self, code_chunk: str) -> dict:
        for attempt in range(llm_config.max_retries):
            try:
                # Truncate large chunks
                if len(code_chunk) > 3000:
                    truncated = code_chunk[:3000] + "\n// ... [truncated]"
                    self.logger.debug(f"Truncating code chunk from {len(code_chunk)} to 3000 chars")
                else:
                    truncated = code_chunk
                    
                self.logger.debug(f"Analyzing class chunk (attempt {attempt+1})")
                result = await self.class_chain.ainvoke({"code": truncated})
                
                # Post-process result
                result["methods"] = result.get("methods", [])
                result["dependencies"] = result.get("dependencies", [])
                result["complexity"] = result.get("complexity", "unknown")
                
                return result
            except Exception as ex:
                if attempt < llm_config.max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                await self.exception_handler.handle(ex, "analyze_class")
                return self.fallback_class_analysis(code_chunk)
    
    async def analyze_project_overview(self, overview_text: str, project_name: str) -> ProjectOverview:
        try:
            if len(overview_text) > 2000:
                truncated = overview_text[:2000] + "\n[truncated]"
                self.logger.debug("Truncating overview text to 2000 chars")
            else:
                truncated = overview_text
                
            result = await self.overview_chain.ainvoke({"overview_text": truncated})
            # Set project_name directly in the result dictionary
            result["project_name"] = project_name
            return ProjectOverview(**result)
        except Exception as ex:
            await self.exception_handler.handle(ex, "analyze_project_overview")
            return ProjectOverview(
                project_name=project_name,
                purpose="Analysis failed",
                core_functionality="Unknown",
                key_technologies=["Unknown"],
                architecture="Unknown",
                business_domain="Unknown"
            )
    
    def fallback_class_analysis(self, code: str) -> dict:
        class_name = "Unknown"
        match = re.search(r'class\s+(\w+)', code)
        if match:
            class_name = match.group(1)
        
        return JavaClassAnalysis(
            class_name=class_name,
            overview="Analysis failed",
            methods=[],
            dependencies=[],
            complexity="unknown"
        ).dict()