import { NextResponse } from 'next/server';
import { sdk, lowLevelClient } from '@/lib/hindsight-client';

export async function GET() {
  try {
    const response = await sdk.listBanks({ client: lowLevelClient });
    return NextResponse.json(response.data, { status: 200 });
  } catch (error) {
    console.error('Error fetching banks:', error);
    return NextResponse.json(
      { error: 'Failed to fetch banks' },
      { status: 500 }
    );
  }
}
