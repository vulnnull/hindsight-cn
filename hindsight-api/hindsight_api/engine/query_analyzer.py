"""
Query analysis abstraction for the memory system.

Provides an interface for analyzing natural language queries to extract
structured information like temporal constraints.
"""
from abc import ABC, abstractmethod
from typing import Optional
from datetime import datetime
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TemporalConstraint(BaseModel):
    """
    Temporal constraint extracted from a query.

    Represents a time range with start and end dates.
    """
    start_date: datetime = Field(description="Start of the time range (inclusive)")
    end_date: datetime = Field(description="End of the time range (inclusive)")

    def __str__(self) -> str:
        return f"{self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}"


class QueryAnalysis(BaseModel):
    """
    Result of analyzing a natural language query.

    Contains extracted structured information like temporal constraints.
    """
    temporal_constraint: Optional[TemporalConstraint] = Field(
        default=None,
        description="Extracted temporal constraint, if any"
    )


class QueryAnalyzer(ABC):
    """
    Abstract base class for query analysis.

    Implementations analyze natural language queries to extract structured
    information like temporal constraints, entities, etc.
    """

    @abstractmethod
    def load(self) -> None:
        """
        Load the query analyzer model.

        This should be called during initialization to load the model
        and avoid cold start latency on first analyze() call.
        """
        pass

    @abstractmethod
    def analyze(
        self, query: str, reference_date: Optional[datetime] = None
    ) -> QueryAnalysis:
        """
        Analyze a natural language query.

        Args:
            query: Natural language query to analyze
            reference_date: Reference date for relative terms (defaults to now)

        Returns:
            QueryAnalysis containing extracted information
        """
        pass


class TransformerQueryAnalyzer(QueryAnalyzer):
    """
    Query analyzer using T5-based generative models.

    Uses T5 to convert natural language temporal expressions into structured
    date ranges without pattern matching or regex.

    Performance:
    - ~30-80ms on CPU, ~5-15ms on GPU
    - Model size: ~80M params (~300MB download)
    """

    def __init__(
        self,
        model_name: str = "google/flan-t5-small",
        device: str = "cpu"
    ):
        """
        Initialize T5 query analyzer.

        Args:
            model_name: Name of the HuggingFace T5 model to use.
                       Default: google/flan-t5-small (~80M params, ~300MB download)
                       Alternative: google/flan-t5-base (~1GB, more accurate)
            device: Device to run model on ("cpu" or "cuda")
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self._tokenizer = None

    def load(self) -> None:
        """Load the T5 model for temporal extraction."""
        if self._model is not None:
            return

        try:
            from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        except ImportError:
            raise ImportError(
                "transformers is required for TransformerQueryAnalyzer. "
                "Install it with: pip install transformers"
            )

        logger.info(f"Loading query analyzer model: {self.model_name}...")
        self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self._model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
        self._model.to(self.device)
        self._model.eval()
        logger.info("Query analyzer model loaded")

    def _load_model(self):
        """Lazy load the T5 model for temporal extraction (calls load())."""
        self.load()

    def analyze(
        self, query: str, reference_date: Optional[datetime] = None
    ) -> QueryAnalysis:
        """
        Analyze query using T5 model.

        Uses T5 to generate structured temporal output directly.

        Args:
            query: Natural language query
            reference_date: Reference date for relative terms (defaults to now)

        Returns:
            QueryAnalysis with temporal_constraint if found
        """
        if reference_date is None:
            reference_date = datetime.now()

        self._load_model()

        # Build prompt for T5 to generate structured temporal output
        # Use fill-in-the-blank format which T5 handles better
        prompt = f"""Today is {reference_date.strftime('%Y-%m-%d')}. Convert temporal expressions to date ranges.

June 2024 = 2024-06-01 to 2024-06-30
March 2023 = 2023-03-01 to 2023-03-31
dogs in June 2023 = 2023-06-01 to 2023-06-30
last year = {reference_date.year - 1}-01-01 to {reference_date.year - 1}-12-31
events in January 2020 = 2020-01-01 to 2020-01-31
what is the weather = none
{query} ="""

        # Tokenize and generate
        inputs = self._tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with self._no_grad():
            outputs = self._model.generate(
                **inputs,
                max_new_tokens=30,
                num_beams=3,
                do_sample=False,
                temperature=1.0
            )

        result = self._tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

        # Parse the generated output
        temporal = self._parse_generated_output(result, reference_date)
        return QueryAnalysis(temporal_constraint=temporal)

    def _no_grad(self):
        """Get torch.no_grad context manager."""
        try:
            import torch
            return torch.no_grad()
        except ImportError:
            from contextlib import nullcontext
            return nullcontext()

    def _parse_generated_output(
        self, result: str, reference_date: datetime
    ) -> Optional[TemporalConstraint]:
        """
        Parse T5 generated output into TemporalConstraint.

        Expected format: "YYYY-MM-DD to YYYY-MM-DD"

        Args:
            result: Generated text from T5
            reference_date: Reference date for validation

        Returns:
            TemporalConstraint if valid output, else None
        """
        if not result or result.lower().strip() in ("none", "null", "no"):
            return None

        try:
            # Parse "YYYY-MM-DD to YYYY-MM-DD"
            import re
            pattern = r'(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})'
            match = re.search(pattern, result, re.IGNORECASE)

            if match:
                start_str = match.group(1)
                end_str = match.group(2)

                start_date = datetime.strptime(start_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_str, "%Y-%m-%d")

                # Set time boundaries
                start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)

                # Validation
                if end_date < start_date:
                    logger.warning(f"Invalid date range: {start_date} to {end_date}")
                    return None

                return TemporalConstraint(start_date=start_date, end_date=end_date)

        except (ValueError, AttributeError) as e:
            return None

        return None
