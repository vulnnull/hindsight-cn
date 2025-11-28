# Hindsight: A Unified Memory System for AI Agents with Temporal Retrieval and Personality-Driven Reasoning

## Abstract

We present **Hindsight**, a comprehensive memory architecture for conversational AI agents that combines multi-strategy retrieval with personality-driven reasoning to enable both high-recall factual search and consistent, trait-based opinion formation. The system consists of two integrated components: **TEMPR (Temporal Entity Memory Priming Retrieval)** for memory recall, and **CARA (Coherent Adaptive Reasoning Agents)** for personality-aware reflection. TEMPR achieves strong retrieval performance through four parallel search strategies—semantic vector search, BM25 keyword matching, graph-based spreading activation incorporating multiple link types (entity, semantic, temporal, causal), and temporal-aware graph traversal—achieving 73.50% on LoComo and 80.60% on LongMemEval benchmarks, with particularly strong performance on multi-hop reasoning (+15.8% over baseline). CARA builds on TEMPR's four-network architecture (world facts, bank experiences, opinions, and observations) to enable personality-driven reasoning using the Big Five model, allowing agents to form and evolve opinions influenced by configurable traits while maintaining epistemic clarity between objective information and subjective beliefs. A novel observation paradigm automatically synthesizes entity-level summaries from multiple facts, creating structured mental models of people, organizations, and concepts without personality influence. The combination enables AI agents with long-term memory that can both retrieve information accurately and reason consistently with stable character traits.

---

# Part I: Recall - TEMPR (Temporal Entity Memory Priming Retrieval)

## 1. Introduction to Recall

Conversational AI agents face a fundamental challenge: maintaining coherent, context-aware memories across extended interactions. Traditional search systems are optimized for human users with top-k ranking and relevance feedback, but AI agents have fundamentally different requirements: they need to retrieve variable amounts of information based on reasoning complexity while respecting LLM context windows. Existing approaches rely either on vector similarity search, which captures semantic relationships but misses entity-level connections, or on keyword matching, which provides precision but lacks conceptual understanding. Neither approach adequately handles the temporal aspects of memory or entity-based reasoning that enable multi-hop information discovery.

We propose TEMPR, a memory retrieval architecture designed specifically for AI agents that combines established information retrieval techniques—semantic vector search, BM25 keyword matching, spreading activation graph traversal (Anderson 1983), and neural reranking—into a unified system optimized for agent workflows. The key architectural choices are:

1. **Agent-Optimized Interface**: budget and max_tokens parameters instead of traditional top-k ranking
2. **Comprehensive Narrative Fact Extraction with Temporal Ranges**: LLM-powered extraction that creates self-contained narrative facts preserving full conversational context, extracting temporal ranges (occurred_start/end) to distinguish point events from periods
3. **Entity-Aware Graph Structure with Multiple Link Types**: LLM-based entity resolution and linking that connects memories through shared identities, along with temporal, semantic, and causal link types
4. **Four-Way Parallel Retrieval**: Semantic, keyword, graph-based (spreading activation), and temporal range retrieval strategies executed in parallel and fused using RRF (Cormack et al. 2009)
5. **Neural Cross-Encoder Reranking**: Learned query-document relevance with temporal awareness and token budget filtering

This combination of techniques enables agents to discover indirectly related information through graph traversal while maintaining temporal awareness, achieving strong performance on multi-hop reasoning tasks.

### 1.1 Contributions

Our key contributions for the recall system are:

1. **Agent-Optimized Retrieval Interface**: Unlike traditional top-k search optimized for human users, we introduce budget and max_tokens parameters that allow AI agents to dynamically trade off latency for recall based on reasoning complexity and context window constraints

2. **Four-Way Parallel Retrieval**: We combine semantic vector search, BM25 keyword matching, graph-based spreading activation (Anderson 1983), and temporal-aware graph traversal into a unified parallel retrieval pipeline using Reciprocal Rank Fusion (Cormack et al. 2009) and neural cross-encoder reranking. The graph traversal incorporates multiple link types (entity, semantic, temporal, causal) with configurable weighting during activation spreading.

3. **LLM-Based Knowledge Graph Construction with Temporal Ranges**: We leverage open-source LLMs for comprehensive narrative fact extraction, entity recognition, and entity disambiguation. The system extracts temporal ranges (occurred_start, occurred_end) to represent both point events and extended periods, distinguishing when facts occurred from when they were mentioned.

4. **Strong Performance on Multi-Hop Reasoning**: 73.50% on LoComo and 80.60% on LongMemEval, with particularly strong performance on multi-hop queries (+15.8% over Mem0), demonstrating the effectiveness of combining these techniques for discovering indirectly related information in conversational contexts

## 2. Memory Organization

### 2.1 Four Memory Networks

TEMPR organizes memories into four distinct networks for epistemic clarity:

**World Network** (fact_type='world'): Objective information about the world
- Example: "Alice works at Google in Mountain View on the AI team"
- Stores facts received from external sources
- No confidence scores (facts are information received, not beliefs)

**Bank Network** (fact_type='bank'): Biographical information about the agent itself
- Example: "I recommended Yosemite National Park to Alice for hiking"
- Stores the agent's own actions and experiences
- Uses first-person perspective ("I recommended..." not "The agent recommended...")

**Opinion Network** (fact_type='opinion'): Subjective beliefs formed by the agent
- Example: "Python is better for data science because of libraries like pandas (confidence: 0.85)"
- Stores judgments and opinions with confidence scores
- Evolved through opinion reinforcement when new evidence arrives
- Influenced by personality traits (see Part II: Reflect)

**Observation Network** (fact_type='observation'): Synthesized entity summaries
- Example: "Alice is a software engineer at Google specializing in machine learning"
- Objective syntheses from multiple facts about an entity
- Generated WITHOUT personality influence (unlike opinions)
- Automatically created and updated in background processes
- Provides structured "mental models" of entities

