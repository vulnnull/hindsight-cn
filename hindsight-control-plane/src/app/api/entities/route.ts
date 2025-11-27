import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const bankId = searchParams.get('bank_id');

    if (!bankId) {
      return NextResponse.json(
        { error: 'bank_id is required' },
        { status: 400 }
      );
    }

    // Remove bank_id from query params and rebuild query string
    const newSearchParams = new URLSearchParams(searchParams);
    newSearchParams.delete('bank_id');
    const queryString = newSearchParams.toString();

    const url = `${DATAPLANE_URL}/api/v1/banks/${bankId}/entities${queryString ? `?${queryString}` : ''}`;
    const response = await fetch(url);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error listing entities:', error);
    return NextResponse.json(
      { error: 'Failed to list entities' },
      { status: 500 }
    );
  }
}
