"""
LongMemEval-specific benchmark implementations.

Provides dataset, answer generator, and evaluator for the LongMemEval benchmark.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
import asyncio
import pydantic
from openai import AsyncOpenAI
import os

# Import common framework
sys.path.insert(0, str(Path(__file__).parent.parent))
from common.benchmark_runner import BenchmarkDataset, LLMAnswerGenerator, LLMAnswerEvaluator
from memora.llm_wrapper import LLMConfig


class LongMemEvalDataset(BenchmarkDataset):
    """LongMemEval dataset implementation."""

    def load(self, path: Path, max_items: Optional[int] = None) -> List[Dict[str, Any]]:
        """Load LongMemEval dataset from JSON file."""
        with open(path, 'r') as f:
            dataset = json.load(f)

        if max_items:
            dataset = dataset[:max_items]

        return dataset

    def get_item_id(self, item: Dict) -> str:
        """Get question ID from LongMemEval item."""
        return item.get("question_id", "unknown")

    def prepare_sessions_for_ingestion(self, item: Dict) -> List[Dict[str, Any]]:
        """
        Prepare LongMemEval conversation sessions for batch ingestion.

        Returns:
            List of session dicts with 'content', 'context', 'event_date'
        """
        sessions = item.get("haystack_sessions", [])
        dates = item.get("haystack_dates", [])
        session_ids = item.get("haystack_session_ids", [])

        # Ensure all lists have same length
        if not (len(sessions) == len(dates) == len(session_ids)):
            min_len = min(len(sessions), len(dates), len(session_ids))
            sessions = sessions[:min_len]
            dates = dates[:min_len]
            session_ids = session_ids[:min_len]

        batch_contents = []

        # Process each session
        for session_turns, date_str, session_id in zip(sessions, dates, session_ids):
            # Parse session date
            session_date = self._parse_date(date_str) if date_str else datetime.now(timezone.utc)

            # Combine all turns in the session into one content string
            session_content_parts = []
            for turn_dict in session_turns:
                role = turn_dict.get("role", "")
                content = turn_dict.get("content", "")

                if not content.strip():
                    continue

                # Format as "role: content"
                session_content_parts.append(f"{role}: {content}")

            # Add session to batch
            if session_content_parts:
                session_content = "\n".join(session_content_parts)
                batch_contents.append({
                    "content": session_content,
                    "context": f"Session {session_id}",
                    "event_date": session_date
                })

        return batch_contents

    def get_qa_pairs(self, item: Dict) -> List[Dict[str, Any]]:
        """
        Extract QA pairs from LongMemEval item.

        For LongMemEval, each item has one question.

        Returns:
            List with single QA dict with 'question', 'answer', 'category'
        """
        return [{
            'question': item.get("question", ""),
            'answer': item.get("answer", ""),
            'category': item.get("question_type", "unknown")
        }]

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date string to datetime object."""
        try:
            # LongMemEval format: "2023/05/20 (Sat) 02:21"
            # Try to parse the main part before the day name
            date_str_cleaned = date_str.split('(')[0].strip() if '(' in date_str else date_str

            # Try multiple formats
            for fmt in ["%Y/%m/%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y/%m/%d"]:
                try:
                    dt = datetime.strptime(date_str_cleaned, fmt)
                    return dt.replace(tzinfo=timezone.utc)
                except ValueError:
                    continue

            # Fallback: try ISO format
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except Exception:
            return datetime.now(timezone.utc)


class LongMemEvalAnswerGenerator(LLMAnswerGenerator):
    """LongMemEval-specific answer generator using configurable LLM provider."""

    def __init__(self):
        """Initialize with LLM configuration for memory operations."""
        self.llm_config = LLMConfig.for_memory()
        self.client = self.llm_config.client
        self.model = self.llm_config.model

    async def generate_answer(
        self,
        question: str,
        memories: List[Dict[str, Any]]
    ) -> Tuple[str, str, Optional[List[Dict[str, Any]]]]:
        """
        Generate answer from retrieved memories using OpenAI.

        Returns:
            Tuple of (answer, reasoning, retrieved_memories_override)
        """
        # Format memories as context
        context_parts = []
        for i, mem in enumerate(memories, 1):
            context_parts.append(f"[Memory {i}] {mem['text']}")

        context = "\n".join(context_parts) if context_parts else "No relevant memories found."

        prompt = f"""You are a helpful assistant. Based on the following memories from past conversations, answer the question.

Memories:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the provided memories
- If the memories don't contain the answer, say "I don't have enough information to answer this question"
- Be concise and direct
- If asked to abstain (e.g., for unanswerable questions), explicitly say you cannot answer

Answer:"""

        try:
            answer = await self.llm_config.call(
                messages=[{"role": "user", "content": prompt}],
                scope="memory",
                temperature=0.0,
                max_tokens=300
            )
            return answer.strip(), "", None  # LongMemEval doesn't use reasoning or override memories
        except Exception as e:
            return f"Error generating answer: {str(e)}", "", None