This separation provides:
- **Epistemic Clarity**: Facts represent information encountered; opinions represent personality-driven judgments; observations represent objective syntheses
- **Traceability**: Opinion reinforcement traces facts; observations trace entity-related facts
- **Debugging**: Developers can separately inspect factual knowledge, formed beliefs, and entity models
- **Confidence Semantics**: Facts and observations lack confidence scores; opinions have confidence scores representing conviction strength
- **Personality Independence**: Observations remain objective while opinions reflect personality

### 2.2 Memory Unit Structure

Each memory is represented as a self-contained node with:

- id: Unique UUID
- bank_id: Identifier for the memory bank this memory belongs to
- text: Self-contained comprehensive narrative fact
- embedding: 384-dimensional vector (BAAI/bge-small-en-v1.5)
- event_date: Timestamp when the fact became true (maintained for backward compatibility)
- occurred_start: Timestamp when the fact/event started (temporal range support)
- occurred_end: Timestamp when the fact/event ended (temporal range support)
- mentioned_at: Timestamp when the fact was mentioned/learned
- context: Optional contextual metadata
- fact_type: One of 'world', 'bank', 'opinion'
- confidence_score: For opinions only, strength of conviction (0.0-1.0)
- access_count: Frequency-based importance signal
- search_vector: Full-text search tsvector for BM25 ranking

### 2.3 LLM-Powered Comprehensive Narrative Fact Extraction

TEMPR employs **LLM-powered comprehensive narrative fact extraction** using open-source models. This approach provides more context-aware extraction compared to traditional rule-based NLP pipelines, though at higher computational cost.

#### 2.3.1 Extraction Principles

**Chunking Strategy**: TEMPR uses a coarse-grained chunking approach, extracting 2-5 comprehensive facts per conversation rather than dozens of atomic fragments. This is a deliberate tradeoff: larger chunks preserve more context and narrative flow, at the cost of reduced precision when only a small portion of the chunk is relevant.

Each fact should:
1. **Capture entire conversations or exchanges** - Include the full back-and-forth discussion
2. **Be narrative and comprehensive** - Tell the complete story with all context
3. **Be self-contained** - Readable without the original text
4. **Include all participants** - WHO said/did WHAT, with their reasoning
5. **Preserve the flow** - Keep related exchanges together in one fact

**Example Comparison**:

❌ **Fragmented Approach** (traditional):
- "Bob suggested Summer Vibes"
- "Alice wanted something unique"
- "They considered Sunset Sessions"
- "Alice likes Beach Beats"
- "They chose Beach Beats"

✅ **Comprehensive Approach** (TEMPR):
- "Alice and Bob discussed naming their summer party playlist. Bob suggested 'Summer Vibes' because it's catchy and seasonal, but Alice wanted something more unique. Bob then proposed 'Sunset Sessions' and 'Beach Beats', with Alice favoring 'Beach Beats' for its playful and fun tone. They ultimately decided on 'Beach Beats' as the final name."

#### 2.3.2 Open-Source LLM Extraction Pipeline

The extraction process leverages open-source LLMs with structured output (Pydantic schemas). This follows the established practice of using LLMs for information extraction, which has been shown to improve context understanding compared to rule-based NLP pipelines, particularly for:
- Coreference resolution in conversational text
- Domain-specific entity recognition
- Maintaining narrative coherence across multi-turn exchanges

**LLM Extraction Steps**:
1. **Pronoun Resolution**: "She loves hiking" → "Alice loves hiking"
2. **Temporal Normalization**: "last year" → "in 2023" (absolute dates)
3. **Temporal Range Extraction**: Identify when facts occurred vs. when mentioned
   - Point events: "on July 14" → occurred_start = occurred_end = 2023-07-14
   - Period events: "in February 2023" → occurred_start = 2023-02-01, occurred_end = 2023-02-28
   - Vague periods: "lately" → estimated range based on context
   - mentioned_at = conversation date (when fact was learned)
4. **Participant Attribution**: Preserve WHO said/did WHAT
5. **Reasoning Preservation**: Include WHY decisions were made
6. **Fact Type Classification**: Determine fact categories (world, bank, opinion)
7. **Entity Extraction**: Identify all entities (PERSON, ORG, LOCATION, PRODUCT, CONCEPT)

**Temporal Augmentation**: Before embedding, facts are augmented with readable temporal information:
- Original: "Alice started working at Google"
- Augmented for embedding: "Alice started working at Google (happened in November 2023)"

This augmentation helps semantic search understand temporal relevance without modifying the stored fact text.

### 2.4 Entity Resolution and Linking

Entity resolution creates strong connections between memories that share common entities, solving the problem where semantically dissimilar facts are related through shared identities.

#### 2.4.1 LLM-Based Entity Recognition

TEMPR uses the same open-source LLM that performs fact extraction to also identify and extract entities during the narrative fact creation process. This unified approach eliminates the brittleness of traditional NER pipelines that struggle with domain-specific entities, novel names, and context-dependent disambiguation.

**Entity Types**:
- PERSON: "Alice", "Bob Chen"
- ORGANIZATION: "Google", "Stanford University"
- LOCATION: "Yosemite National Park", "California"
- PRODUCT: "Python", "pandas library"
- CONCEPT: "machine learning", "remote work"
- OTHER: Miscellaneous proper nouns

#### 2.4.2 LLM-Based Entity Disambiguation

Multiple mentions of entities (e.g., "Alice", "Alice Chen", "Alice C.") must be resolved to a single canonical entity. TEMPR uses the LLM to perform entity disambiguation, analyzing the surrounding context to determine if two entity mentions refer to the same entity. This handles complex cases like:
- Nicknames and formal names ("Bob" vs. "Robert Chen")
- Partial mentions ("Alice" vs. "Alice Chen")
- Context-dependent disambiguation ("Apple the company" vs. "apple the fruit")

