"""
Meta-Path Forward Push (MPFP) graph retrieval.

A sublinear graph traversal algorithm for memory retrieval over heterogeneous
graphs with multiple edge types (semantic, temporal, causal, entity).

Combines meta-path patterns from HIN literature with Forward Push local
propagation from Approximate PPR.

Key properties:
- Sublinear in graph size (threshold pruning bounds active nodes)
- Lazy edge loading: only loads edges for frontier nodes, not entire graph
- Predefined patterns capture different retrieval intents
- All patterns run in parallel, results fused via RRF
- No LLM in the loop during traversal
"""

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, field

from ..db_utils import acquire_with_retry
from ..memory_engine import fq_table
from .graph_retrieval import GraphRetriever
from .types import MPFPTimings, RetrievalResult

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# Data Classes
# -----------------------------------------------------------------------------


@dataclass
class EdgeTarget:
    """A neighbor node with its edge weight."""

    node_id: str
    weight: float


@dataclass
class EdgeCache:
    """
    Cache for lazily-loaded edges.

    Grows per-hop as edges are loaded for frontier nodes.
    Shared across patterns to avoid redundant loads.
    """

    # edge_type -> from_node_id -> list of EdgeTarget
    graphs: dict[str, dict[str, list[EdgeTarget]]] = field(default_factory=dict)
    # Track which (edge_type, node_id) have been loaded
    _loaded: set[tuple[str, str]] = field(default_factory=set)

    def get_neighbors(self, edge_type: str, node_id: str) -> list[EdgeTarget]:
        """Get neighbors for a node via a specific edge type."""
        return self.graphs.get(edge_type, {}).get(node_id, [])

    def get_normalized_neighbors(self, edge_type: str, node_id: str, top_k: int) -> list[EdgeTarget]:
        """Get top-k neighbors with weights normalized to sum to 1."""
        neighbors = self.get_neighbors(edge_type, node_id)[:top_k]
        if not neighbors:
            return []

        total = sum(n.weight for n in neighbors)
        if total == 0:
            return []

        return [EdgeTarget(node_id=n.node_id, weight=n.weight / total) for n in neighbors]

    def is_loaded(self, edge_type: str, node_id: str) -> bool:
        """Check if edges for this node+type have been loaded."""
        return (edge_type, node_id) in self._loaded

    def get_uncached(self, edge_type: str, node_ids: list[str]) -> list[str]:
        """Get node IDs that haven't been loaded yet for this edge type."""
        return [n for n in node_ids if not self.is_loaded(edge_type, n)]

    def add_edges(self, edge_type: str, edges: dict[str, list[EdgeTarget]], all_queried: list[str]):
        """
        Add loaded edges to the cache.

        Args:
            edge_type: Type of edges
            edges: Dict mapping from_node_id -> list of EdgeTarget
            all_queried: All node IDs that were queried (marks them as loaded even if no edges)
        """
        if edge_type not in self.graphs:
            self.graphs[edge_type] = {}

        for node_id, neighbors in edges.items():
            self.graphs[edge_type][node_id] = neighbors

        # Mark all queried nodes as loaded (even if they have no edges)
        for node_id in all_queried:
            self._loaded.add((edge_type, node_id))


@dataclass
class PatternResult:
    """Result from a single pattern traversal."""

    pattern: list[str]
    scores: dict[str, float]  # node_id -> accumulated mass


@dataclass
class MPFPConfig:
    """Configuration for MPFP algorithm."""

    alpha: float = 0.15  # teleport/keep probability
    threshold: float = 1e-6  # mass pruning threshold (lower = explore more)
    top_k_neighbors: int = 20  # fan-out limit per node

    # Patterns from semantic seeds
    patterns_semantic: list[list[str]] = field(
        default_factory=lambda: [
            ["semantic", "semantic"],  # topic expansion
            ["entity", "temporal"],  # entity timeline
            ["semantic", "causes"],  # reasoning chains (forward)
            ["semantic", "caused_by"],  # reasoning chains (backward)
            ["entity", "semantic"],  # entity context
        ]
    )

    # Patterns from temporal seeds
    patterns_temporal: list[list[str]] = field(
        default_factory=lambda: [
            ["temporal", "semantic"],  # what was happening then
            ["temporal", "entity"],  # who was involved then
        ]
    )


