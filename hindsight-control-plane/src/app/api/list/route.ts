import { NextRequest, NextResponse } from 'next/server';
import { hindsightClient, sdk, lowLevelClient } from '@/lib/hindsight-client';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const bankId = searchParams.get('bank_id') || searchParams.get('agent_id');

    if (!bankId) {
      return NextResponse.json(
        { error: 'bank_id is required' },
        { status: 400 }
      );
    }

    const limit = searchParams.get('limit') ? Number(searchParams.get('limit')) : undefined;
    const offset = searchParams.get('offset') ? Number(searchParams.get('offset')) : undefined;
    const type = searchParams.get('type') || searchParams.get('fact_type') || undefined;
    const q = searchParams.get('q') || undefined;

    const response = await hindsightClient.listMemories(bankId, {
      limit,
      offset,
      type,
      q
    });

    return NextResponse.json(response, { status: 200 });
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
    const bankId = searchParams.get('bank_id') || searchParams.get('agent_id');
    const unitId = searchParams.get('unit_id');

    if (!bankId) {
      return NextResponse.json(
        { error: 'bank_id is required' },
        { status: 400 }
      );
    }

    if (!unitId) {
      return NextResponse.json(
        { error: 'unit_id is required' },
        { status: 400 }
      );
    }

    const response = await sdk.sdk.deleteMemoryUnit({
      client: lowLevelClient,
      path: { bank_id: bankId, unit_id: unitId }
    });

    return NextResponse.json(response.data, { status: 200 });
  } catch (error) {
    console.error('Error deleting memory unit:', error);
    return NextResponse.json(
      { error: 'Failed to delete memory unit' },
      { status: 500 }
    );
  }
}
