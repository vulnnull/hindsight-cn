import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ documentId: string }> }
) {
  try {
    const { documentId } = await params;
    const searchParams = request.nextUrl.searchParams;
    const agentId = searchParams.get('agent_id');

    if (!agentId) {
      return NextResponse.json(
        { error: 'agent_id is required' },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${DATAPLANE_URL}/api/v1/agents/${agentId}/documents/${documentId}`
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching document:', error);
    return NextResponse.json(
      { error: 'Failed to fetch document' },
      { status: 500 }
    );
  }
}
