"""
LongMemEval Benchmark Evaluation

This script evaluates the Entity-Aware Memory System on the LongMemEval benchmark,
which tests five core long-term memory abilities:
1. Information extraction
2. Multi-session reasoning
3. Temporal reasoning
4. Knowledge updates
5. Abstention

Dataset: LongMemEval-S (~115k tokens, ~40 sessions per instance, 500 questions)
Source: https://github.com/xiaowu0162/LongMemEval

Uses the common benchmark framework with LongMemEval-specific implementations.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import argparse
import subprocess
import logging
from rich.console import Console
from memora import TemporalSemanticMemory
from longmemeval_benchmark import LongMemEvalDataset, LongMemEvalAnswerGenerator, LongMemEvalAnswerEvaluator
from common.benchmark_runner import BenchmarkRunner

console = Console()


def download_dataset(dataset_path: Path) -> bool:
    """
    Download the LongMemEval dataset if it doesn't exist.

    Returns:
        True if successful, False otherwise
    """
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


async def run_benchmark(
    max_instances: int = None,
    max_questions_per_instance: int = None,
    thinking_budget: int = 100,
    top_k: int = 20,
    skip_ingestion: bool = False
):
    """
    Run the LongMemEval benchmark.

    Args:
        max_instances: Maximum number of instances to evaluate (None for all)
        max_questions_per_instance: Maximum questions per instance (for testing)
        thinking_budget: Thinking budget for spreading activation search
        top_k: Number of memory units to retrieve per query
        skip_ingestion: Whether to skip ingestion and use existing data
    """
    # Check dataset exists, download if needed
    dataset_path = Path(__file__).parent / "longmemeval_s_cleaned.json"
    if not dataset_path.exists():
        if not download_dataset(dataset_path):
            console.print(f"[red]Failed to download dataset. Please download manually:[/red]")
            console.print("[yellow]curl -L 'https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json' -o benchmarks/longmemeval/longmemeval_s_cleaned.json[/yellow]")
            return

    # Initialize components
    dataset = LongMemEvalDataset()
    answer_generator = LongMemEvalAnswerGenerator()
    answer_evaluator = LongMemEvalAnswerEvaluator()
    memory = TemporalSemanticMemory()

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
        top_k=top_k,
        skip_ingestion=skip_ingestion,
        max_concurrent_questions=8,  # Lower for LongMemEval (each has full conversation)
        eval_semaphore_size=8,
        clear_agent_per_item=True  # Clear agent data per item for isolation
    )

    # Display and save results
    runner.display_results(results)
    runner.save_results(results, Path(__file__).parent / 'benchmark_results.json')

    # Generate detailed report by question type
    generate_type_report(results)

    return results


def generate_type_report(results: dict):
    """Generate a detailed report by question type."""
    from rich.table import Table

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
        "--top-k",
        type=int,
        default=20,
        help="Number of memory units to retrieve per query"
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
        top_k=args.top_k,
        skip_ingestion=args.skip_ingestion
    ))
