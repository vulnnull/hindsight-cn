"""
LoComo Benchmark Runner for Entity-Aware Memory System

Evaluates the memory system on the LoComo (Long-term Conversational Memory) benchmark.

Uses the common benchmark framework with LoComo-specific implementations.
"""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
import argparse
import logging
from memora import TemporalSemanticMemory
from locomo_benchmark import LoComoDataset, LoComoAnswerGenerator, LoComoThinkAnswerGenerator, LoComoAnswerEvaluator
from common.benchmark_runner import BenchmarkRunner


async def run_benchmark(
    max_conversations: int = None,
    max_questions_per_conv: int = None,
    skip_ingestion: bool = False,
    use_think: bool = False
):
    """
    Run the LoComo benchmark.

    Args:
        max_conversations: Maximum number of conversations to evaluate (None for all)
        max_questions_per_conv: Maximum questions per conversation (None for all)
        skip_ingestion: Whether to skip ingestion and use existing data
        use_think: Whether to use the think API instead of search + LLM
    """
    # Initialize components
    dataset = LoComoDataset()
    memory = TemporalSemanticMemory()
    await memory.initialize()

    # Select answer generator based on mode
    if use_think:
        answer_generator = LoComoThinkAnswerGenerator(
            memory=memory,
            agent_id="locomo",
            thinking_budget=500,
            top_k=20
        )
    else:
        answer_generator = LoComoAnswerGenerator()

    answer_evaluator = LoComoAnswerEvaluator()

    # Create benchmark runner
    runner = BenchmarkRunner(
        dataset=dataset,
        answer_generator=answer_generator,
        answer_evaluator=answer_evaluator,
        memory=memory
    )

    # Run benchmark
    dataset_path = Path(__file__).parent / 'locomo10.json'
    results = await runner.run(
        dataset_path=dataset_path,
        agent_id="locomo",
        max_items=max_conversations,
        max_questions_per_item=max_questions_per_conv,
        thinking_budget=500,
        top_k=20,
        skip_ingestion=skip_ingestion,
        max_concurrent_questions=16,
        eval_semaphore_size=8
    )

    # Display and save results
    runner.display_results(results)

    # Determine output filename based on mode
    suffix = "_think" if use_think else ""
    results_filename = f'benchmark_results{suffix}.json'
    runner.save_results(results, Path(__file__).parent / results_filename)

    # Generate markdown table
    generate_markdown_table(results, use_think)

    return results


def generate_markdown_table(results: dict, use_think: bool = False):
    """
    Generate a markdown table with benchmark results.

    Category mapping:
    1 = Multi-hop
    2 = Single-hop
    3 = Temporal
    4 = Open-domain
    """
    from rich.console import Console
    console = Console()

    category_names = {
        '1': 'Multi-hop',
        '2': 'Single-hop',
        '3': 'Temporal',
        '4': 'Open-domain'
    }

    # Build markdown content
    lines = []
    mode_str = " (Think Mode)" if use_think else ""
    lines.append(f"# LoComo Benchmark Results{mode_str}")
    lines.append("")
    lines.append(f"**Overall Accuracy**: {results['overall_accuracy']:.2f}% ({results['total_correct']}/{results['total_questions']})")
    lines.append("")
    lines.append("| Sample ID | Sessions | Questions | Correct | Accuracy | Multi-hop | Single-hop | Temporal | Open-domain |")
    lines.append("|-----------|----------|-----------|---------|----------|-----------|------------|----------|-------------|")

    for item_result in results['item_results']:
        item_id = item_result['item_id']
        num_sessions = item_result['num_sessions']
        metrics = item_result['metrics']

        # Calculate category accuracies
        cat_stats = metrics.get('category_stats', {})
        cat_accuracies = {}

        for cat_id in ['1', '2', '3', '4']:
            if cat_id in cat_stats:
                stats = cat_stats[cat_id]
                acc = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
                cat_accuracies[cat_id] = f"{acc:.1f}% ({stats['correct']}/{stats['total']})"
            else:
                cat_accuracies[cat_id] = "N/A"

        lines.append(
            f"| {item_id} | {num_sessions} | {metrics['total']} | {metrics['correct']} | "
            f"{metrics['accuracy']:.2f}% | {cat_accuracies['1']} | {cat_accuracies['2']} | "
            f"{cat_accuracies['3']} | {cat_accuracies['4']} |"
        )

    # Write to file with suffix
    suffix = "_think" if use_think else ""
    output_file = Path(__file__).parent / f'results_table{suffix}.md'
    output_file.write_text('\n'.join(lines))
    console.print(f"\n[green]✓[/green] Results table saved to {output_file}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

    parser = argparse.ArgumentParser(description='Run LoComo benchmark')
    parser.add_argument('--max-conversations', type=int, default=None, help='Maximum conversations to evaluate')
    parser.add_argument('--max-questions', type=int, default=None, help='Maximum questions per conversation')
    parser.add_argument('--skip-ingestion', action='store_true', help='Skip ingestion and use existing data')
    parser.add_argument('--use-think', action='store_true', help='Use think API instead of search + LLM')

    args = parser.parse_args()

    results = asyncio.run(run_benchmark(
        max_conversations=args.max_conversations,
        max_questions_per_conv=args.max_questions,
        skip_ingestion=args.skip_ingestion,
        use_think=args.use_think
    ))
