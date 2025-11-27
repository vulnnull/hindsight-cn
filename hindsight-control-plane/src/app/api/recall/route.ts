import { NextRequest, NextResponse } from 'next/server';
import { hindsightClient } from '@/lib/hindsight-client';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const bankId = body.bank_id || body.agent_id || 'default';
    const { query, types, fact_type, max_tokens, trace, budget } = body;

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

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    console.error('Error recalling:', error);
    return NextResponse.json(
      { error: 'Failed to recall' },
      { status: 500 }
    );
  }
}
