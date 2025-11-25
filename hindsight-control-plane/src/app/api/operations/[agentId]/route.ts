import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ agentId: string }> }
) {
  try {
    const { agentId } = await params;
    const response = await fetch(`${DATAPLANE_URL}/api/v1/agents/${agentId}/operations`);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching operations:', error);
    return NextResponse.json(
      { error: 'Failed to fetch operations' },
      { status: 500 }
    );
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ agentId: string }> }
) {
  try {
    const { agentId } = await params;
    const searchParams = request.nextUrl.searchParams;
    const operationId = searchParams.get('operation_id');

    if (!operationId) {
      return NextResponse.json(
        { error: 'operation_id is required' },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${DATAPLANE_URL}/api/v1/agents/${agentId}/operations/${operationId}`,
      { method: 'DELETE' }
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error canceling operation:', error);
    return NextResponse.json(
      { error: 'Failed to cancel operation' },
      { status: 500 }
    );
  }
}
