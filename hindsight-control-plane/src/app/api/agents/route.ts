import { NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || 'http://localhost:8888';

export async function GET() {
  try {
    const response = await fetch(`${DATAPLANE_URL}/api/v1/agents`);
    const data = await response.json();
    return NextResponse.json(data, { status: response.status });
  } catch (error) {
    console.error('Error fetching agents:', error);
    return NextResponse.json(
      { error: 'Failed to fetch agents' },
      { status: 500 }
    );
  }
}
