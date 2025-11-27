import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ entityId: string }> }
) {
  try {
    const { entityId } = await params;
    const searchParams = request.nextUrl.searchParams;
    const bankId = searchParams.get('bank_id');

    if (!bankId) {
      return NextResponse.json(
        { error: 'bank_id is required' },
        { status: 400 }
      );
    }

    // Decode URL-encoded entityId in case it contains special chars
    const decodedEntityId = decodeURIComponent(entityId);
    const url = `${DATAPLANE_URL}/api/v1/banks/${bankId}/entities/${decodedEntityId}`;
    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error getting entity:', error);
    return NextResponse.json(
      { error: 'Failed to get entity' },
      { status: 500 }
    );
  }
}
