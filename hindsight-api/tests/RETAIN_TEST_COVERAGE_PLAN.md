# Retain Test Coverage Plan

## Current Test Coverage Analysis

### ✅ Currently Tested Features

1. **Basic Retention** (`test_retain.py`)
   - Storing content with chunks
   - Basic recall functionality

2. **Document Tracking** (`test_document_tracking.py`)
   - Document creation and retrieval
   - Document upsert (automatic replacement)
   - Document deletion with cascade
   - Memories without documents (backward compatibility)

3. **Batch Processing** (`test_batch_chunking.py`)
   - Auto-chunking for large batches (>500k chars)
   - Small batch processing without chunking

4. **Chunk and Entity Ordering** (`test_retain.py`)
   - Chunks follow fact relevance order
   - Entities follow fact relevance order
   - Token limit truncation behavior

5. **Temporal Data** (`test_retain.py`) ✅ **COMPLETED**
   - Event date storage as occurred_start
   - Temporal ordering of facts
   - Distinction between occurred_start and mentioned_at
   - mentioned_at bug fix (was using event_date, now uses current timestamp)

6. **Context Tracking** (`test_retain.py`) ✅ **COMPLETED**
   - Context preservation in storage
   - Multiple contexts in batch operations

7. **Metadata Storage** (`test_retain.py`) ✅ **COMPLETED**
   - Storage and retrieval of metadata (basic test)
   - Note: Full metadata support depends on API implementation

8. **Batch Processing Edge Cases** (`test_retain.py`) ✅ **COMPLETED**
   - Empty batch handling
   - Single-item batch processing
   - Mixed content sizes in batch
   - Missing optional fields handling

9. **Multi-Document Batches** (`test_retain.py`) ✅ **COMPLETED**
   - Multiple documents via separate retain calls
   - Document upsert behavior

10. **Chunk Storage Advanced** (`test_retain.py`) ✅ **COMPLETED**
    - Chunk-to-fact mapping via chunk_id
    - Chunk ordering preservation (chunk_index)
    - Chunk truncation behavior

---

## 🔴 Missing Test Coverage - Priority Features

### 1. **Fact Type Override**
**Feature**: `fact_type_override` parameter to force fact type
- Location: `memory_engine.py:593, 634`
- Use cases: Forcing 'opinion', 'world', or 'bank' facts

**Proposed Tests**:
```python
@pytest.mark.asyncio
async def test_fact_type_override_opinion(memory):
    """Test that fact_type_override='opinion' stores all facts as opinions."""

@pytest.mark.asyncio
async def test_fact_type_override_world(memory):
    """Test that fact_type_override='world' stores all facts as world facts."""

@pytest.mark.asyncio
async def test_fact_type_override_bank(memory):
    """Test that fact_type_override='bank' stores all facts as bank facts."""
```

---

### 2. **Confidence Scores for Opinions**
**Feature**: `confidence_score` parameter for opinion reliability
- Location: `memory_engine.py:594, 635`
- Use cases: Tracking opinion certainty

**Proposed Tests**:
```python
@pytest.mark.asyncio
async def test_confidence_score_storage(memory):
    """Test that confidence scores are stored and retrievable."""
    # Store opinion with confidence 0.8
    # Recall and verify confidence is preserved

@pytest.mark.asyncio
async def test_confidence_score_ranking(memory):
    """Test that higher confidence opinions rank higher in recall."""
    # Store multiple opinions with different confidence scores
    # Verify recall returns higher confidence first
```

---

### 3. **~~Temporal Data (event_date)~~** ✅ **IMPLEMENTED**
~~**Feature**: Track when events occurred vs when they were mentioned~~
- ~~Location: `memory_engine.py:591, occurred_start/occurred_end/mentioned_at`~~
- ~~Use cases: Temporal reasoning, time-based queries~~
- **Status**: All 3 tests implemented and passing
- **Bug Fixed**: mentioned_at was using event_date instead of current timestamp

---

### 4. **~~Context Tracking~~** ✅ **IMPLEMENTED**
~~**Feature**: Store context about why/how memory was formed~~
- ~~Location: `memory_engine.py:590`~~
- ~~Use cases: Understanding memory provenance~~
- **Status**: 2 tests implemented

---

### 5. **Entity Extraction and Linking**
**Feature**: Automatic entity detection and relationship tracking
- Location: `entity_processing.py`, `memory_engine.py:1741-1763`

**Proposed Tests**:
```python
@pytest.mark.asyncio
async def test_entity_extraction(memory):
    """Test that entities are automatically extracted from content."""
    # Store "Alice works at Google"
    # Verify "Alice" and "Google" are extracted as entities

@pytest.mark.asyncio
async def test_entity_linking_across_facts(memory):
    """Test that same entity is linked across multiple facts."""
    # Store multiple facts mentioning "Alice"
    # Verify they link to same entity_id

@pytest.mark.asyncio
async def test_entity_observations_generation(memory):
    """Test that entity observations are generated and updated."""
    # Store facts about entity
    # Check entity observations contain summaries
```

---

