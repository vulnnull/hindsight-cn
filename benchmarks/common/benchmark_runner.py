"""
Common benchmark runner framework based on the LoComo implementation.

This module provides a unified interface for running benchmarks with the same
optimizations as the working LoComo benchmark:
- Batch ingestion for speed
- Parallel question processing with semaphores
- Parallel LLM judging with rate limiting
- Progress tracking with Rich
- Comprehensive metrics collection
- Support for both traditional (search + LLM) and integrated (think API) approaches

The framework supports two answer generation patterns:
1. Traditional: Benchmark runner performs search, then passes results to answer generator
2. Integrated: Answer generator performs its own retrieval (e.g., think API)
   - Indicated by needs_external_search() returning False
   - Skips the search step for efficiency
"""

import json
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table
from rich import box
import pydantic

from memora import TemporalSemanticMemory
from openai import AsyncOpenAI

console = Console()


class BenchmarkDataset(ABC):
    """Abstract base class for benchmark datasets."""

    @abstractmethod
    def load(self, path: Path, max_items: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Load dataset from file.

        Returns:
            List of dataset items
        """
        pass

    @abstractmethod
    def get_item_id(self, item: Dict) -> str:
        """Get unique identifier for an item."""
        pass

    @abstractmethod
    def prepare_sessions_for_ingestion(self, item: Dict) -> List[Dict[str, Any]]:
        """
        Prepare conversation sessions for batch ingestion.

        Returns:
            List of session dicts with keys: 'content', 'context', 'event_date'
        """
        pass

    @abstractmethod
    def get_qa_pairs(self, item: Dict) -> List[Dict[str, Any]]:
        """
        Extract QA pairs from an item.

        Returns:
            List of QA dicts with keys: 'question', 'answer', 'category' (optional)
        """
        pass


class LLMAnswerGenerator(ABC):
    """Abstract base class for LLM-based answer generation."""

    def needs_external_search(self) -> bool:
        """
        Whether this generator needs external search to be performed.

        Returns:
            True if the benchmark runner should perform search before calling generate_answer.
            False if the generator does its own retrieval (e.g., integrated think API).
        """
        return True

    @abstractmethod
    async def generate_answer(
        self,
        question: str,
        memories: List[Dict[str, Any]]
    ) -> Tuple[str, str, Optional[List[Dict[str, Any]]]]:
        """
        Generate answer from retrieved memories.

        Returns:
            Tuple of (answer, reasoning, retrieved_memories_override)
            - answer: The generated answer text
            - reasoning: Explanation of how the answer was derived
            - retrieved_memories_override: Optional list of memories to include in results
              - None: Use memories passed in (traditional mode)
              - List: Use these memories instead (integrated mode like think API)
        """
        pass


class LLMAnswerEvaluator(ABC):
    """Abstract base class for LLM-based answer evaluation."""

    @abstractmethod
    async def judge_answer(
        self,
        question: str,
        correct_answer: str,
        predicted_answer: str,
        semaphore: asyncio.Semaphore
    ) -> Tuple[bool, str]:
        """
        Evaluate predicted answer against correct answer.

        Args:
            question: The question
            correct_answer: Gold/correct answer
            predicted_answer: Predicted answer
            semaphore: Semaphore for rate limiting

        Returns:
            Tuple of (is_correct, reasoning)
        """
        pass


class BenchmarkRunner:
    """
    Common benchmark runner using the proven LoComo approach.

    Optimizations:
    - Batch ingestion (put_batch_async)
    - Parallel question processing with rate limiting
    - Parallel LLM judging with rate limiting
    - Progress tracking
    """

    def __init__(
        self,
        dataset: BenchmarkDataset,
        answer_generator: LLMAnswerGenerator,
        answer_evaluator: LLMAnswerEvaluator,
        memory: Optional[TemporalSemanticMemory] = None
    ):
        """
        Initialize benchmark runner.

        Args:
            dataset: Dataset implementation
            answer_generator: Answer generator implementation
            answer_evaluator: Answer evaluator implementation
            memory: Memory system instance (creates new if None)
        """
        self.dataset = dataset
        self.answer_generator = answer_generator
        self.answer_evaluator = answer_evaluator
        self.memory = memory or TemporalSemanticMemory()

    async def ingest_conversation(
        self,
        item: Dict[str, Any],
        agent_id: str
    ) -> int:
        """
        Ingest conversation into memory using batch ingestion.

        Uses put_batch_async for maximum efficiency.

        Returns:
            Number of sessions ingested
        """
        batch_contents = self.dataset.prepare_sessions_for_ingestion(item)

        if batch_contents:
            await self.memory.put_batch_async(
                agent_id=agent_id,
                contents=batch_contents
            )

        return len(batch_contents)

    async def answer_question(
        self,
        agent_id: str,
        question: str,
        thinking_budget: int = 500,
        top_k: int = 20,
        weight_activation: float = 0.30,
        weight_semantic: float = 0.30,
        weight_recency: float = 0.25,
        weight_frequency: float = 0.15,
    ) -> Tuple[str, str, List[Dict]]:
        """
        Answer a question using memory retrieval.

        Returns:
            Tuple of (answer, reasoning, retrieved_memories)
        """
        # Check if generator needs external search
        if self.answer_generator.needs_external_search():
            # Traditional flow: search then generate
            results, _ = await self.memory.search_async(
                agent_id=agent_id,
                query=question,
                thinking_budget=thinking_budget,
                top_k=top_k,
                weight_activation=weight_activation,
                weight_semantic=weight_semantic,
                weight_recency=weight_recency,
                weight_frequency=weight_frequency,
                fact_type="world"
            )

            if not results:
                return "I don't have enough information to answer that question.", "No relevant memories found.", []

            # Generate answer using LLM
            answer, reasoning, memories_override = await self.answer_generator.generate_answer(question, results)

            # Use override if provided, otherwise use search results
            final_memories = memories_override if memories_override is not None else results

            return answer, reasoning, final_memories
        else:
            # Integrated flow: generator does its own search (e.g., think API)
            # Pass empty memories list since generator doesn't need them
            answer, reasoning, memories_override = await self.answer_generator.generate_answer(question, [])

            # Use memories from generator (should not be None for integrated mode)
            final_memories = memories_override if memories_override is not None else []

            return answer, reasoning, final_memories

    async def evaluate_qa_task(
        self,
        agent_id: str,
        qa_pairs: List[Dict],
        item_id: str,
        thinking_budget: int,
        top_k: int,
        max_questions: Optional[int] = None,
        semaphore: asyncio.Semaphore = None,
        weight_activation: float = 0.30,
        weight_semantic: float = 0.30,
        weight_recency: float = 0.25,
        weight_frequency: float = 0.15,
    ) -> List[Dict]:
        """
        Evaluate QA task with parallel question processing.

        Args:
            semaphore: Semaphore to limit concurrent question processing

        Returns:
            List of QA results
        """
        # Filter out questions without answers (category 5)
        qa_pairs = [pair for pair in qa_pairs if pair.get('answer')]
        questions_to_eval = qa_pairs[:max_questions] if max_questions else qa_pairs

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[cyan]Evaluating QA for {item_id} - {len(questions_to_eval)} questions",
                total=len(questions_to_eval)
            )

            # Create tasks for all questions
            async def process_question(qa):
                async with semaphore:
                    question = qa['question']
                    correct_answer = qa['answer']
                    category = qa.get('category', 0)

                    # Get predicted answer, reasoning, and retrieved memories
                    predicted_answer, reasoning, retrieved_memories = await self.answer_question(
                        agent_id, question, thinking_budget, top_k,
                        weight_activation, weight_semantic, weight_recency, weight_frequency
                    )

                    return {
                        'question': question,
                        'correct_answer': correct_answer,
                        'predicted_answer': predicted_answer,
                        'reasoning': reasoning,
                        'category': category,
                        'retrieved_memories': retrieved_memories
                    }

            question_tasks = [process_question(qa) for qa in questions_to_eval]

            # Use as_completed to update progress as results come in
            results = []
            for coro in asyncio.as_completed(question_tasks):
                result = await coro
                results.append(result)
                progress.update(task, advance=1)

        return results

    async def calculate_metrics(self, results: List[Dict], eval_semaphore_size: int = 8) -> Dict:
        """
        Calculate evaluation metrics using parallel LLM-as-judge.

        Args:
            results: QA results to evaluate
            eval_semaphore_size: Max concurrent LLM judge requests

        Returns:
            Dict with evaluation metrics
        """
        total = len(results)

        # Semaphore to limit concurrent requests
        semaphore = asyncio.Semaphore(eval_semaphore_size)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"[yellow]Judging answers with LLM (parallel, max {eval_semaphore_size})...",
                total=total
            )

            # Create all judgment tasks
            async def judge_single(result):
                is_correct, eval_reasoning = await self.answer_evaluator.judge_answer(
                    result['question'],
                    result['correct_answer'],
                    result['predicted_answer'],
                    semaphore
                )
                result['is_correct'] = is_correct
                result['correctness_reasoning'] = eval_reasoning
                return result

            judgment_tasks = [judge_single(result) for result in results]

            # Process in parallel with progress updates
            judged_results = []
            for coro in asyncio.as_completed(judgment_tasks):
                judged_result = await coro
                judged_results.append(judged_result)
                progress.update(task, advance=1)

        # Calculate stats
        correct = sum(1 for r in judged_results if r.get('is_correct', False))
        category_stats = {}

        for result in judged_results:
            category = result.get('category', 'unknown')
            if category not in category_stats:
                category_stats[category] = {'correct': 0, 'total': 0}
            category_stats[category]['total'] += 1
            if result.get('is_correct', False):
                category_stats[category]['correct'] += 1

        accuracy = (correct / total * 100) if total > 0 else 0

        return {
            'accuracy': accuracy,
            'correct': correct,
            'total': total,
            'category_stats': category_stats,
            'detailed_results': judged_results
        }

    async def process_single_item(
        self,
        item: Dict,
        agent_id: str,
        i: int,
        total_items: int,
        thinking_budget: int,
        top_k: int,
        max_questions_per_item: Optional[int],
        skip_ingestion: bool,
        question_semaphore: asyncio.Semaphore,
        eval_semaphore_size: int = 8,
        weight_activation: float = 0.30,
        weight_semantic: float = 0.30,
        weight_recency: float = 0.25,
        weight_frequency: float = 0.15,
    ) -> Dict:
        """
        Process a single item (ingest + evaluate).

        Returns:
            Result dict with metrics
        """
        item_id = self.dataset.get_item_id(item)

        console.print(f"\n[bold blue]Item {i}/{total_items}[/bold blue] (ID: {item_id})")

        if not skip_ingestion:
            # Clear previous agent data only on first item
            if i == 1:
                console.print("  [1] Clearing previous agent data...")
                await self.memory.delete_agent(agent_id)
                console.print(f"      [green]✓[/green] Cleared '{agent_id}' agent data")

            # Ingest conversation
            console.print("  [2] Ingesting conversation (batch mode)...")
            num_sessions = await self.ingest_conversation(item, agent_id)
            console.print(f"      [green]✓[/green] Ingested {num_sessions} sessions")
        else:
            num_sessions = -1

        # Evaluate QA
        qa_pairs = self.dataset.get_qa_pairs(item)
        console.print(f"  [3] Evaluating {len(qa_pairs)} QA pairs (parallel)...")
        qa_results = await self.evaluate_qa_task(
            agent_id,
            qa_pairs,
            item_id,
            thinking_budget,
            top_k,
            max_questions_per_item,
            question_semaphore,
            weight_activation,
            weight_semantic,
            weight_recency,
            weight_frequency
        )

        # Calculate metrics
        console.print("  [4] Calculating metrics...")
        metrics = await self.calculate_metrics(qa_results, eval_semaphore_size)

        console.print(f"      [green]✓[/green] Accuracy: {metrics['accuracy']:.2f}% ({metrics['correct']}/{metrics['total']})")

        return {
            'item_id': item_id,
            'metrics': metrics,
            'num_sessions': num_sessions
        }

    async def run(
        self,
        dataset_path: Path,
        agent_id: str,
        max_items: Optional[int] = None,
        max_questions_per_item: Optional[int] = None,
        thinking_budget: int = 500,
        top_k: int = 20,
        skip_ingestion: bool = False,
        max_concurrent_questions: int = 16,
        eval_semaphore_size: int = 8,
        clear_agent_per_item: bool = False,
        weight_activation: float = 0.30,
        weight_semantic: float = 0.30,
        weight_recency: float = 0.25,
        weight_frequency: float = 0.15,
    ) -> Dict[str, Any]:
        """
        Run the full benchmark evaluation.

        Args:
            dataset_path: Path to dataset file
            agent_id: Agent ID to use
            max_items: Maximum number of items to evaluate
            max_questions_per_item: Maximum questions per item
            thinking_budget: Thinking budget for search
            top_k: Number of memories to retrieve
            skip_ingestion: Skip ingestion and use existing data
            max_concurrent_questions: Max concurrent question processing
            eval_semaphore_size: Max concurrent LLM judge requests
            clear_agent_per_item: Clear agent data before each item (for isolation)
            weight_activation: Weight for activation score in final ranking (default: 0.30)
            weight_semantic: Weight for semantic similarity in final ranking (default: 0.30)
            weight_recency: Weight for recency score in final ranking (default: 0.25)
            weight_frequency: Weight for frequency score in final ranking (default: 0.15)

        Returns:
            Dict with complete benchmark results
        """
        console.print(f"\n[bold cyan]Benchmark Evaluation[/bold cyan]")
        console.print("=" * 80)

        # Load dataset
        console.print(f"\n[1] Loading dataset from {dataset_path}...")
        items = self.dataset.load(dataset_path, max_items)
        console.print(f"    [green]✓[/green] Loaded {len(items)} items")

        # Initialize memory system
        console.print(f"\n[2] Initializing memory system...")
        console.print(f"    [green]✓[/green] Memory system initialized")

        # Create semaphore for question processing
        question_semaphore = asyncio.Semaphore(max_concurrent_questions)

        # Process items
        all_results = []

        for i, item in enumerate(items, 1):
            # Clear agent per item if requested (for isolation in benchmarks like LongMemEval)
            if clear_agent_per_item and i > 1 and not skip_ingestion:
                await self.memory.delete_agent(agent_id)

            result = await self.process_single_item(
                item, agent_id, i, len(items),
                thinking_budget, top_k, max_questions_per_item,
                skip_ingestion, question_semaphore, eval_semaphore_size,
                weight_activation, weight_semantic, weight_recency, weight_frequency
            )
            all_results.append(result)

        # Calculate overall metrics
        total_correct = sum(r['metrics']['correct'] for r in all_results)
        total_questions = sum(r['metrics']['total'] for r in all_results)
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0

        return {
            'overall_accuracy': overall_accuracy,
            'total_correct': total_correct,
            'total_questions': total_questions,
            'num_items': len(items),
            'item_results': all_results
        }

    def display_results(self, results: Dict[str, Any]):
        """Display benchmark results in a formatted table."""
        console.print("\n[bold green]✓ Benchmark Complete![/bold green]\n")

        # Display results table
        table = Table(title="Benchmark Results", box=box.ROUNDED)
        table.add_column("Item ID", style="cyan")
        table.add_column("Sessions", justify="right", style="yellow")
        table.add_column("Questions", justify="right", style="blue")
        table.add_column("Correct", justify="right", style="green")
        table.add_column("Accuracy", justify="right", style="magenta")

        for result in results['item_results']:
            metrics = result['metrics']
            table.add_row(
                result['item_id'],
                str(result['num_sessions']),
                str(metrics['total']),
                str(metrics['correct']),
                f"{metrics['accuracy']:.1f}%"
            )

        table.add_row(
            "[bold]OVERALL[/bold]",
            "-",
            f"[bold]{results['total_questions']}[/bold]",
            f"[bold]{results['total_correct']}[/bold]",
            f"[bold]{results['overall_accuracy']:.1f}%[/bold]"
        )

        console.print(table)

    def save_results(self, results: Dict[str, Any], output_path: Path):
        """Save results to JSON file."""
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        console.print(f"\n[green]✓[/green] Results saved to {output_path}")