async def run_benchmark(
    max_instances: int = None,
    max_questions_per_instance: int = None,
    thinking_budget: int = 100,
    max_tokens: int = 4096,
    skip_ingestion: bool = False
):
    """
    Run the LongMemEval benchmark.

    Args:
        max_instances: Maximum number of instances to evaluate (None for all)
        max_questions_per_instance: Maximum questions per instance (for testing)
        thinking_budget: Thinking budget for spreading activation search
        max_tokens: Maximum tokens to retrieve from memories
        skip_ingestion: Whether to skip ingestion and use existing data
    """
    from rich.console import Console
    console = Console()

    # Check dataset exists, download if needed
    dataset_path = Path(__file__).parent / "datasets" / "longmemeval_s_cleaned.json"
    if not dataset_path.exists():
        if not download_dataset(dataset_path):
            console.print(f"[red]Failed to download dataset. Please download manually:[/red]")
            console.print("[yellow]curl -L 'https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json' -o benchmarks/longmemeval/datasets/longmemeval_s_cleaned.json[/yellow]")
            return

    # Initialize components
    dataset = LongMemEvalDataset()
    answer_generator = LongMemEvalAnswerGenerator()
    answer_evaluator = LLMAnswerEvaluator()
    memory = TemporalSemanticMemory(
        db_url=os.getenv("DATABASE_URL"),
        memory_llm_provider=os.getenv("MEMORY_LLM_PROVIDER", "groq"),
        memory_llm_api_key=os.getenv("MEMORY_LLM_API_KEY"),
        memory_llm_model=os.getenv("MEMORY_LLM_MODEL", "openai/gpt-oss-120b"),
        memory_llm_base_url=os.getenv("MEMORY_LLM_BASE_URL") or None,  # Use None to get provider defaults
    )

    # Create benchmark runner
    runner = BenchmarkRunner(
        dataset=dataset,
        answer_generator=answer_generator,
        answer_evaluator=answer_evaluator,
        memory=memory
    )

    # Run benchmark
    # Note: LongMemEval requires clearing agent per item for isolation
    results = await runner.run(
        dataset_path=dataset_path,
        agent_id="longmemeval",
        max_items=max_instances,
        max_questions_per_item=max_questions_per_instance,
        thinking_budget=thinking_budget,
        max_tokens=max_tokens,
        skip_ingestion=skip_ingestion,
        max_concurrent_questions=8,  # Lower for LongMemEval (each has full conversation)
        eval_semaphore_size=8,
        clear_agent_per_item=True  # Clear agent data per item for isolation
    )

    # Display and save results
    runner.display_results(results)
    runner.save_results(results, Path(__file__).parent / 'results' / 'benchmark_results.json')

    # Generate detailed report by question type
    generate_type_report(results)

    return results


def download_dataset(dataset_path: Path) -> bool:
    """
    Download the LongMemEval dataset if it doesn't exist.

    Returns:
        True if successful, False otherwise
    """
    import subprocess
    from rich.console import Console
    console = Console()

    url = "https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json"

    console.print(f"[yellow]Dataset not found. Downloading from HuggingFace...[/yellow]")
    console.print(f"[dim]URL: {url}[/dim]")
    console.print(f"[dim]Destination: {dataset_path}[/dim]")

    try:
        # Use curl to download with progress
        result = subprocess.run(
            ["curl", "-L", "-o", str(dataset_path), url],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode == 0 and dataset_path.exists():
            console.print(f"[green]✓ Dataset downloaded successfully[/green]")
            return True
        else:
            console.print(f"[red]✗ Download failed: {result.stderr}[/red]")
            return False

    except subprocess.TimeoutExpired:
        console.print(f"[red]✗ Download timed out after 5 minutes[/red]")
        return False
    except Exception as e:
        console.print(f"[red]✗ Download error: {e}[/red]")
        return False


def generate_type_report(results: dict):
    """Generate a detailed report by question type."""
    from rich.table import Table
    from rich.console import Console
    console = Console()

    # Aggregate stats by question type
    type_stats = {}

    for item_result in results['item_results']:
        metrics = item_result['metrics']
        by_category = metrics.get('category_stats', {})

        for qtype, stats in by_category.items():
            if qtype not in type_stats:
                type_stats[qtype] = {'total': 0, 'correct': 0}
            type_stats[qtype]['total'] += stats['total']
            type_stats[qtype]['correct'] += stats['correct']

    # Display table
    table = Table(title="Performance by Question Type")
    table.add_column("Question Type", style="cyan")
    table.add_column("Total", justify="right", style="yellow")
    table.add_column("Correct", justify="right", style="green")
    table.add_column("Accuracy", justify="right", style="magenta")

    for qtype, stats in sorted(type_stats.items()):
        acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
        table.add_row(
            qtype,
            str(stats['total']),
            str(stats['correct']),
            f"{acc:.1f}%"
        )

    console.print("\n")
    console.print(table)


if __name__ == "__main__":
    import logging
    import argparse

    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser(description="Run LongMemEval benchmark")
    parser.add_argument(
        "--max-instances",
        type=int,
        default=None,
        help="Limit number of instances to evaluate (default: all 500)"
    )
    parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        help="Limit number of questions per instance (for quick testing)"
    )
    parser.add_argument(
        "--thinking-budget",
        type=int,
        default=100,
        help="Thinking budget for spreading activation search"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=4096,
        help="Maximum tokens to retrieve from memories"
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip ingestion and use existing data"
    )

    args = parser.parse_args()

    results = asyncio.run(run_benchmark(
        max_instances=args.max_instances,
        max_questions_per_instance=args.max_questions,
        thinking_budget=args.thinking_budget,
        max_tokens=args.max_tokens,
        skip_ingestion=args.skip_ingestion
    ))
