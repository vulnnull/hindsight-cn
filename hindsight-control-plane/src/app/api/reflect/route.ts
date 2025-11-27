import { NextRequest, NextResponse } from 'next/server';
import { hindsightClient } from '@/lib/hindsight-client';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const bankId = body.bank_id || body.agent_id || 'default';
    const { query, context, budget, thinking_budget } = body;

    const response = await hindsightClient.reflect(
      bankId,
      query,
      {
        context,
        budget: budget || (thinking_budget ? 'mid' : 'low')
      }
    );

    return NextResponse.json(response, { status: 200 });
  } catch (error) {
    console.error('Error reflecting:', error);
    return NextResponse.json(
      { error: 'Failed to reflect' },
      { status: 500 }
    );
  }
}
