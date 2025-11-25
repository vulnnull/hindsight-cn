import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const agentId = body.agent_id;

    if (!agentId) {
      return NextResponse.json(
        { error: 'agent_id is required' },
        { status: 400 }
      );
    }

    // Remove agent_id from body as it's now in the path
    const { agent_id, ...bodyWithoutAgentId } = body;

    const response = await fetch(`${DATAPLANE_URL}/api/v1/agents/${agentId}/memories`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(bodyWithoutAgentId),
    });

    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error batch put:', error);
    return NextResponse.json(
      { error: 'Failed to batch put' },
      { status: 500 }
    );
  }
}
