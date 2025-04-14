#!/usr/bin/env python3
"""
RheumaMIR Benchmarking Script

This script evaluates LLM models on their rheumatology knowledge using the RheumaMIR dataset.

Usage:
  python benchmark_rheuma.py --dataset datasets/RheumaMIR.csv --openai-key YOUR_KEY --gemini-key YOUR_KEY --groq-key YOUR_KEY --claude-key YOUR_KEY
"""

import os
import time
import click
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import matplotlib.pyplot as plt
from tqdm import tqdm
from abc import ABC, abstractmethod
import logging

# API clients
import openai
from google import genai
from google.genai import types
import groq
import anthropic

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelResult:
    """Stores the results of a model evaluation."""

    model_name: str
    accuracy: float
    avg_latency: float
    correct_count: int
    total_questions: int
    question_results: List[Dict[str, Any]]


class LLMModel(ABC):
    """Base abstract class for all LLM models."""

    def __init__(
        self,
        model_name: str,
        api_key: str,
        display_name: str = None,
        init_kwargs: Dict[str, Any] = None,
    ):
        self.model_name = model_name
        self.display_name = display_name or model_name
        self.api_key = api_key
        self.client = self._initialize_client(**(init_kwargs or {}))

    @abstractmethod
    def _initialize_client(self, **kwargs):
        pass

    @abstractmethod
    def query(self, prompt: str) -> Tuple[str, float]:
        pass

    def construct_prompt(self, question: str) -> str:
        return f"""As an expert in rheumatology, please answer the following question with only the answer number (1, 2, 3, or 4):

Question: {question}

Provide only the number."""


class OpenAIModel(LLMModel):
    def _initialize_client(self, **kwargs):
        return openai.Client(api_key=self.api_key, **kwargs)

    def query(self, prompt: str) -> Tuple[str, float]:
        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            # temperature=0,
        )
        end_time = time.time()
        return response.choices[0].message.content, end_time - start_time


class GeminiModel(LLMModel):
    def _initialize_client(self, **kwargs):
        return genai.Client(api_key=self.api_key)

    def query(self, prompt: str) -> Tuple[str, float]:
        start_time = time.time()
        content = types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        response = self.client.models.generate_content(model=self.model_name, contents=content)
        end_time = time.time()
        return response.text, end_time - start_time


class GroqModel(LLMModel):
    def _initialize_client(self, **kwargs):
        return groq.Client(api_key=self.api_key)

    def query(self, prompt: str) -> Tuple[str, float]:
        start_time = time.time()
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        end_time = time.time()
        return response.choices[0].message.content, end_time - start_time


class ClaudeModel(LLMModel):
    def _initialize_client(self, **kwargs):
        return anthropic.Anthropic(api_key=self.api_key)

    def query(self, prompt: str) -> Tuple[str, float]:
        start_time = time.time()
        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=100,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
        )
        end_time = time.time()
        return response.content[0].text, end_time - start_time


def create_model(
    model_type: str, model_name: str, api_key: str, display_name: str = None
) -> LLMModel:
    """Factory function to create a model instance."""
    if model_type == "openai":
        return OpenAIModel(model_name, api_key, display_name)
    elif model_type == "gemini":
        return GeminiModel(model_name, api_key, display_name)
    elif model_type == "groq":
        return GroqModel(model_name, api_key, display_name)
    elif model_type == "grok":
        return OpenAIModel(
            model_name, api_key, display_name, {"base_url": "https://api.x.ai/v1"}
        )
    elif model_type == "claude":
        return ClaudeModel(model_name, api_key, display_name)
    else:
        raise ValueError(f"Unsupported model type: {model_type}")


def check_answer(prediction: str, ground_truth: str) -> bool:
    """Check if prediction matches ground truth."""
    # Extract just the number
    prediction = prediction.strip()
    for char in prediction:
        if char.isdigit():
            prediction = char
            break

    return prediction == ground_truth.strip()


def evaluate_model(
    model: LLMModel, dataset: pd.DataFrame, sample_size: int = None
) -> ModelResult:
    """Evaluate a model on the dataset."""
    # Sample dataset if needed
    if sample_size is not None and sample_size < len(dataset):
        df_sample = dataset.sample(sample_size, random_state=42)
    else:
        df_sample = dataset

    results = []
    latencies = []

    for i in tqdm(range(len(df_sample)), desc=f"Evaluating {model.display_name}"):
        row = df_sample.iloc[i]
        question = row["Question (EN)"]
        ground_truth = row["Official answer"]

        prompt = model.construct_prompt(question)

        logger.debug(f"Prompt: {prompt}")
        logger.debug(f"Ground Truth: {ground_truth}")
        logger.debug(f"Model: {model.display_name}")
        try:
            prediction, latency = model.query(prompt)
            correct = check_answer(prediction, ground_truth)
            logger.debug(f"Prediction: {prediction}")
            logger.debug(f"Correct: {check_answer(prediction, ground_truth)}")

            results.append(
                {
                    "question": question,
                    "ground_truth": ground_truth,
                    "prediction": prediction,
                    "correct": correct,
                    "latency": latency,
                }
            )

            latencies.append(latency)
        except Exception as e:
            logger.error(f"Error querying model: {e}")
            results.append(
                {
                    "question": question,
                    "ground_truth": ground_truth,
                    "prediction": f"ERROR: {str(e)}",
                    "correct": False,
                    "latency": 0.0,
                }
            )

    correct_count = sum(1 for r in results if r["correct"])
    accuracy = correct_count / len(results)

    return ModelResult(
        model_name=model.display_name,
        accuracy=accuracy,
        avg_latency=np.mean(latencies) if latencies else 0,
        correct_count=correct_count,
        total_questions=len(results),
        question_results=results,
    )