@dataclass
class SeedNode:
    """An entry point node with its initial score."""

    node_id: str
    score: float  # initial mass (e.g., similarity score)


# -----------------------------------------------------------------------------
# Lazy Edge Loading
# -----------------------------------------------------------------------------


async def load_edges_for_frontier(
    pool,
    bank_id: str,
    edge_type: str,
    node_ids: list[str],
) -> dict[str, list[EdgeTarget]]:
    """
    Load edges for specific frontier nodes only.

    Args:
        pool: Database connection pool
        bank_id: Memory bank ID
        edge_type: Type of edges to load
        node_ids: Frontier node IDs to load edges for

    Returns:
        Dict mapping from_node_id -> list of EdgeTarget
    """
    if not node_ids:
        return {}

    async with acquire_with_retry(pool) as conn:
        rows = await conn.fetch(
            f"""
            SELECT ml.from_unit_id, ml.to_unit_id, ml.weight
            FROM {fq_table("memory_links")} ml
            WHERE ml.from_unit_id = ANY($1::uuid[])
              AND ml.link_type = $2
              AND ml.weight >= 0.1
            ORDER BY ml.from_unit_id, ml.weight DESC
            """,
            node_ids,
            edge_type,
        )

    result: dict[str, list[EdgeTarget]] = defaultdict(list)
    for row in rows:
        from_id = str(row["from_unit_id"])
        to_id = str(row["to_unit_id"])
        weight = row["weight"]
        result[from_id].append(EdgeTarget(node_id=to_id, weight=weight))

    return dict(result)


# -----------------------------------------------------------------------------
# Core Algorithm (Async with Lazy Loading)
# -----------------------------------------------------------------------------


async def mpfp_traverse_async(
    pool,
    bank_id: str,
    seeds: list[SeedNode],
    pattern: list[str],
    config: MPFPConfig,
    cache: EdgeCache,
) -> PatternResult:
    """
    Async Forward Push traversal with lazy edge loading.

    Loads edges on-demand per hop, only for frontier nodes.

    Args:
        pool: Database connection pool
        bank_id: Memory bank ID
        seeds: Entry point nodes with initial scores
        pattern: Sequence of edge types to follow
        config: Algorithm parameters
        cache: Shared edge cache (grows as edges are loaded)

    Returns:
        PatternResult with accumulated scores per node
    """
    if not seeds:
        return PatternResult(pattern=pattern, scores={})

    scores: dict[str, float] = {}

    # Initialize frontier with seed masses (normalized)
    total_seed_score = sum(s.score for s in seeds)
    if total_seed_score == 0:
        total_seed_score = len(seeds)  # fallback to uniform

    frontier: dict[str, float] = {s.node_id: s.score / total_seed_score for s in seeds}

    # Follow pattern hop by hop
    for edge_type in pattern:
        # Collect frontier nodes above threshold
        active_nodes = [node_id for node_id, mass in frontier.items() if mass >= config.threshold]

        if not active_nodes:
            break

        # Find nodes that need edge loading
        uncached = cache.get_uncached(edge_type, active_nodes)

        # Batch load edges for uncached nodes
        if uncached:
            edges = await load_edges_for_frontier(pool, bank_id, edge_type, uncached)
            cache.add_edges(edge_type, edges, uncached)

        # Propagate mass
        next_frontier: dict[str, float] = {}

        for node_id, mass in frontier.items():
            if mass < config.threshold:
                continue

            # Keep α portion for this node
            scores[node_id] = scores.get(node_id, 0) + config.alpha * mass

            # Push (1-α) to neighbors
            push_mass = (1 - config.alpha) * mass
            neighbors = cache.get_normalized_neighbors(edge_type, node_id, config.top_k_neighbors)

            for neighbor in neighbors:
                next_frontier[neighbor.node_id] = next_frontier.get(neighbor.node_id, 0) + push_mass * neighbor.weight

        frontier = next_frontier

    # Final frontier nodes get their remaining mass
    for node_id, mass in frontier.items():
        if mass >= config.threshold:
            scores[node_id] = scores.get(node_id, 0) + mass

    return PatternResult(pattern=pattern, scores=scores)


