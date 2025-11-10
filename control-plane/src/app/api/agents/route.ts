import { NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.DATAPLANE_API_URL || 'http://localhost:8080';

export async function GET() {
  try {
    const response = await fetch(`${DATAPLANE_URL}/api/agents`);
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
