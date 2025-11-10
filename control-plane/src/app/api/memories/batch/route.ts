import { NextRequest, NextResponse } from 'next/server';

const DATAPLANE_URL = process.env.DATAPLANE_API_URL || 'http://localhost:8080';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${DATAPLANE_URL}/api/memories/batch`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
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
