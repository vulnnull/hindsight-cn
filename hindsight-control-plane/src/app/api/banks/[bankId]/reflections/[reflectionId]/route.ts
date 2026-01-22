import { NextResponse } from "next/server";

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || "http://localhost:8888";

export async function GET(
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
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/reflections/${reflectionId}`,
      { method: "GET" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error getting reflection:", errorText);
      return NextResponse.json({ error: "Failed to get reflection" }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error getting reflection:", error);
    return NextResponse.json({ error: "Failed to get reflection" }, { status: 500 });
  }
}

export async function PATCH(
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

    const body = await request.json();

    const response = await fetch(
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/reflections/${reflectionId}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error updating reflection:", errorText);
      return NextResponse.json(
        { error: errorText || "Failed to update reflection" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error updating reflection:", error);
    return NextResponse.json({ error: "Failed to update reflection" }, { status: 500 });
  }
}

export async function DELETE(
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
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/reflections/${reflectionId}`,
      { method: "DELETE" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error deleting reflection:", errorText);
      return NextResponse.json(
        { error: errorText || "Failed to delete reflection" },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("Error deleting reflection:", error);
    return NextResponse.json({ error: "Failed to delete reflection" }, { status: 500 });
  }
}
