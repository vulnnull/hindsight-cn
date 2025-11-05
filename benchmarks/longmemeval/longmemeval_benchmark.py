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
    ) -> Tuple[str, str]:
        """
        Generate answer from retrieved memories using OpenAI.

        Returns:
            Tuple of (answer, reasoning)
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
            return answer.strip(), ""  # LongMemEval doesn't use reasoning
        except Exception as e:
            return f"Error generating answer: {str(e)}", ""


class LongMemEvalAnswerEvaluator(LLMAnswerEvaluator):
    """LongMemEval-specific answer evaluator using configurable LLM provider."""

    def __init__(self):
        """Initialize with LLM configuration for judge/evaluator."""
        self.llm_config = LLMConfig.for_judge()
        self.client = self.llm_config.client
        self.model = self.llm_config.model

    async def judge_answer(
        self,
        question: str,
        correct_answer: str,
        predicted_answer: str,
        semaphore: asyncio.Semaphore
    ) -> Tuple[bool, str]:
        """
        Evaluate predicted answer using OpenAI LLM-as-judge.

        Returns:
            Tuple of (is_correct, reasoning)
        """
        async with semaphore:
            prompt = f"""You are an expert evaluator. Evaluate if the predicted answer is semantically equivalent to the gold answer.

Question: {question}

Gold Answer: {correct_answer}

Predicted Answer: {predicted_answer}

Instructions:
- Score 1 if the predicted answer is semantically equivalent (same meaning, different wording is OK)
- Score 1 if the predicted answer correctly abstains when the gold answer indicates the question is unanswerable
- Score 0 if the predicted answer is incorrect or contradicts the gold answer
- Score 0 if the predicted answer provides an answer when it should abstain
- Provide a brief explanation

Output format:
Score: [0 or 1]
Explanation: [brief explanation]"""

            try:
                content = await self.llm_config.call(
                    messages=[{"role": "user", "content": prompt}],
                    scope="judge",
                    temperature=0.0,
                    max_tokens=200
                )

                content = content.strip()

                # Parse score and explanation
                lines = content.split('\n')
                score = 0
                explanation = ""

                for line in lines:
                    if line.startswith("Score:"):
                        score_str = line.replace("Score:", "").strip()
                        score = int(score_str) if score_str.isdigit() else 0
                    elif line.startswith("Explanation:"):
                        explanation = line.replace("Explanation:", "").strip()

                return score == 1, explanation

            except Exception as e:
                return False, f"Evaluation error: {str(e)}"