The LLM considers multiple signals:
- **Name Similarity**: String similarity using Levenshtein distance
- **Co-occurrence Patterns**: Entities mentioned together frequently are likely distinct
- **Temporal Proximity**: Recent mentions are more likely to refer to the same entity

#### 2.4.3 Entity Link Structure

Each entity creates a link_type='entity' edge between all memories mentioning it:

**Properties**:
- weight=1.0 (constant, no temporal decay)
- entity_id: Reference to resolved canonical entity
- Bidirectional connections between all mentioning memories

**Impact on Retrieval**: Entity links enable graph traversal to discover indirectly related facts:

**Example Query**: "What does Alice do?"
1. **Semantic Match**: "Alice works at Google in Mountain View..." (direct match)
2. **Entity Traversal**: Follow entity links for "Alice" →
   - "Alice loves hiking in Yosemite..." (different semantic space)
   - "I recommended technical books to Alice" (Bank Network, via "Alice")
3. **Chained Traversal**: Follow "Google" entity →
   - "Google's office in Mountain View has excellent amenities"

### 2.5 Link Types and Graph Structure

The memory graph contains four types of edges connecting memory units:

#### 2.5.1 Temporal Links

Temporal links connect memories close in time, enabling temporal reasoning:

**Creation Logic**:

**Properties**:
- Decays linearly with time distance
- Minimum weight 0.3 to maintain some connectivity
- Enables "What happened around the same time?" queries

#### 2.5.2 Semantic Links

Semantic links connect memories with similar meanings:

**Creation Logic**:

**Properties**:
- Uses pgvector HNSW index for efficient nearest-neighbor search
- Higher threshold (0.7) than retrieval (0.3) to avoid over-connection
- Weight equals cosine similarity score

#### 2.5.3 Entity Links

Entity links (described in Section 2.4.3) create the strongest connections:

**Properties**:
- weight=1.0 (constant, never decays)
- Connects all memories mentioning the same resolved entity
- Most reliable traversal path during graph search

#### 2.5.4 Causal Links

Causal links represent identified cause-effect relationships between facts. During fact extraction, the LLM attempts to identify causal relationships between facts extracted from the same conversation. These links are incorporated as one component of the graph retrieval system.

**Causal Relationship Types**:
- causes: This fact directly causes the target fact
- caused_by: This fact was caused by the target fact (inverse of causes)
- enables: This fact enables or allows the target fact to happen
- prevents: This fact prevents or blocks the target fact

**Properties**:
- weight: Strength of causal relationship ∈ [0.0, 1.0] (default 1.0)
- Directional edges (from cause to effect)
- Prioritized during graph traversal with 2x activation boost

**Role in Retrieval**: Causal links provide an additional signal during graph-based retrieval. When present, they allow the system to traverse explanatory relationships in addition to semantic, temporal, and entity-based connections.

**Example**: For a query "Why does Alice spend time in the garden?", the system may find both direct semantic matches ("Alice spends time in the garden to find comfort") and traverse causal links to related facts ("Alice lost her friend Karlie in February 2023").

**Graph Density**: Each memory unit typically has:
- 5-10 temporal links (to nearby memories)
- 3-5 semantic links (to similar content)
- Variable entity links (depending on entity mention frequency)
- 0-3 causal links (when causal relationships are identified)

### 2.6 The Observation Paradigm

A critical challenge in long-term memory systems is maintaining structured, high-level understanding of entities (people, organizations, places, concepts) without re-reading all individual facts each time. Traditional approaches either retrieve all entity-related facts (expensive, noisy) or maintain no entity-level state (losing structured understanding). Hindsight introduces **observations**—automatically synthesized entity summaries that provide structured "mental models" without personality influence.

#### 2.6.1 Motivation and Design

