"""
Performance tuning test using real LoComo conversation.

This test loads a long conversation (419 dialogues across 19 sessions),
ingests it into memory, and runs searches to measure performance.
"""
import logging
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path


# Configure logging to show performance metrics
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(name)s: %(message)s'
)


@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minute timeout for performance test
async def test_batch_ingestion_single_call(memory):
    """
    Test ingesting entire conversation in ONE batch call.

    This is the most efficient way - all sessions in one put_batch_async.
    """
    # Load conversation fixture
    fixture_path = Path(__file__).parent / "fixtures" / "locomo_conversation_sample.json"
    with open(fixture_path) as f:
        conversation_data = json.load(f)

    sample_id = conversation_data['sample_id']
    logging.info(f"\n{'='*80}")
    logging.info(f"BATCH INGESTION TEST: {sample_id}")
    logging.info(f"{'='*80}")

    agent_id = f"batch_test_{sample_id}_{datetime.now(timezone.utc).timestamp()}"

    try:
        # Parse all sessions into batch format
        # LIMIT to first 5 sessions for faster iteration during perf tuning
        MAX_SESSIONS = 5
        logging.info(f"\nPreparing batch contents (limiting to {MAX_SESSIONS} sessions for perf tuning)...")
        conversation = conversation_data['conversation']
        batch_contents = []

        for i in range(1, MAX_SESSIONS + 1):
            session_key = f'session_{i}'
            session_date_key = f'session_{i}_date_time'

            if session_key not in conversation or not conversation[session_key]:
                break

            session_dialogues = conversation[session_key]
            session_date = conversation.get(session_date_key, datetime.now(timezone.utc).isoformat())

            # Combine dialogues
            session_text = "\n".join([
                f"{d['speaker']}: {d['text']}"
                for d in session_dialogues
            ])

            # Parse date
            try:
                from dateutil import parser as date_parser
                event_date = date_parser.isoparse(session_date)
            except:
                event_date = datetime.now(timezone.utc)

            batch_contents.append({
                'content': session_text,
                'context': f'session_{i}',
                'event_date': event_date
            })

        logging.info(f"Prepared {len(batch_contents)} sessions for batch ingestion")

        # Single batch call
        logging.info(f"\nIngesting all {len(batch_contents)} sessions in ONE batch call...")
        result_ids = await memory.put_batch_async(
            agent_id=agent_id,
            contents=batch_contents,
            document_id=f"{agent_id}_full_conversation"
        )

        total_units = sum(len(ids) for ids in result_ids)
        logging.info(f"\n{'='*80}")
        logging.info(f"BATCH INGESTION COMPLETE: {total_units} memory units created")
        logging.info(f"{'='*80}")

        # Run one sample search
        logging.info(f"\nRunning sample search...")
        question = conversation_data['qa'][0]['question']
        logging.info(f"Question: {question}")

        results, _ = await memory.search_async(
            agent_id=agent_id,
            query=question,
            fact_type=["world"],
            thinking_budget=100,
            top_k=5,
            enable_trace=False
        )

        logging.info(f"Found {len(results)} results")
        if results:
            logging.info(f"Top result: {results[0]['text'][:100]}...")

    finally:
        # Cleanup
        logging.info("\nCleaning up...")
        await memory.delete_agent(agent_id)
