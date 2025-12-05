"""
LongMemEval-specific benchmark implementations.

Provides dataset, answer generator, and evaluator for the LongMemEval benchmark.
"""
import sys
from pathlib import Path

from benchmarks.common.benchmark_runner import BenchmarkRunner

import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Tuple, Optional
import asyncio
import pydantic
from openai import AsyncOpenAI
import os

from benchmarks.common.benchmark_runner import BenchmarkDataset, LLMAnswerGenerator, LLMAnswerEvaluator
from hindsight_api.engine.llm_wrapper import LLMConfig


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

            # Clean session turns - remove has_answer key if present
            cleaned_turns = []
            for turn in session_turns:
                if isinstance(turn, dict):
                    # Create a copy without has_answer
                    cleaned_turn = {k: v for k, v in turn.items() if k != 'has_answer'}
                    cleaned_turns.append(cleaned_turn)
                else:
                    cleaned_turns.append(turn)

            session_content = json.dumps(cleaned_turns)
            question_id = item.get("question_id", "unknown")
            document_id = f"{question_id}_{session_id}"
            batch_contents.append({
                "content": session_content,
                "context": f"Session {document_id} - you are the assistant in this conversation - happened on {session_date.strftime('%Y-%m-%d %H:%M:%S')} UTC.",
                "event_date": session_date,
                "document_id": document_id
            })

        return batch_contents

    def get_qa_pairs(self, item: Dict) -> List[Dict[str, Any]]:
        """
        Extract QA pairs from LongMemEval item.

        For LongMemEval, each item has one question.

        Returns:
            List with single QA dict with 'question', 'answer', 'category', 'question_date'
        """
        # Parse question_date if available
        question_date = None
        if 'question_date' in item:
            question_date = self._parse_date(item['question_date'])

        return [{
            'question': item.get("question", ""),
            'answer': item.get("answer", ""),
            'category': item.get("question_type", "unknown"),
            'question_date': question_date
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
            raise ValueError(f"Failed to parse date string: {date_str}")


class QuestionAnswer(pydantic.BaseModel):
    answer: str
    reasoning: str

class LongMemEvalAnswerGenerator(LLMAnswerGenerator):
    """LongMemEval-specific answer generator using configurable LLM provider."""

    def __init__(self):
        """Initialize with LLM configuration for memory operations."""
        self.llm_config = LLMConfig.for_judge()
        self.client = self.llm_config._client
        self.model = self.llm_config.model

    async def generate_answer(
                self,
                question: str,
                recall_result: Dict[str, Any],
                question_date: Optional[datetime] = None,
                question_type: Optional[str] = None
        ) -> Tuple[str, str, Optional[List[Dict[str, Any]]]]:
            """
            Generate answer from retrieved memories using Groq.

            Args:
                question: The question text
                recall_result: Full RecallResult dict containing results, entities, chunks, and trace
                question_date: Date when the question was asked (for temporal context)
                question_type: Question category (e.g., 'single-session-user', 'multi-session-assistant')

            Returns:
                Tuple of (answer, reasoning, None)
                - None indicates to use the memories from recall_result
            """
            context = json.dumps(recall_result)

            # Format question date if provided
            formatted_question_date = question_date.strftime('%Y-%m-%d %H:%M:%S UTC') if question_date else "Not specified"

            # Use LLM to generate answer
            try:
                answer_obj = await self.llm_config.call(
                    messages=[
                        {
                            "role": "user",
                            "content": f"""You are a helpful assistant that must answer user questions based on the previous conversations.

**How to Answer:**
1. Start by scanning retrieved context to understand the facts and events that happened and the timeline.
2. Reason about all the memories and find the right answer, considering the most recent memory as an update of the current facts.
3. If you have 2 possible answers, just say both.

In general the answer must be comprehensive and plenty of details from the retrieved context.

For quantitative questions, use numbers and units. Example: 'How many..', just answer the number and which ones. Consider EACH item even if it's not the most recent one. Reason and do calculation for complex questions.
If questions asks a location (where...?) make sure to include the location name.
For recommendations/suggestions, use the retrieved context to understand the user's preferences and user's personal experiences, and provide a possible answer based on those. Include the reasoning and explicitly say what the user prefers, before making suggestions (user previous experiences or specific requests FROM the user). Consider as much user preferences as possible in your answer.
For questions asking for help or instructions, consider the users' recent memories and previous interactions with the assistant to understand their current situation better (recent purchases, specific product models used..) 
For specific number/value questions, use the context to understand what is the most up-to-date number based on recency, but also include the reasoning (in the answer) on previous possible values and why you think are less relevant.
For open questions, include as much details as possible from different sources that are relevant.
For questions where a specific entity/role is mentioned and it's different from your memory, just say the truth, don't make up anything just to fulfill the question. For example, if the question is about a specific sport, you should consider if the memories and the question are about the same sport. (e.g. american football vs soccer, shows vs podcasts)
For comparative questions, say you don't know the answer if you don't have information about both sides. (or more sides) 
For questions related to time/date, carefully review the question date and the memories date to correctly answer the question.
For questions related to time/date calculation (e.g. How many days passed between X and Y?), carefully review the memories date to correctly answer the question and only provide an answer if you have information about both X and Y, otherwise say it's not possible to calculate and why.

Consider assistant's previous actions (e.g., bookings, reminders) as impactful to the user experiences.


Question: {question}
Question Date: {formatted_question_date}

Retrieved Context:
{context}


Answer:
"""
                        }
                    ],
                    response_format=QuestionAnswer,
                    scope="memory",
                    max_tokens=8192,
                )
                return answer_obj.answer, answer_obj.reasoning + " (question date: " + formatted_question_date + ")", None
            except Exception as e:
                return f"Error generating answer: {str(e)}", "Error occurred during answer generation.", None


async def run_benchmark(
    max_instances: int = None,
    max_instances_per_category: int = None,
    max_questions_per_instance: int = None,
    thinking_budget: int = 500,
    max_tokens: int = 8192,
    skip_ingestion: bool = False,
    filln: bool = False,
    question_id: str = None,
    only_failed: bool = False,
    only_invalid: bool = False,
    only_ingested: bool = False,
    category: str = None,
    max_concurrent_items: int = 1,
    results_filename: str = "benchmark_results.json"
):
    """
    Run the LongMemEval benchmark.

    Args:
        max_instances: Maximum number of instances to evaluate (None for all). Mutually exclusive with max_instances_per_category and category.
        max_instances_per_category: Maximum number of instances per category (None for all). Mutually exclusive with max_instances and category.
        max_questions_per_instance: Maximum questions per instance (for testing)
        thinking_budget: Thinking budget for spreading activation search
        max_tokens: Maximum tokens to retrieve from memories
        skip_ingestion: Whether to skip ingestion and use existing data
        filln: If True, only process questions where the agent has no indexed data yet
        question_id: Optional question ID to filter (e.g., 'e47becba'). Useful with --skip-ingestion.
        only_failed: If True, only run questions that were previously marked as incorrect (is_correct=False)
        only_invalid: If True, only run questions that were previously marked as invalid (is_invalid=True)
        only_ingested: If True, only run questions whose memory bank already exists (has been ingested)
        category: Optional category to filter questions (e.g., 'single-session-user', 'multi-session', 'temporal-reasoning'). Mutually exclusive with max_instances and max_instances_per_category.
        max_concurrent_items: Maximum number of instances to process in parallel (default: 1 for sequential)
        results_filename: Filename for results (default: benchmark_results.json). Directory is fixed to results/.
    """
    from rich.console import Console
    console = Console()

    # Validate mutually exclusive arguments
    exclusive_args = [max_instances is not None, max_instances_per_category is not None, category is not None]
    if sum(exclusive_args) > 1:
        console.print("[red]Error: --max-instances, --max-questions-per-category, and --category are mutually exclusive[/red]")
        return

    # Validate --only-ingested can't be combined with other dataset filters
    if only_ingested:
        incompatible_flags = []
        if only_failed:
            incompatible_flags.append("--only-failed")
        if only_invalid:
            incompatible_flags.append("--only-invalid")
        if category is not None:
            incompatible_flags.append("--category")
        if question_id is not None:
            incompatible_flags.append("--question-id")
        if max_instances_per_category is not None:
            incompatible_flags.append("--max-instances-per-category")

        if incompatible_flags:
            console.print(f"[red]Error: --only-ingested cannot be combined with: {', '.join(incompatible_flags)}[/red]")
            return

    # Check dataset exists, download if needed
    dataset_path = Path(__file__).parent / "datasets" / "longmemeval_s_cleaned.json"
    if not dataset_path.exists():
        if not download_dataset(dataset_path):
            console.print(f"[red]Failed to download dataset. Please download manually:[/red]")
            console.print("[yellow]curl -L 'https://huggingface.co/datasets/xiaowu0162/longmemeval-cleaned/resolve/main/longmemeval_s_cleaned.json' -o benchmarks/longmemeval/datasets/longmemeval_s_cleaned.json[/yellow]")
            return

    # Initialize components
    dataset = LongMemEvalDataset()

    # Start with all items or load from dataset
    original_dataset_items = None
    filtered_items = None

    # Handle max_instances_per_category (aka max_questions_per_category)
    if max_instances_per_category:
        console.print(f"[cyan]Limiting to {max_instances_per_category} questions per category[/cyan]")
        if original_dataset_items is None:
            original_dataset_items = dataset.load(dataset_path, max_items=None)

        # Group by category and take max_instances_per_category from each
        from collections import defaultdict
        category_items = defaultdict(list)
        for item in original_dataset_items:
            cat = item.get('question_type', 'unknown')
            category_items[cat].append(item)

        # Take up to max_instances_per_category from each category
        filtered_items = []
        for cat, items in sorted(category_items.items()):
            limited = items[:max_instances_per_category]
            filtered_items.extend(limited)
            console.print(f"  [green]{cat}:[/green] {len(limited)} questions (of {len(items)} available)")

        console.print(f"[green]Total: {len(filtered_items)} questions across {len(category_items)} categories[/green]")

    # Load previous results if filtering for failed/invalid questions
    failed_question_ids = set()
    invalid_question_ids = set()
    if only_failed or only_invalid:
        results_path = Path(__file__).parent / 'results' / 'benchmark_results.json'
        if not results_path.exists():
            console.print(f"[red]Error: Cannot use --only-failed or --only-invalid without existing results file[/red]")
            console.print(f"[yellow]Results file not found: {results_path}[/yellow]")
            return

        with open(results_path, 'r') as f:
            previous_results = json.load(f)

        # Extract question IDs that failed or are invalid
        for item_result in previous_results.get('item_results', []):
            item_id = item_result['item_id']
            for detail in item_result['metrics'].get('detailed_results', []):
                if only_failed and detail.get('is_correct') == False and not detail.get('is_invalid', False):
                    failed_question_ids.add(item_id)
                if only_invalid and detail.get('is_invalid', False):
                    invalid_question_ids.add(item_id)

        if only_failed:
            console.print(f"[cyan]Filtering to {len(failed_question_ids)} questions that failed (is_correct=False)[/cyan]")
        if only_invalid:
            console.print(f"[cyan]Filtering to {len(invalid_question_ids)} questions that were invalid (is_invalid=True)[/cyan]")

    # Filter dataset by category if specified
    if category:
        console.print(f"[cyan]Filtering questions by category: {category}[/cyan]")
        if original_dataset_items is None:
            # Load full dataset without max_instances limit for filtering
            original_dataset_items = dataset.load(dataset_path, max_items=None)

        filtered_items = [item for item in original_dataset_items if item.get('question_type') == category]

        if not filtered_items:
            console.print(f"[yellow]No questions found for category '{category}'. Available categories:[/yellow]")
            available_categories = set(item.get('question_type', 'unknown') for item in original_dataset_items)
            for cat in sorted(available_categories):
                console.print(f"  - {cat}")
            return

        total_found = len(filtered_items)
        will_run = min(total_found, max_instances) if max_instances else total_found
        if max_instances and total_found > max_instances:
            console.print(f"[green]Found {total_found} questions for category '{category}' (will run {will_run} due to --max-instances)[/green]")
        else:
            console.print(f"[green]Found {total_found} questions for category '{category}'[/green]")

    # Filter dataset based on failed/invalid flags
    if only_failed or only_invalid:
        target_ids = failed_question_ids if only_failed else invalid_question_ids
        if not target_ids:
            filter_type = "failed" if only_failed else "invalid"
            console.print(f"[yellow]No {filter_type} questions found in previous results. Nothing to run.[/yellow]")
            return

        # Load original items if not already loaded
        if original_dataset_items is None:
            # Load full dataset without max_instances limit for filtering
            original_dataset_items = dataset.load(dataset_path, max_items=None)

        # If we already have filtered_items from category filtering, filter those
        # Otherwise start with all items
        items_to_filter = filtered_items if filtered_items is not None else original_dataset_items
        filtered_items = [item for item in items_to_filter if dataset.get_item_id(item) in target_ids]

        filter_type = "failed" if only_failed else "invalid"
        total_found = len(filtered_items)
        will_run = min(total_found, max_instances) if max_instances else total_found
        if max_instances and total_found > max_instances:
            console.print(f"[green]Found {total_found} {filter_type} items to re-evaluate (will run {will_run} due to --max-instances)[/green]")
        else:
            console.print(f"[green]Found {total_found} {filter_type} items to re-evaluate[/green]")

    answer_generator = LongMemEvalAnswerGenerator()
    answer_evaluator = LLMAnswerEvaluator()

    # Create local memory engine
    from benchmarks.common.benchmark_runner import create_memory_engine
    memory = await create_memory_engine()

    # Filter by only_ingested: only run items whose memory bank already exists
    if only_ingested:
        console.print("[cyan]Filtering to only items with existing memory banks...[/cyan]")

        # Load all items if not already loaded
        if original_dataset_items is None:
            original_dataset_items = dataset.load(dataset_path, max_items=None)

        items_to_check = filtered_items if filtered_items is not None else original_dataset_items

        # Check which items have existing banks
        ingested_items = []
        pool = await memory._get_pool()

        for item in items_to_check:
            item_id = dataset.get_item_id(item)
            agent_id = f"longmemeval_{item_id}"

            # Check if bank has any memory units
            async with pool.acquire() as conn:
                result = await conn.fetchrow(
                    "SELECT COUNT(*) as count FROM memory_units WHERE bank_id = $1 LIMIT 1",
                    agent_id
                )
                if result['count'] > 0:
                    ingested_items.append(item)

        filtered_items = ingested_items
        console.print(f"[green]Found {len(filtered_items)} items with existing memory banks[/green]")

        if not filtered_items:
            console.print("[yellow]No items found with existing memory banks. Nothing to run.[/yellow]")
            return

    # Create benchmark runner
    runner = BenchmarkRunner(
        dataset=dataset,
        answer_generator=answer_generator,
        answer_evaluator=answer_evaluator,
        memory=memory
    )

    # If filtering by category, failed, invalid, only_ingested, or max_instances_per_category, we need to use a custom dataset that only returns those items
    # We'll temporarily replace the dataset's load method
    if filtered_items is not None:
        original_load = dataset.load
        def filtered_load(path: Path, max_items: Optional[int] = None):
            return filtered_items[:max_items] if max_items else filtered_items
        dataset.load = filtered_load

    # Run benchmark
    # Single-phase approach: each question gets its own isolated agent_id
    # This ensures each question only has access to its own context
    output_path = Path(__file__).parent / 'results' / results_filename

    # Create results directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    merge_with_existing = (filln or question_id is not None or only_failed or only_invalid or only_ingested or category is not None or max_instances_per_category is not None)

    results = await runner.run(
        dataset_path=dataset_path,
        agent_id="longmemeval",  # Will be suffixed with question_id per item
        max_items=max_instances if not max_instances_per_category else None,  # Don't apply max_items when using per-category limit
        max_questions_per_item=max_questions_per_instance,
        thinking_budget=thinking_budget,
        max_tokens=max_tokens,
        skip_ingestion=skip_ingestion or only_ingested,  # Auto-skip ingestion when using --only-ingested
        max_concurrent_questions=8,
        eval_semaphore_size=8,
        separate_ingestion_phase=False,  # Process each question independently
        clear_agent_per_item=True,  # Use unique agent_id per question
        filln=filln,  # Only process questions without indexed data
        specific_item=question_id,  # Optional filter for specific question ID
        max_concurrent_items=max_concurrent_items,  # Parallel instance processing
        output_path=output_path,  # Save results incrementally
        merge_with_existing=merge_with_existing  # Merge when using --fill, --category, --only-failed, --only-invalid flags or specific question
    )

    # Display results (final save already happened incrementally)
    runner.display_results(results)
    console.print(f"\n[green]✓[/green] Results saved incrementally to {output_path}")

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

    # Create parent directory if it doesn't exist
    dataset_path.parent.mkdir(parents=True, exist_ok=True)

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
        help="Limit TOTAL number of questions to evaluate (default: all 500). For per-category limits, use --max-questions-per-category instead."
    )
    parser.add_argument(
        "--max-instances-per-category",
        "--max-questions-per-category",  # Alias since each instance = 1 question in LongMemEval
        type=int,
        default=None,
        dest="max_instances_per_category",
        help="Limit number of questions per category (e.g., 20 = 20 questions from each of the 6 categories = 120 total). Mutually exclusive with --max-instances and --category."
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
        default=500,
        help="Thinking budget for spreading activation search"
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=8192,
        help="Maximum tokens to retrieve from memories"
    )
    parser.add_argument(
        "--skip-ingestion",
        action="store_true",
        help="Skip ingestion and use existing data"
    )
    parser.add_argument(
        "--fill",
        action="store_true",
        help="Only process questions not already in results file (for resuming interrupted runs)"
    )
    parser.add_argument(
        "--question-id",
        type=str,
        default=None,
        help="Filter to specific question ID (e.g., 'e47becba'). Useful with --skip-ingestion to test a single question."
    )
    parser.add_argument(
        "--only-failed",
        action="store_true",
        help="Only run questions that were previously marked as incorrect (is_correct=False). Requires existing results file."
    )
    parser.add_argument(
        "--only-invalid",
        action="store_true",
        help="Only run questions that were previously marked as invalid (is_invalid=True). Requires existing results file."
    )
    parser.add_argument(
        "--only-ingested",
        action="store_true",
        help="Only run questions whose memory bank already exists (has been ingested). Automatically skips ingestion. Cannot be combined with --only-failed, --only-invalid, --category, --question-id, or --max-instances-per-category."
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="Filter questions by category/question_type. Available categories: 'single-session-user', 'multi-session', 'single-session-preference', 'temporal-reasoning', 'knowledge-update', 'single-session-assistant'. Mutually exclusive with --max-instances and --max-instances-per-category."
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="Number of instances to process in parallel (default: 1 for sequential). Higher values speed up evaluation but use more memory."
    )
    parser.add_argument(
        "--results-filename",
        type=str,
        default="benchmark_results.json",
        help="Filename for results output (default: benchmark_results.json). Saved in results/ directory."
    )

    args = parser.parse_args()

    # Validate that only one of --only-failed or --only-invalid is set
    if args.only_failed and args.only_invalid:
        parser.error("Cannot use both --only-failed and --only-invalid at the same time")

    # Validate mutually exclusive arguments
    exclusive_count = sum([
        args.max_instances is not None,
        args.max_instances_per_category is not None,
        args.category is not None
    ])
    if exclusive_count > 1:
        parser.error("--max-instances, --max-questions-per-category, and --category are mutually exclusive")

    results = asyncio.run(run_benchmark(
        max_instances=args.max_instances,
        max_instances_per_category=args.max_instances_per_category,
        max_questions_per_instance=args.max_questions,
        thinking_budget=args.thinking_budget,
        max_tokens=args.max_tokens,
        skip_ingestion=args.skip_ingestion,
        filln=args.fill,
        question_id=args.question_id,
        only_failed=args.only_failed,
        only_invalid=args.only_invalid,
        only_ingested=args.only_ingested,
        category=args.category,
        max_concurrent_items=args.parallel,
        results_filename=args.results_filename
    ))