**The Problem**: When a system accumulates dozens of facts about an entity like "Alice," queries about Alice must either:
1. Retrieve all 50+ individual facts (expensive, overwhelming)
2. Rely only on top-k semantic matches (may miss key attributes)
3. Manually maintain entity profiles (doesn't scale, requires human curation)

**The Solution**: Observations provide a fourth fact type that synthesizes multiple facts into coherent, objective entity summaries, automatically maintained as new information arrives.

**Key Properties**:
- **Objective Synthesis**: Generated WITHOUT personality influence (unlike opinions)
- **Entity-Scoped**: Each observation is about a single entity
- **Automatic Maintenance**: Generated in background after fact ingestion
- **Multi-Fact Fusion**: Combines information scattered across multiple facts
- **Response Augmentation**: NOT used for retrieval/search, but returned alongside results when include_entities=True to provide entity context

#### 2.6.2 Observation Generation

Observations are generated through an LLM-powered synthesis process:

**Trigger**: When new facts mentioning an entity are ingested via retain(), a background task is queued to regenerate observations for that entity.

**Process**:

**LLM Prompt Structure**:

**Example Transformation**:

**Input Facts**:
- "Alice works at Google"
- "Alice is a software engineer"
- "Alice specializes in ML and deep learning"
- "Alice joined Google in 2023"
- "Alice is detail-oriented and methodical"

**Generated Observations**:
- "Alice is a software engineer at Google specializing in machine learning and deep learning"
- "Alice joined Google in 2023"
- "Alice is detail-oriented and methodical in her approach"

#### 2.6.3 Storage and Retrieval

**Storage**: Observations are stored as regular memory_units with fact_type='observation':


**Entity Links**: Observations are linked to their entity via the entity_links table, enabling efficient lookup of all observations for an entity.

**Important**: Observations are NOT used during the retrieval/search process itself. They do not participate in the 4-way parallel search (semantic, keyword, graph, temporal). Instead, they are **response augmentations**—additional context returned alongside search results.

**Response Augmentation**: When calling recall() with include_entities=True:


**Response Structure**:

#### 2.6.4 Observations vs. Opinions

A critical distinction separates observations from opinions:

| Dimension | Observations | Opinions |
|-----------|-------------|----------|
| **Influence** | No personality influence | Influenced by Big Five traits |
| **Purpose** | Objective entity summaries | Subjective beliefs and judgments |
| **Confidence** | No confidence score | Confidence score (0.0-1.0) |
| **Generation** | Background synthesis from facts | Formed during reflect() reasoning |
| **Update Mechanism** | Regenerated when entity facts change | Updated via opinion reinforcement |
| **Example** | "Alice is a software engineer at Google" | "Alice is an excellent engineer" |

**Why Both?**: Observations provide factual entity understanding for retrieval contexts, while opinions represent the memory bank's personality-driven beliefs for reasoning contexts. A memory bank can have objective observations about Alice (she works at Google, specializes in ML) AND personality-influenced opinions about Alice (she's a talented engineer, she'd be great for project X).

#### 2.6.5 Background Processing

Observation generation is asynchronous to avoid blocking retain() operations:

**Flow**:

This design ensures low-latency writes while maintaining fresh entity summaries.

#### 2.6.6 Benefits and Use Cases

**Benefits**:

1. **Contextual Entity Summaries**: After retrieving facts that mention entities, observations provide synthesized context about those entities without requiring separate queries
2. **Structured Entity Understanding**: Provides coherent mental models of entities as response augmentation
3. **Token Efficiency**: 3-5 observations provide more structured context than retrieving all entity-related facts
4. **Objective Grounding**: When reflecting with personality, observations provide objective entity context
5. **Scalability**: Automatically maintained as facts accumulate, always fresh when needed
6. **Separation of Concerns**: Search focuses on relevant facts through semantic similarity, keyword matching, and graph traversal; observations provide entity context post-retrieval

**Note on Observation Stability**: While observations are regenerated when entity facts change, the core retrieval mechanism remains grounded in the original facts. The four-way parallel search (semantic, keyword, graph, temporal) retrieves facts based on query relevance, semantic co-occurrence, and entity relationships—not based on observations. This ensures that the most relevant factual information is surfaced regardless of how observations may evolve over time.

**Use Cases**:

**Multi-Agent Conversations**: When retrieving facts that mention people, observations provide shared, objective entity context:

**Entity-Centric Queries**: "Tell me about Alice" retrieves facts about Alice, and observations provide synthesized entity summary in the response.

**Contextual Reasoning**: When forming opinions during reflect(), observations provide factual entity grounding alongside retrieved facts.

**Knowledge Graph Interfaces**: Observations can be exposed as structured entity profiles in UIs or APIs via dedicated entity endpoints.

## 3. Retrieval Architecture

Our retrieval pipeline addresses the fundamental challenge of long-term memory: achieving both **high recall** (finding all relevant information) and **high precision** (ranking the most relevant items first).

### 3.1 Four-Way Parallel Retrieval

We execute four complementary retrieval strategies in parallel, each capturing different aspects of relevance:

#### 3.1.1 Semantic Retrieval (Vector Similarity)

**Method**: Cosine similarity between query embedding and memory embeddings
**Index**: pgvector HNSW (Hierarchical Navigable Small World)
**Threshold**: ≥ 0.3 similarity

**Implementation**:

**Advantages**:
- Captures conceptual similarity
- Handles synonyms and paraphrasing
- Language-model understanding of meaning

**Limitations**:
- Misses exact proper nouns if not in training data
- Cannot reason about temporal relationships
- Weak at entity disambiguation

#### 3.1.2 Keyword Retrieval (BM25 Full-Text Search)

**Method**: PostgreSQL full-text search with BM25 ranking (ts_rank_cd)
**Index**: GIN index on to_tsvector('english', text)

**Advantages**:
- High precision for proper nouns and technical terms
- Exact phrase matching
- Fast execution with GIN index

**Limitations**:
- No semantic understanding
- Requires exact or stemmed matches

**Complementarity**: Semantic + Keyword achieves >90% recall: vector search catches concepts, BM25 catches exact names.

#### 3.1.3 Graph Retrieval (Spreading Activation)

**Method**: Activation spreading from semantic entry points through the memory graph, following the spreading activation model of memory (Anderson 1983).

**Algorithm**:

**Decay Mechanism**: Activation decays by 0.8 per hop, limiting spread to ~4-5 hops.

**Link Weighting with Causal Boosting**:
- **Causal links**: Base weight × 2.0 boost (causes/caused_by) or × 1.5 boost (enables/prevents)
- **Entity links**: weight 1.0 (no boost, already strong signal)
- **Semantic links**: weight ∈ [0.7, 1.0] (cosine similarity, no boost)
- **Temporal links**: weight ∈ [0.3, 1.0] (time-based decay, no boost)

**Advantages**:
- Discovers indirectly related facts through graph connectivity
- Leverages entity links to traverse knowledge graph
- Finds context-adjacent memories via temporal links
- Prioritizes explanatory relationships through causal boosting

#### 3.1.4 Temporal Graph Retrieval (Time-Constrained + Spreading)

**Activation Condition**: Only triggered when temporal constraint detected in query

**Temporal Parsing**: Uses google/flan-t5-small (80M parameters) to extract temporal constraints from natural language queries:
- "last spring" → 2024-03-01 to 2024-05-31
- "in June" → 2024-06-01 to 2024-06-30
- "last year" → 2024-01-01 to 2024-12-31
- "between March and May" → 2025-03-01 to 2025-05-31

**Temporal Range Matching**: Facts are matched against time constraints using their temporal range (occurred_start, occurred_end):


**Algorithm**:

### 3.2 Reciprocal Rank Fusion (RRF)

After parallel retrieval, we merge 3-4 ranked lists using Reciprocal Rank Fusion (Cormack et al. 2009):

**Algorithm**:

**Advantages over Score-Based Fusion**:
- **Rank-based**: Position matters more than absolute scores
- **Robust to missing items**: Missing from a list contributes 0, not a penalty
- **Multi-evidence weighting**: Items appearing in multiple lists rank higher

### 3.3 Neural Cross-Encoder Reranking

After RRF fusion, TEMPR applies neural cross-encoder reranking to refine precision:

**Model**: cross-encoder/ms-marco-MiniLM-L-6-v2 (pretrained on MS MARCO passage ranking)

**Algorithm**:

**Advantages**:
- Learns query-document relevance patterns from supervised data
- Considers full query-document interaction
- Temporal awareness through formatted date context

### 3.4 Token Budget Filtering

Final stage applies token budget filtering to limit context window usage:

**Algorithm**:

**Purpose**: Ensures retrieved facts fit within LLM context windows while maximizing information density.

### 3.5 Complete Retrieval Pipeline

**End-to-End Flow**:

## 4. Evaluation

We evaluate TEMPR on two established long-term memory benchmarks: LoComo (Long-term Conversation Memory) and LongMemEval.

### 4.1 LoComo Benchmark

LoComo evaluates conversational memory systems across four dimensions: single-hop queries, multi-hop queries, open-domain queries, and temporal queries.

**Results**:

| Method | Single Hop J ↑ | Multi-Hop J ↑ | Open Domain J ↑ | Temporal J ↑ | Overall |
|--------|---------------|---------------|-----------------|--------------|---------|
| A-Mem* | 39.79 | 18.85 | 54.05 | 31.08 | 48.38 |
| LangMem | 62.23 | 47.92 | 71.12 | 23.43 | 58.10 |
| Zep (Mem0 paper) | 61.70 | 41.35 | 76.60 | 49.31 | 65.99 |
| OpenAI | 63.79 | 42.92 | 62.29 | 21.71 | 52.90 |
| Mem0 | 67.13 | 51.15 | 72.93 | 55.51 | 66.88 |
| Mem0 w/ Graph | 65.71 | 47.19 | 75.71 | 58.13 | 68.44 |
| **TEMPR** | **73.20** | **66.90** | **78.60** | **56.30** | **73.50** |

**Analysis**: TEMPR achieves strong performance across all query types:
- **Single-Hop (+6.1% vs Mem0)**: Superior performance due to comprehensive narrative facts and BM25 keyword matching
- **Multi-Hop (+15.8% vs Mem0)**: Largest improvement, demonstrating effectiveness of graph-based spreading activation
- **Open Domain (+2.9% vs Mem0)**: Strong performance through multi-strategy parallel retrieval
- **Temporal (-1.8% vs Mem0 w/ Graph)**: Competitive temporal reasoning

### 4.2 LongMemEval Benchmark

LongMemEval assesses memory systems across six dimensions:

**Results**:

| Method | Single-Session Preference | Single-Session Assistant | Temporal Reasoning | Multi-Session | Knowledge Update | Single-Session User | Overall |
|--------|--------------------------|-------------------------|-------------------|---------------|-----------------|-------------------|---------|
| Zep gpt-4o-mini | 53.30% | 75.00% | 54.10% | 47.40% | 74.40% | 92.90% | 63.80% |
| Zep gpt-4o | 56.70% | 80.40% | 62.40% | 57.90% | 83.30% | 92.90% | 71.00% |
| **TEMPR** | **83.30%** | **80.40%** | **75.90%** | **75.20%** | **85.90%** | **92.90%** | **80.60%** |
| Mastra gpt-4o | 46.70% | 100.00% | 75.20% | 76.70% | 84.60% | 97.10% | 80.05% |

**Analysis**: TEMPR achieves competitive performance:
- **Single-Session Preference (+26.6% vs Zep gpt-4o)**: Dramatic improvement enabled by comprehensive narrative facts
- **Temporal Reasoning (+13.5% vs Zep gpt-4o)**: Strong performance through dedicated temporal graph retrieval
- **Multi-Session (+17.3% vs Zep gpt-4o)**: Entity-aware graph linking maintains consistency

The 80.60% overall score represents a 9.6 percentage point improvement over Zep gpt-4o (71.00%).

---

# Part II: Reflect - CARA (Coherent Adaptive Reasoning Agents)

## 5. Introduction to Reflect

Conversational AI agents increasingly need to maintain consistent perspectives and form judgments that reflect stable character traits. Current systems either provide purely objective information retrieval without perspective, or generate responses that lack consistency across interactions. Human conversation partners expect agents to have stable viewpoints, preferences, and reasoning styles—characteristics that emerge from personality.

We propose CARA (Coherent Adaptive Reasoning Agents), a personality framework that addresses these limitations through:

1. **Big Five Personality Integration**: Configurable traits (OCEAN model) that influence how agents interpret facts and form opinions
2. **TEMPR Memory Integration**: Leverages TEMPR's three-network architecture (world facts, bank experiences, opinions) for sophisticated memory access
3. **Opinion Reinforcement**: Dynamic belief updating when new evidence reinforces, weakens, or contradicts existing opinions
4. **Personality Bias Control**: Adjustable influence strength allowing agents to range from objective to strongly personality-driven
5. **Background Merging**: LLM-powered integration of biographical information with intelligent conflict resolution

This architecture enables agents to maintain consistent identities while allowing beliefs to evolve naturally with new information.

### 5.1 Motivation

Consider an agent discussing remote work. With high openness (0.9) and low conscientiousness (0.2), the agent might form the opinion: "Remote work enables creative flexibility and spontaneous innovation." The same facts presented to an agent with low openness (0.2) and high conscientiousness (0.9) might yield: "Remote work lacks the structure and accountability needed for consistent performance."

Both agents access identical factual information, but personality traits bias how they weight different aspects (flexibility vs. structure) and what conclusions they draw. This mirrors human reasoning—our personalities influence what we attend to and how we integrate information into our worldview.

### 5.2 Contributions

Our key contributions for the reflect system are:

1. **Personality-Aware Reasoning**: A prompt engineering framework that injects Big Five traits into LLM reasoning, demonstrating how personality consistently biases opinion formation

2. **TEMPR-Based Three-Network Architecture**: Integration with TEMPR to manage three distinct networks (world facts, bank experiences, opinions), enabling architectural separation between objective information and subjective beliefs with epistemic clarity and traceability

3. **Opinion Reinforcement Mechanism**: An automatic belief update system that adjusts confidence scores when new evidence arrives, creating dynamic belief systems that evolve with information

4. **Background Merging with Conflict Resolution**: An LLM-powered method for maintaining coherent agent identities when new biographical information contradicts existing background

5. **Bias Strength Control**: A meta-parameter that allows tuning personality influence from objective (0.0) to strongly subjective (1.0), enabling task-appropriate personality expression

## 6. Personality Model

### 6.1 Big Five Framework

We adopt the **Big Five** personality model (OCEAN), which is empirically validated across cultures and provides continuous trait dimensions:

**Trait Dimensions** (each 0.0-1.0):

1. **Openness (O)**: Receptiveness to new ideas, creativity, abstract thinking
   - High: "I embrace novel approaches", "innovation over tradition"
   - Low: "I prefer proven methods", "tradition over experimentation"

2. **Conscientiousness (C)**: Organization, goal-directed behavior, dependability
   - High: "I plan systematically", "evidence-based decisions"
   - Low: "I work flexibly", "intuition-based decisions"

3. **Extraversion (E)**: Sociability, assertiveness, energy from interaction
   - High: "I seek collaboration", "enthusiastic communication"
   - Low: "I prefer solitude", "measured communication"

4. **Agreeableness (A)**: Cooperation, empathy, conflict avoidance
   - High: "I seek consensus", "consider social harmony"
   - Low: "I express dissent", "prioritize accuracy over harmony"

5. **Neuroticism (N)**: Emotional sensitivity, anxiety, stress response
   - High: "I consider risks carefully", "emotionally engaged"
   - Low: "I remain calm under uncertainty", "emotionally detached"

**Bias Strength** (0.0-1.0): Meta-parameter controlling how much personality influences opinions
- 0.0: Neutral, fact-based reasoning (no personality bias)
- 0.5: Moderate personality influence, balanced with objective analysis
- 1.0: Strong personality influence, facts filtered through trait lens

### 6.2 Psychological Basis

The Big Five model has several advantages for AI agents:

1. **Empirical Validation**: Decades of psychological research demonstrate cross-cultural stability and predictive validity
2. **Continuous Dimensions**: Unlike categorical types, continuous scales allow fine-grained personality tuning
3. **Behavioral Prediction**: Traits predict information processing styles, decision-making approaches, and communication preferences
4. **Interpretability**: Well-understood trait meanings enable users to anticipate agent behavior

**Trait Influence on Reasoning**:
- **High Openness**: Favors novel solutions, abstract thinking, considers unconventional perspectives
- **High Conscientiousness**: Emphasizes systematic analysis, evidence quality, long-term consequences
- **High Extraversion**: Considers social aspects, collaborative solutions, enthusiastic expression
- **High Agreeableness**: Weights harmony, considers multiple viewpoints, seeks consensus
- **High Neuroticism**: Attends to risks, emotional implications, uncertainty

## 7. Bank Profile Structure

### 7.1 Profile Schema

Each memory bank has an associated profile containing identity information:


**Name Field**: Memory bank's name used in prompts and self-reference ("Your name: Marcus")

**Personality Field**: JSONB containing six continuous values (five traits + bias strength)

**Background Field**: First-person narrative describing the agent's biographical context:
- "I am a software engineer with 10 years of startup experience"
- "I was born in Texas and value innovation over tradition"
- "I am a creative artist interested in digital media"

### 7.2 Trait Description Generation

Personality traits are translated into natural language descriptions for LLM prompts:


**Example Output** (openness=0.9, conscientiousness=0.2, extraversion=0.7, agreeableness=0.3, neuroticism=0.5):

This verbalization makes traits interpretable to the LLM, enabling personality-biased reasoning.

## 8. Opinion Network and Opinion Formation

### 8.1 Opinion Structure

Opinions are stored as memory units in the dedicated opinion network (fact_type='opinion'):

**Core Attributes**:
- text: The opinion statement with explicit reasoning
- confidence_score: Opinion strength and resistance to change (0.0-1.0)
- event_date: When the opinion was formed
- bank_id: Which memory bank holds this opinion
- entities: Mentioned entities (for reinforcement triggering)

**Example Opinion**:

**Fact vs. Opinion Separation**:

A critical architectural distinction separates **facts** (objective information stored in world/bank networks) from **opinions** (subjective beliefs stored in the opinion network). This separation provides:

1. **Epistemic Clarity**: Facts represent information encountered; opinions represent judgments formed
2. **Traceability**: Opinion reinforcement can trace which facts influenced belief updates
3. **Debugging**: Developers can separately inspect factual knowledge vs. formed beliefs
4. **Confidence Semantics**: Facts lack confidence scores; opinions have confidence scores

### 8.2 Opinion Formation

Opinions are generated during "reflect" operations—when the agent is asked to reason about a topic and form a judgment.

**Formation Process**:
1. Retrieve relevant facts from all memory networks (world, bank, existing opinions) using TEMPR
2. Inject bank profile (name, personality, background) into LLM prompt
3. Generate reasoning with personality bias applied
4. Extract new opinions from response using structured output
5. Store opinions with confidence scores in opinion network

**Prompt Structure** (bias_strength=0.8):

### 8.3 System Message Adaptation

The system message adjusts based on bias strength to control personality influence:

**High bias (≥0.7)**:

**Moderate bias (0.4-0.7)**:

**Low bias (<0.4)**:

### 8.4 Confidence Score Semantics

Confidence scores represent opinion strength—how firmly the agent holds the belief:

- **0.9-1.0**: Very strong conviction, deeply held belief
- **0.7-0.9**: Strong conviction, firmly held opinion
- **0.5-0.7**: Moderate conviction, open to revision
- **0.3-0.5**: Weak conviction, easily influenced
- **0.0-0.3**: Very weak conviction, highly malleable

**LLM Generation**: Confidence scores are extracted using structured output (Pydantic schema):


## 9. Opinion Reinforcement

### 9.1 Motivation

Human beliefs evolve as we encounter new information. Supporting evidence strengthens beliefs, contradictory evidence weakens them, and sufficient contradiction causes belief revision. Opinion reinforcement implements this dynamic belief updating.

### 9.2 Reinforcement Mechanism

When new facts are ingested (via retain), the system:

1. **Identify Related Opinions**: Find existing opinions that mention entities in the new facts
2. **Evaluate Evidence Relationship**: Use LLM to determine if new facts:
   - **Reinforce**: Support the existing opinion (increase confidence)
   - **Weaken**: Contradict the existing opinion (decrease confidence)
   - **Contradict**: Strongly contradict, requiring opinion revision
   - **Neutral**: Unrelated or no clear relationship
3. **Update Opinions**: Adjust confidence scores or revise opinion text based on evaluation

**Example Reinforcement**:

**Existing Opinion** (confidence: 0.7):

**New Fact**:

**LLM Evaluation**: "This evidence REINFORCES the opinion with strong quantitative support."

**Updated Opinion** (confidence: 0.85):

### 9.3 Reinforcement Algorithm


### 9.4 Reinforcement Guarantees

**Consistency**: Opinions are only updated when new facts genuinely relate to existing beliefs

**Personality Coherence**: Reinforcement evaluation incorporates bank personality, ensuring updates align with trait-driven reasoning

**Transparency**: Each update records the triggering facts and reasoning, providing an audit trail

**Bounded Updates**: Confidence changes are bounded (±0.1-0.15 per update) to prevent extreme swings

## 10. Background Merging

### 10.1 Challenge

Memory bank backgrounds accumulate biographical information over time. New information may:
- **Complement**: Add new facts without contradiction
- **Conflict**: Contradict existing facts ("born in Texas" vs. "born in Colorado")
- **Refine**: Provide more specific versions of existing facts

Naive concatenation creates incoherent backgrounds with contradictions. We need intelligent merging.

### 10.2 LLM-Powered Merging

We use an LLM to merge backgrounds with conflict resolution:

**Merge Rules**:
1. **New overwrites old** when contradictory
2. **Add non-conflicting** information
3. **Maintain first-person** perspective ("I..." not "You...")
4. **Keep concise** (under 500 characters)

**Prompt Template**:

**Example Merges**:

**Conflict Resolution**:
- Current: "I was born in Colorado"
- New: "You were born in Texas"
- Result: "I was born in Texas"

**Addition**:
- Current: "I was born in Texas"
- New: "I have 10 years of startup experience"
- Result: "I was born in Texas. I have 10 years of startup experience."

### 10.3 First-Person Normalization

Users may provide background in second person ("You are..."), but internal storage maintains first person for consistency in prompts.

**Normalization**: LLM automatically converts:
- "You are a creative engineer" → "I am a creative engineer"
- "You were born in 1990" → "I was born in 1990"
- "You value innovation" → "I value innovation"

## 11. Personality-Driven Reasoning Examples

### 11.1 Example: Remote Work Discussion

**Scenario**: Two memory banks with opposite personalities discuss remote work given identical facts.

**Facts** (both banks receive):
- "Remote work eliminates commute time (average 1 hour/day saved)"
- "Office work provides spontaneous collaboration and mentorship"
- "Studies show 65% of remote workers report higher productivity"
- "Some managers report difficulty monitoring remote employee performance"

**Bank A** (High Openness=0.9, Low Conscientiousness=0.2, bias=0.8):

**Bank B** (Low Openness=0.2, High Conscientiousness=0.9, bias=0.8):

**Analysis**: Both banks accessed identical facts but formed opposite conclusions based on personality:
- Bank A (high openness) weighted autonomy, flexibility, innovation
- Bank B (high conscientiousness) weighted structure, monitoring, discipline

### 11.2 Example: Opinion Evolution

**Scenario**: Bank forms initial opinion, then encounters reinforcing and contradictory evidence.

**Initial State** (t=0):

**Reinforcement** (t=1):
- New Fact: "Python dominates AI/ML with 75% market share; TensorFlow and PyTorch are Python-first"
- Update: Confidence → 0.85, text adds "Python's dominance in AI/ML frameworks..."

**Partial Contradiction** (t=2):
- New Fact: "Julia offers 10x faster numerical computation; increasingly adopted in research"
- Update: Confidence → 0.75, text revised to include nuance about specialized languages

**Strong Contradiction** (t=3):
- New Fact: "Major tech companies migrating data pipelines to Rust for performance"
- Update: Confidence → 0.55, text revised to acknowledge Python's shifting role

**Trajectory**: The opinion evolved from strong conviction (0.7 → 0.85) to weaker, more malleable belief (0.55) as evidence accumulated.

## 12. Use Cases and Real-World Deployment

### 12.1 Multi-Persona Sports Commentary (Production Deployment)

**Application**: AI-generated sports analysis and entertainment content with multiple agent personalities

**Real-World System**: A production sports content platform where AI agents with distinct personalities co-host episodic shows discussing team performance, game analysis, and sports debates.

**System Architecture**:
- **Multiple Banks**: Each bank has unique personality traits and sports background
- **Continuous Memory**: Banks maintain persistent team/player assessments across episodes spanning months
- **Opinion Evolution**: As games occur and statistics accumulate, banks automatically update beliefs through reinforcement
- **Personality-Driven Commentary**: The same game results generate different perspectives based on bank traits

**Key Benefits Observed**:
1. **Viewer Engagement**: Improved audience retention with "personality diversity" as primary appeal
2. **Content Consistency**: Banks maintain recognizable voices across episodes without manual tuning
3. **Scalability**: New banks can be added with distinct personalities without retraining
4. **Opinion Richness**: Opinion networks capture nuanced, evolving assessments

This deployment validates that personality-driven opinion systems can operate at production scale for content generation requiring consistent yet adaptive perspectives.

### 12.2 Additional Use Cases

**Customer Support**: Multi-agent systems with specialized personas (empathetic, analytical, creative)

**Consistent Character AI**: Conversational AI characters for entertainment or education with stable personality

**Explainable AI**: Systems requiring transparent decision-making where personality traits explain reasoning style

---

# Part III: Unified Hindsight Architecture

## 13. Integration: TEMPR + CARA

The Hindsight system integrates TEMPR (recall) and CARA (reflect) into a unified architecture:

### 13.1 Three Core Operations

**1. Retain** (retain()): Store information into memory banks
- LLM-powered fact extraction with temporal ranges
- Entity recognition and resolution
- Graph link construction (temporal, semantic, entity, causal)
- Automatic opinion reinforcement for existing beliefs

**2. Recall** (recall()): Retrieve memories using multi-strategy search
- Four-way parallel retrieval (semantic, keyword, graph, temporal)
- Reciprocal Rank Fusion
- Neural cross-encoder reranking
- Token budget filtering

**3. Reflect** (reflect()): Generate personality-aware responses
- Retrieves relevant memories from all networks using TEMPR
- Loads bank personality and background
- Generates response influenced by Big Five traits
- Forms new opinions with confidence scores
- Stores opinions for future retrieval

### 13.2 Unified Data Flow


### 13.3 PostgreSQL Schema

The system uses PostgreSQL with pgvector for storage:


## 14. System Properties

### 14.1 Epistemic Clarity

The three-network architecture provides clear separation:
- **World**: What the bank knows about the world
- **Bank**: What the bank has done
- **Opinion**: What the bank believes

This enables:
- Transparent reasoning (trace opinions back to facts)
- Debugging (identify missing facts vs. flawed reasoning)
- Confidence calibration (opinions have confidence, facts don't)

### 14.2 Temporal Awareness

Multi-dimensional temporal representation:
- occurred_start / occurred_end: When events actually happened
- mentioned_at: When the bank learned about it
- event_date: Backward compatibility

Enables:
- Precise historical queries ("What happened in June?")
- Recency-aware ranking (newer mentions prioritized)
- Period matching (events spanning weeks or months)

### 14.3 Entity-Aware Reasoning

LLM-based entity resolution creates knowledge graph:
- Connects semantically distant facts through shared entities
- Enables multi-hop discovery ("Alice's manager's team")
- Disambiguates mentions ("Alice" vs. "Alice Chen")

### 14.4 Multiple Link Types

The graph incorporates multiple relationship types:
- Entity links connect memories mentioning the same entities
- Semantic links connect conceptually similar memories
- Temporal links connect temporally proximate memories
- Causal links represent identified cause-effect relationships
- Links are weighted differently during graph traversal

### 14.5 Personality Consistency

Big Five traits ensure stable reasoning style:
- Configurable bias strength (objective to subjective)
- Trait-appropriate opinion formation
- Consistent voice across interactions

### 14.6 Dynamic Belief Systems

Opinion reinforcement enables belief evolution:
- Confidence increases with supporting evidence
- Confidence decreases with contradictory evidence
- Opinion text revised when strongly contradicted
- Audit trail of belief changes

## 15. Conclusion

We present Hindsight, a unified memory architecture for AI agents that combines TEMPR's multi-strategy retrieval with CARA's personality-driven reasoning. The system achieves strong performance on established benchmarks (73.50% on LoComo, 80.60% on LongMemEval) while enabling personality-consistent opinion formation through the Big Five model.

The integration of four parallel search strategies (semantic, keyword, graph with multiple link types, temporal) with three-network architecture (world, bank, opinion) and opinion reinforcement creates a comprehensive memory system that:
- Retrieves information with high recall and precision
- Maintains epistemic clarity between facts and beliefs
- Enables personality-driven reasoning with stable traits
- Supports dynamic belief evolution with evidence

Real-world deployment in sports content generation demonstrates the system's ability to maintain consistent yet adaptive perspectives across extended interactions. Future work will explore personality evolution, multi-agent belief systems, and richer personality models incorporating values and cultural factors.

By combining temporal-aware retrieval with personality-driven reasoning, Hindsight moves toward conversational agents that exhibit not just memory and intelligence, but character—stable traits and evolving beliefs that enable more natural, trustworthy human-AI interaction.

## References

1. Anderson, J. R. (1983). A spreading activation theory of memory. *Journal of Verbal Learning and Verbal Behavior*, 22(3), 261-295.

2. Cormack, G. V., Clarke, C. L., & Buettcher, S. (2009). Reciprocal rank fusion outperforms condorcet and individual rank learning methods. In *SIGIR'09* (pp. 758-759).

3. McCrae, R. R., & Costa, P. T. (1997). Personality trait structure as a human universal. *American Psychologist*, 52(5), 509.

4. Goldberg, L. R. (1993). The structure of phenotypic personality traits. *American Psychologist*, 48(1), 26.

5. Malkov, Y. A., & Yashunin, D. A. (2018). Efficient and robust approximate nearest neighbor search using hierarchical navigable small world graphs. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 42(4), 824-836.

6. Robertson, S., & Zaragoza, H. (2009). The probabilistic relevance framework: BM25 and beyond. *Foundations and Trends in Information Retrieval*, 3(4), 333-489.

7. Brown, T. B., Mann, B., Ryder, N., Subbiah, M., Kaplan, J., Dhariwal, P., ... & Amodei, D. (2020). Language models are few-shot learners. *Advances in Neural Information Processing Systems*, 33, 1877-1901.

8. Petroni, F., Rocktäschel, T., Riedel, S., Lewis, P., Bakhtin, A., Wu, Y., & Miller, A. (2019). Language models as knowledge bases?. In *Proceedings of EMNLP-IJCNLP* (pp. 2463-2473).
