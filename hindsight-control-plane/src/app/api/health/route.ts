import { NextResponse } from "next/server";
import { sdk, lowLevelClient } from "@/lib/hindsight-client";

export async function GET() {
  const status: {
    status: string;
    service: string;
    dataplane?: {
      status: string;
      url: string;
      error?: string;
    };
  } = {
    status: "ok",
    service: "hindsight-control-plane",
  };

  // Check dataplane connectivity
  const dataplaneUrl = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || "http://localhost:8888";
  try {
    await sdk.listBanks({ client: lowLevelClient });
    status.dataplane = {
      status: "connected",
      url: dataplaneUrl,
    };
  } catch (error) {
    status.dataplane = {
      status: "disconnected",
      url: dataplaneUrl,
      error: error instanceof Error ? error.message : String(error),
    };
  }

  return NextResponse.json(status, { status: 200 });
}
