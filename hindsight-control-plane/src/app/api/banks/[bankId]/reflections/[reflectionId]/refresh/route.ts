import { NextResponse } from "next/server";

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || "http://localhost:8888";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ bankId: string; reflectionId: string }> }
) {
  try {
    const { bankId, reflectionId } = await params;

    if (!bankId || !reflectionId) {
      return NextResponse.json(
        { error: "bank_id and reflection_id are required" },
        { status: 400 }
      );
    }

    const response = await fetch(
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/reflections/${reflectionId}/refresh`,
      { method: "POST" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error refreshing reflection:", errorText);
      return NextResponse.json(
        { error: errorText || "Failed to refresh reflection" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error refreshing reflection:", error);
    return NextResponse.json({ error: "Failed to refresh reflection" }, { status: 500 });
  }
}
