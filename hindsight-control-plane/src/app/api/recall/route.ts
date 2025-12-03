import { NextRequest, NextResponse } from 'next/server';
import { lowLevelClient, sdk } from '@/lib/hindsight-client';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const bankId = body.bank_id || body.agent_id || 'default';
    const { query, types, fact_type, max_tokens, trace, budget, include, query_timestamp } = body;

    console.log('[Recall API] Request:', { bankId, query, types: types || fact_type, max_tokens, trace, budget, query_timestamp });
    console.log('[Recall API] Include options:', JSON.stringify(include, null, 2));

    const response = await sdk.recallMemories({
      client: lowLevelClient,
      path: { bank_id: bankId },
      body: {
        query,
        types: types || fact_type,
        max_tokens,
        trace,
        budget: budget || 'mid',
        include,
        query_timestamp,
      },
    });

    if (!response.data) {
      console.error('[Recall API] No data in response', { response, error: response.error });
      throw new Error(`API returned no data: ${JSON.stringify(response.error || 'Unknown error')}`);
    }

    console.log('[Recall API] Response structure:', {
      hasResults: !!response.data?.results,
      resultsCount: response.data?.results?.length,
      hasTrace: !!response.data?.trace,
      hasEntities: !!response.data?.entities,
      entitiesType: typeof response.data?.entities,
      entitiesKeys: response.data?.entities ? Object.keys(response.data.entities) : null,
      hasChunks: !!response.data?.chunks,
      chunksType: typeof response.data?.chunks,
      chunksKeys: response.data?.chunks ? Object.keys(response.data.chunks) : null,
    });

    // Return a clean JSON object by spreading the response
    // This ensures any non-serializable properties are excluded
    const jsonResponse = {
      results: response.data.results,
      trace: response.data.trace,
      entities: response.data.entities,
      chunks: response.data.chunks,
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
