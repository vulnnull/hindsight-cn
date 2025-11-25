import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const agentId = searchParams.get('agent_id');

    if (!agentId) {
      return NextResponse.json(
        { error: 'agent_id is required' },
        { status: 400 }
      );
    }

    // Remove agent_id from query params and rebuild query string
    const newSearchParams = new URLSearchParams(searchParams);
    newSearchParams.delete('agent_id');
    const queryString = newSearchParams.toString();

    const url = `${DATAPLANE_URL}/api/v1/agents/${agentId}/memories/list${queryString ? `?${queryString}` : ''}`;
    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error listing memory units:', error);
    return NextResponse.json(
      { error: 'Failed to list memory units' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const agentId = searchParams.get('agent_id');
    const unitId = searchParams.get('unit_id');

    if (!agentId) {
      return NextResponse.json(
        { error: 'agent_id is required' },
        { status: 400 }
      );
    }

    if (!unitId) {
      return NextResponse.json(
        { error: 'unit_id is required' },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${DATAPLANE_URL}/api/v1/agents/${agentId}/memories/${unitId}`,
      { method: 'DELETE' }
    );
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error deleting memory unit:', error);
    return NextResponse.json(
      { error: 'Failed to delete memory unit' },
      { status: 500 }
    );
  }
}