def generate_report(results: List[ModelResult], output_dir: str) -> None:
    """Generate report and visualizations."""
    os.makedirs(output_dir, exist_ok=True)

    # Create summary CSV
    summary_df = pd.DataFrame(
        [
            {
                "Model": r.model_name,
                "Accuracy": r.accuracy,
                "Avg Latency (s)": r.avg_latency,
                "Correct": f"{r.correct_count}/{r.total_questions}",
            }
            for r in results
        ]
    )

    summary_df.to_csv(os.path.join(output_dir, "summary.csv"), index=False)

    # Save detailed results for each model
    for result in results:
        pd.DataFrame(result.question_results).to_csv(
            os.path.join(
                output_dir, f"{result.model_name.replace(' ', '_')}_details.csv"
            ),
            index=False,
        )

    # Performance bar chart
    plt.figure(figsize=(10, 6))
    models = [r.model_name for r in results]
    accuracies = [r.accuracy for r in results]

    bars = plt.bar(models, accuracies, color="skyblue")
    plt.ylabel("Accuracy")
    plt.title("Model Accuracy Comparison")
    plt.xticks(rotation=45, ha="right")

    # Add values on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.01,
            f"{height:.2f}",
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "accuracy_comparison.png"), dpi=300)

    # Print summary to console
    best_model = max(results, key=lambda x: x.accuracy)
    logger.info("\nBenchmark Results Summary:")
    logger.info(
        f"Best model: {best_model.model_name} (Accuracy: {best_model.accuracy:.2f})"
    )
    for r in results:
        logger.info(
            f"{r.model_name}: Accuracy={r.accuracy:.2f}, Correct={r.correct_count}/{r.total_questions}"
        )


@click.command()
@click.option(
    "--dataset",
    type=click.Path(exists=True),
    required=True,
    help="RheumaMIR dataset CSV",
    default="datasets/RheumaMIR.csv",
)
@click.option(
    "--openai-key", help="OpenAI API key", default=os.getenv("OPENAI_API_KEY")
)
@click.option(
    "--gemini-key", help="Google Gemini API key", default=os.getenv("GOOGLE_API_KEY")
)
@click.option("--grok-key", help="Grok API key", default=os.getenv("GROK_API_KEY"))
@click.option(
    "--claude-key", help="Anthropic Claude API key", default=os.getenv("CLAUDE_API_KEY")
)
@click.option("--output-dir", default="benchmark_results", help="Results directory")
@click.option(
    "--sample-size", type=int, default=None, help="Sample size (None = use all)"
)
def main(
    dataset,
    openai_key,
    gemini_key,
    grok_key,
    claude_key,
    output_dir,
    sample_size,
):
    """Benchmark LLM models on rheumatology knowledge using RheumaMIR dataset."""
    # Load dataset
    df = pd.read_csv(dataset)
    logger.info(f"Dataset loaded with {len(df)} questions")

    # Define models to evaluate
    models_to_evaluate = []

    if openai_key:
        models_to_evaluate.extend(
            [
                ("openai", "gpt-4o", openai_key, "OpenAI GPT-4o"),
                ("openai", "o3-mini", openai_key, "OpenAI o3-mini"),
            ]
        )

    if gemini_key:
        models_to_evaluate.extend(
            [
                (
                    "gemini",
                    "gemini-2.5-pro-preview-03-25",
                    gemini_key,
                    "Google Gemini 2.5 Pro",
                ),
            ]
        )

    if grok_key:
        models_to_evaluate.extend(
            [
                ("grok", "grok-3-beta", grok_key, "Grok 3"),
                ("grok", "grok-3-fast-beta", grok_key, "Grok 3 Fast"),
            ]
        )

    if claude_key:
        models_to_evaluate.extend(
            [
                ("claude", "claude-3-5-sonnet-latest", claude_key, "Claude 3.5 Sonnet"),
                ("claude", "claude-3-7-sonnet-latest", claude_key, "Claude 3.7 Sonnet"),
            ]
        )

    if not models_to_evaluate:
        logger.error(
            "Error: No models to evaluate. Please provide at least one API key."
        )
        return

    # Evaluate models
    results = []
    for model_type, model_name, api_key, display_name in models_to_evaluate:
        logger.info(f"\nEvaluating {display_name}...")
        model = create_model(model_type, model_name, api_key, display_name)
        result = evaluate_model(model, df, sample_size)
        results.append(result)
        logger.info(f"  Accuracy: {result.accuracy:.2f}")
        logger.info(f"  Correct: {result.correct_count}/{result.total_questions}")

    # Generate report
    generate_report(results, output_dir)
    logger.info(f"\nDetailed results saved to {output_dir}")


if __name__ == "__main__":
    main()