def rrf_fusion(
    results: list[PatternResult],
    k: int = 60,
    top_k: int = 50,
) -> list[tuple[str, float]]:
    """
    Reciprocal Rank Fusion to combine pattern results.

    Args:
        results: List of pattern results
        k: RRF constant (higher = more uniform weighting)
        top_k: Number of results to return

    Returns:
        List of (node_id, fused_score) tuples, sorted by score descending
    """
    fused: dict[str, float] = {}

    for result in results:
        if not result.scores:
            continue

        # Rank nodes by their score in this pattern
        ranked = sorted(result.scores.keys(), key=lambda n: result.scores[n], reverse=True)

        for rank, node_id in enumerate(ranked):
            fused[node_id] = fused.get(node_id, 0) + 1.0 / (k + rank + 1)

    # Sort by fused score and return top-k
    sorted_results = sorted(fused.items(), key=lambda x: x[1], reverse=True)

    return sorted_results[:top_k]


# -----------------------------------------------------------------------------
# Database Loading
# -----------------------------------------------------------------------------


async def fetch_memory_units_by_ids(
    pool,
    node_ids: list[str],
    fact_type: str,
) -> list[RetrievalResult]:
    """Fetch full memory unit details for a list of node IDs."""
    if not node_ids:
        return []

    async with acquire_with_retry(pool) as conn:
        rows = await conn.fetch(
            f"""
            SELECT id, text, context, event_date, occurred_start, occurred_end,
                   mentioned_at, access_count, embedding, fact_type, document_id, chunk_id
            FROM {fq_table("memory_units")}
            WHERE id = ANY($1::uuid[])
              AND fact_type = $2
            """,
            node_ids,
            fact_type,
        )

    return [RetrievalResult.from_db_row(dict(r)) for r in rows]


# -----------------------------------------------------------------------------
# Graph Retriever Implementation
# -----------------------------------------------------------------------------


