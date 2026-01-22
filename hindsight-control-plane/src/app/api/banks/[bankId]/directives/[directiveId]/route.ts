import { NextResponse } from "next/server";

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || "http://localhost:8888";

export async function GET(
  request: Request,
  { params }: { params: Promise<{ bankId: string; directiveId: string }> }
) {
  try {
    const { bankId, directiveId } = await params;

    if (!bankId || !directiveId) {
      return NextResponse.json({ error: "bank_id and directive_id are required" }, { status: 400 });
    }

    const response = await fetch(
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/directives/${directiveId}`,
      { method: "GET" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error getting directive:", errorText);
      return NextResponse.json({ error: "Failed to get directive" }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error getting directive:", error);
    return NextResponse.json({ error: "Failed to get directive" }, { status: 500 });
  }
}

export async function PATCH(
  request: Request,
  { params }: { params: Promise<{ bankId: string; directiveId: string }> }
) {
  try {
    const { bankId, directiveId } = await params;

    if (!bankId || !directiveId) {
      return NextResponse.json({ error: "bank_id and directive_id are required" }, { status: 400 });
    }

    const body = await request.json();

    const response = await fetch(
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/directives/${directiveId}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error updating directive:", errorText);
      return NextResponse.json(
        { error: errorText || "Failed to update directive" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error updating directive:", error);
    return NextResponse.json({ error: "Failed to update directive" }, { status: 500 });
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ bankId: string; directiveId: string }> }
) {
  try {
    const { bankId, directiveId } = await params;

    if (!bankId || !directiveId) {
      return NextResponse.json({ error: "bank_id and directive_id are required" }, { status: 400 });
    }

    const response = await fetch(
      `${DATAPLANE_URL}/v1/default/banks/${bankId}/directives/${directiveId}`,
      { method: "DELETE" }
    );

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error deleting directive:", errorText);
      return NextResponse.json(
        { error: errorText || "Failed to delete directive" },
        { status: response.status }
      );
    }

    return NextResponse.json({ success: true }, { status: 200 });
  } catch (error) {
    console.error("Error deleting directive:", error);
    return NextResponse.json({ error: "Failed to delete directive" }, { status: 500 });
  }
}
