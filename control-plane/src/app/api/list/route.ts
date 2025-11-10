import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.DATAPLANE_API_URL || 'http://localhost:8080';

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const queryString = searchParams.toString();

    const response = await fetch(`${DATAPLANE_URL}/api/list?${queryString}`);
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
