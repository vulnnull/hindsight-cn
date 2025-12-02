import { NextRequest, NextResponse } from 'next/server';
import { hindsightClient } from '@/lib/hindsight-client';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const bankId = body.bank_id || body.agent_id || 'default';
    const { query, types, fact_type, max_tokens, trace, budget, include } = body;

    console.log('[Recall API] Request:', { bankId, query, types: types || fact_type, max_tokens, trace, budget });

    const response = await hindsightClient.recallMemories(
      bankId,
      {
        query,
        types: types || fact_type,
        maxTokens: max_tokens,
        trace,
        budget
      }
    );

    console.log('[Recall API] Response type:', typeof response);
    console.log('[Recall API] Response keys:', Object.keys(response || {}));
    console.log('[Recall API] Response structure:', {
      hasResults: !!response?.results,
      resultsCount: response?.results?.length,
      hasTrace: !!response?.trace,
      hasEntities: !!response?.entities,
      hasChunks: !!response?.chunks,
    });

    // Return a clean JSON object by spreading the response
    // This ensures any non-serializable properties are excluded
    const jsonResponse = {
      results: response.results,
      trace: response.trace,
      entities: response.entities,
      chunks: response.chunks,
    };

    return NextResponse.json(jsonResponse, { status: 200 });
  } catch (error) {
    console.error('Error recalling:', error);
    return NextResponse.json(
      { error: 'Failed to recall' },
      { status: 500 }
    );
  }
}