### 6. **Fact Deduplication**
**Feature**: Prevent storing duplicate/similar facts
- Location: `memory_engine.py:1014-1079` (deduplication check)

**Proposed Tests**:
```python
@pytest.mark.asyncio
async def test_exact_duplicate_prevention(memory):
    """Test that exact duplicate facts are not stored twice."""
    # Store same fact twice
    # Verify only one unit created

@pytest.mark.asyncio
async def test_similar_fact_deduplication(memory):
    """Test that semantically similar facts are deduplicated."""
    # Store "Alice works at Google" and "Alice is employed by Google"
    # Verify deduplication occurs based on similarity

@pytest.mark.asyncio
async def test_temporal_deduplication(memory):
    """Test that deduplication respects temporal windows."""
    # Store similar facts with different timestamps
    # Verify they're treated as separate if time difference is large
```

---

### 7. **Causal Relationships**
**Feature**: Track causal links between facts
- Location: `memory_engine.py:810` (all_causal_relations)

**Proposed Tests**:
```python
@pytest.mark.asyncio
async def test_causal_relationship_extraction(memory):
    """Test that causal relationships are extracted."""
    # Store "Alice got promoted because she shipped the project"
    # Verify causal link is extracted

@pytest.mark.asyncio
async def test_causal_relationship_recall(memory):
    """Test that causal relationships affect recall."""
    # Store facts with causal links
    # Query should surface related facts
```

---

### 8. **Embeddings and Vector Storage**
**Feature**: Generate and store embeddings for semantic search
- Location: `memory_engine.py:904-923`

**Proposed Tests**:
```python
@pytest.mark.asyncio
async def test_embedding_generation(memory):
    """Test that embeddings are generated for facts."""
    # Store fact
    # Query database to verify embedding exists

@pytest.mark.asyncio
async def test_semantic_similarity_search(memory):
    """Test that semantically similar facts are recalled together."""
    # Store "Alice loves Python"
    # Query "Who enjoys programming?"
    # Verify Alice's fact is recalled via semantic similarity
```

---

### 9. **~~Metadata Storage~~** ✅ **IMPLEMENTED**
~~**Feature**: Store arbitrary metadata with facts~~
- ~~Location: `memory_engine.py:792, 811`~~
- **Status**: Basic metadata test implemented
- **Note**: Full metadata support depends on API layer implementation

---

### 10. **~~Batch Processing Edge Cases~~** ✅ **IMPLEMENTED**
~~**Feature**: Handle various batch sizes and edge cases~~
- **Status**: 4 tests implemented
  - Empty batch handling
  - Single-item batch
  - Mixed content sizes
  - Missing optional fields

---

### 11. **~~Multi-Document Batches~~** ✅ **IMPLEMENTED**
~~**Feature**: Process multiple documents in one batch call~~
- **Status**: 2 tests implemented
  - Multiple documents via separate retain calls
  - Document upsert behavior

---

### 12. **~~Chunk Storage Advanced~~** ✅ **IMPLEMENTED**
~~**Feature**: Chunk-level operations and queries~~
- **Status**: 3 tests implemented
  - Chunk-to-fact mapping
  - Chunk ordering preservation
  - Chunk truncation behavior

---

## 🔵 Lower Priority / Edge Cases

### 13. **Error Handling**
- Invalid bank_id
- Malformed content
- Missing required fields
- Database connection failures

### 14. **Performance Tests**
- Large batch throughput
- Concurrent retention operations
- Memory usage under load

### 15. **Backward Compatibility**
- Retention without document_id
- Legacy API usage patterns

---

## Test Implementation Status

### ✅ Completed Tests (17 total tests implemented)
1. ~~Temporal data tests (3 tests)~~ ✅
2. ~~Context tracking tests (2 tests)~~ ✅
3. ~~Metadata tests (1 test - basic)~~ ✅
4. ~~Batch edge cases (4 tests)~~ ✅
5. ~~Multi-document batches (2 tests)~~ ✅
6. ~~Chunk storage advanced (3 tests)~~ ✅
7. ~~Bug Fix: mentioned_at now uses current timestamp~~ ✅

### 🟡 Not Implemented (Requires LLM or Complex Setup)
These tests depend on non-deterministic LLM behavior or require complex setup:
1. Fact type override tests (3 tests) - Depends on LLM classification
2. Confidence score tests (2 tests) - Depends on LLM opinion extraction
3. Entity extraction tests (3 tests) - Depends on LLM entity detection
4. Fact deduplication tests (3 tests) - Depends on LLM similarity detection
5. Causal relationships tests (2 tests) - Depends on LLM causal extraction
6. Embeddings tests (2 tests) - Would test internal implementation details

### 🔵 Deferred (Lower Priority)
7. Error handling (4 tests) - Infrastructure tests
8. Performance tests (3 tests) - Requires specific benchmarking setup

---

## Success Metrics

- **Coverage**: 95%+ line coverage for retain code paths
- **Reliability**: All tests pass consistently
- **Documentation**: Each test includes clear docstring explaining what it validates
- **Maintainability**: Tests are independent and can run in parallel