class MPFPGraphRetriever(GraphRetriever):
    """
    Graph retrieval using Meta-Path Forward Push with lazy edge loading.

    Runs predefined patterns in parallel from semantic and temporal seeds,
    loading edges on-demand per hop instead of loading entire graph upfront.
    """

    def __init__(self, config: MPFPConfig | None = None):
        """
        Initialize MPFP retriever.

        Args:
            config: Algorithm configuration (uses defaults if None)
        """
        self.config = config or MPFPConfig()

    @property
    def name(self) -> str:
        return "mpfp"

    async def retrieve(
        self,
        pool,
        query_embedding_str: str,
        bank_id: str,
        fact_type: str,
        budget: int,
        query_text: str | None = None,
        semantic_seeds: list[RetrievalResult] | None = None,
        temporal_seeds: list[RetrievalResult] | None = None,
        adjacency=None,  # Ignored - kept for interface compatibility
    ) -> tuple[list[RetrievalResult], MPFPTimings | None]:
        """
        Retrieve facts using MPFP algorithm with lazy edge loading.

        Args:
            pool: Database connection pool
            query_embedding_str: Query embedding (used for fallback seed finding)
            bank_id: Memory bank ID
            fact_type: Fact type to filter
            budget: Maximum results to return
            query_text: Original query text (optional)
            semantic_seeds: Pre-computed semantic entry points
            temporal_seeds: Pre-computed temporal entry points
            adjacency: Ignored (kept for interface compatibility)

        Returns:
            Tuple of (List of RetrievalResult with activation scores, MPFPTimings)
        """
        import time

        timings = MPFPTimings(fact_type=fact_type)

        # Convert seeds to SeedNode format
        semantic_seed_nodes = self._convert_seeds(semantic_seeds, "similarity")
        temporal_seed_nodes = self._convert_seeds(temporal_seeds, "temporal_score")

        # If no semantic seeds provided, fall back to finding our own
        if not semantic_seed_nodes:
            semantic_seed_nodes = await self._find_semantic_seeds(pool, query_embedding_str, bank_id, fact_type)

        # Collect all pattern jobs
        pattern_jobs = []

        # Patterns from semantic seeds
        for pattern in self.config.patterns_semantic:
            if semantic_seed_nodes:
                pattern_jobs.append((semantic_seed_nodes, pattern))

        # Patterns from temporal seeds
        for pattern in self.config.patterns_temporal:
            if temporal_seed_nodes:
                pattern_jobs.append((temporal_seed_nodes, pattern))

        if not pattern_jobs:
            return [], timings

        timings.pattern_count = len(pattern_jobs)

        # Shared edge cache across all patterns
        cache = EdgeCache()

        # Run all patterns in parallel (each does lazy edge loading)
        step_start = time.time()
        pattern_tasks = [
            mpfp_traverse_async(pool, bank_id, seeds, pattern, self.config, cache) for seeds, pattern in pattern_jobs
        ]
        pattern_results = await asyncio.gather(*pattern_tasks)
        timings.traverse = time.time() - step_start

        # Count edges loaded
        timings.edge_count = sum(len(neighbors) for g in cache.graphs.values() for neighbors in g.values())

        # Fuse results
        step_start = time.time()
        fused = rrf_fusion(pattern_results, top_k=budget)
        timings.fusion = time.time() - step_start

        if not fused:
            return [], timings

        # Get top result IDs
        result_ids = [node_id for node_id, score in fused][:budget]

        # Fetch full details
        step_start = time.time()
        results = await fetch_memory_units_by_ids(pool, result_ids, fact_type)
        timings.fetch = time.time() - step_start
        timings.result_count = len(results)

        # Add activation scores from fusion
        score_map = {node_id: score for node_id, score in fused}
        for result in results:
            result.activation = score_map.get(result.id, 0.0)

        # Sort by activation
        results.sort(key=lambda r: r.activation or 0, reverse=True)

        return results, timings

    def _convert_seeds(
        self,
        seeds: list[RetrievalResult] | None,
        score_attr: str,
    ) -> list[SeedNode]:
        """Convert RetrievalResult seeds to SeedNode format."""
        if not seeds:
            return []

        result = []
        for seed in seeds:
            score = getattr(seed, score_attr, None)
            if score is None:
                score = seed.activation or seed.similarity or 1.0
            result.append(SeedNode(node_id=seed.id, score=score))

        return result

    async def _find_semantic_seeds(
        self,
        pool,
        query_embedding_str: str,
        bank_id: str,
        fact_type: str,
        limit: int = 20,
        threshold: float = 0.3,
    ) -> list[SeedNode]:
        """Fallback: find semantic seeds via embedding search."""
        async with acquire_with_retry(pool) as conn:
            rows = await conn.fetch(
                f"""
                SELECT id, 1 - (embedding <=> $1::vector) AS similarity
                FROM {fq_table("memory_units")}
                WHERE bank_id = $2
                  AND embedding IS NOT NULL
                  AND fact_type = $3
                  AND (1 - (embedding <=> $1::vector)) >= $4
                ORDER BY embedding <=> $1::vector
                LIMIT $5
                """,
                query_embedding_str,
                bank_id,
                fact_type,
                threshold,
                limit,
            )

        return [SeedNode(node_id=str(r["id"]), score=r["similarity"]) for r in rows]
