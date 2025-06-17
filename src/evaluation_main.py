import json
import os
import sys
import asyncio
from datetime import datetime
from pathlib import Path
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    answer_correctness,
    context_precision,
    context_recall,
    faithfulness
)
from langchain_cohere import ChatCohere
from langchain.embeddings import CohereEmbeddings
from config.config import eval_config, llm_config
import re


class RagasEvaluator:
    def __init__(self):
        self.setup_llm()
        self.setup_embeddings()

        self.metric_map = {
            "answer_correctness": answer_correctness,
            "context_precision": context_precision,
            "context_recall": context_recall,
            "faithfulness": faithfulness
        }

        os.makedirs(os.path.dirname(eval_config.evaluation_output_path), exist_ok=True)

    def setup_llm(self):
        try:
            api_key = llm_config.api_key
            if not api_key:
                print("❌ Cohere API key not found!")
                sys.exit(1)

            self.llm = ChatCohere(
                model=llm_config.model_name,
                cohere_api_key=api_key,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                max_retries=llm_config.max_retries,
                request_timeout=llm_config.timeout,
                timeout=30  # Explicit timeout added
            )
            print(f"✅ Cohere LLM initialized: {llm_config.model_name}")

        except Exception as e:
            print(f"❌ Error setting up LLM: {e}")
            sys.exit(1)

    def setup_embeddings(self):
        try:
            api_key = llm_config.api_key
            if not api_key:
                print("❌ API key missing for embeddings!")
                sys.exit(1)
                
            self.embeddings = CohereEmbeddings(
                model="embed-english-v3.0",
                cohere_api_key=api_key
            )
            print("✅ Cohere embeddings initialized")
        except Exception as e:
            print(f"❌ Embeddings init failed: {e}")
            sys.exit(1)

    def load_json_data(self, path):
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"❌ File not found: {path}")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON format: {path}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Unexpected error loading {path}: {e}")
            sys.exit(1)

    def normalize_name(self, name):
        """Normalize names to improve matching"""
        if not name:
            return ""
        # Remove special characters and convert to lowercase
        name = re.sub(r'[^a-zA-Z0-9]', '', name).lower()
        # Remove common prefixes/suffixes
        name = name.replace("controller", "").replace("service", "")
        return name

    def create_evaluation_dataset(self, gold_data, pred_data):
        questions, ground_truths, answers, contexts = [], [], [], []

        # Create class mapping with normalized keys
        gold_classes = {}
        for idx, c in enumerate(gold_data.get("components", [])):
            class_name = c.get("class_name", f"unknown_class_{idx}")
            # Use normalized name for matching
            norm_name = self.normalize_name(class_name)
            gold_classes[norm_name] = c
            
        pred_classes = {}
        for idx, c in enumerate(pred_data.get("components", [])):
            class_name = c.get("class_name", f"unknown_class_{idx}")
            # Use normalized name for matching
            norm_name = self.normalize_name(class_name)
            pred_classes[norm_name] = c

        # Create a set of all unique normalized class names
        all_classes = set(gold_classes.keys()) | set(pred_classes.keys())

        for norm_class_name in all_classes:
            gold = gold_classes.get(norm_class_name)
            pred = pred_classes.get(norm_class_name)
            
            # If we have gold but no pred, create an empty prediction
            if gold and not pred:
                print(f"⚠️ Creating empty prediction for: {norm_class_name}")
                pred = {
                    "overview": "",
                    "methods": [],
                    "source_file": gold.get("source_file", "")
                }
                
            # If we have pred but no gold, skip
            if pred and not gold:
                print(f"⚠️ Missing gold data for: {norm_class_name}")
                continue
                
            if not gold or not pred:
                continue

            # Get original class name for display
            orig_class_name = gold.get("class_name", norm_class_name)

            # Class overview comparison
            gold_overview = gold.get("overview", "")
            pred_overview = pred.get("overview", "")
            
            if gold_overview or pred_overview:
                questions.append(f"Class overview: {orig_class_name}")
                ground_truths.append(gold_overview)
                answers.append(pred_overview)
                contexts.append([f"Class: {orig_class_name} | File: {gold.get('source_file', 'unknown')}"])

            # Method-level comparison
            gold_methods = {}
            for m in gold.get("methods", []):
                method_name = m.get("name", f"method_{id(m)}")
                # Normalize method names for matching
                norm_method_name = self.normalize_name(method_name)
                gold_methods[norm_method_name] = m
                
            pred_methods = {}
            for m in pred.get("methods", []):
                method_name = m.get("name", f"method_{id(m)}")
                # Normalize method names for matching
                norm_method_name = self.normalize_name(method_name)
                pred_methods[norm_method_name] = m

            # Create a set of all unique normalized method names
            all_methods = set(gold_methods.keys()) | set(pred_methods.keys())

            for norm_method_name in all_methods:
                gold_method = gold_methods.get(norm_method_name)
                pred_method = pred_methods.get(norm_method_name)
                
                # If we have gold method but no pred, create empty prediction
                if gold_method and not pred_method:
                    print(f"⚠️ Creating empty prediction for method: {orig_class_name}.{norm_method_name}")
                    pred_method = {
                        "description": "",
                        "signature": ""
                    }
                    
                # If we have pred method but no gold, skip
                if pred_method and not gold_method:
                    print(f"⚠️ Missing gold data for method: {orig_class_name}.{norm_method_name}")
                    continue
                    
                if not gold_method or not pred_method:
                    continue
                    
                # Get original method name for display
                orig_method_name = gold_method.get("name", norm_method_name)
                    
                gold_desc = gold_method.get("description", "")
                pred_desc = pred_method.get("description", "")
                
                questions.append(f"Method: {orig_class_name}.{orig_method_name}")
                ground_truths.append(gold_desc)
                answers.append(pred_desc)
                contexts.append([
                    f"Method: {orig_method_name} | Signature: {gold_method.get('signature', '')}"
                ])

        if not questions:
            print("⚠️ Warning: No evaluation pairs found. Evaluation may be incomplete.")
            return None

        print(f"✅ Prepared {len(questions)} evaluation pairs")
        return Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "ground_truth": ground_truths,
            "contexts": contexts
        })

    def get_metrics(self):
        valid_metrics = []
        for m in eval_config.metrics:
            if m in self.metric_map:
                valid_metrics.append(self.metric_map[m])
            else:
                print(f"⚠️ Skipping unknown metric: '{m}'")
        return valid_metrics

    async def run_evaluation(self):
        print("🚀 Starting RAGAS Evaluation with Cohere")

        try:
            gold_data = self.load_json_data(eval_config.gold_path)
            pred_data = self.load_json_data(eval_config.predictions_path)
            dataset = self.create_evaluation_dataset(gold_data, pred_data)

            if dataset is None:
                print("❌ Evaluation aborted: No valid data pairs")
                return

            metrics = self.get_metrics()
            if not metrics:
                print("❌ No valid metrics configured. Evaluation aborted.")
                return

            result = evaluate(
                dataset,
                metrics=metrics,
                embeddings=self.embeddings,
                llm=self.llm,
                raise_exceptions=False  # Continue despite individual failures
            )

            # Save detailed per-sample results
            result_df = result.to_pandas()
            result_df.to_csv(eval_config.evaluation_output_path, index=False)

            # Save overall summary
            summary_path = eval_config.evaluation_output_path.replace(".csv", "_summary.txt")
            with open(summary_path, "w") as f:
                f.write("\n📊 Evaluation Summary (Aggregated Metrics):\n")
                for metric_name, score in result.scores.items():
                    f.write(f"{metric_name}: {score:.4f}\n")
                print(f"\n📁 Summary saved to: {summary_path}")

            print(f"✅ Evaluation complete. Output: {eval_config.evaluation_output_path}")
            print(result)
            
        except Exception as e:
            print(f"❌ Evaluation failed: {e}")
            sys.exit(1)


if __name__ == "__main__":
    evaluator = RagasEvaluator()
    asyncio.run(evaluator.run_evaluation())