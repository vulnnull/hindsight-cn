import { NextResponse } from "next/server";

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || "http://localhost:8888";

export async function GET(request: Request, { params }: { params: Promise<{ bankId: string }> }) {
  try {
    const { bankId } = await params;
    const { searchParams } = new URL(request.url);
    const tags = searchParams.getAll("tags");
    const tagsMatch = searchParams.get("tags_match");

    if (!bankId) {
      return NextResponse.json({ error: "bank_id is required" }, { status: 400 });
    }

    const queryParams = new URLSearchParams();
    if (tags.length > 0) {
      tags.forEach((t) => queryParams.append("tags", t));
    }
    if (tagsMatch) {
      queryParams.append("tags_match", tagsMatch);
    }

    const url = `${DATAPLANE_URL}/v1/default/banks/${bankId}/reflections${queryParams.toString() ? `?${queryParams}` : ""}`;
    const response = await fetch(url, { method: "GET" });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error listing reflections:", errorText);
      return NextResponse.json(
        { error: "Failed to list reflections" },
        { status: response.status }
      );
    }

    const data = await response.json();
    return NextResponse.json(data, { status: 200 });
  } catch (error) {
    console.error("Error listing reflections:", error);
    return NextResponse.json({ error: "Failed to list reflections" }, { status: 500 });
  }
}

export async function POST(request: Request, { params }: { params: Promise<{ bankId: string }> }) {
  try {
    const { bankId } = await params;

    if (!bankId) {
      return NextResponse.json({ error: "bank_id is required" }, { status: 400 });
    }

    const body = await request.json();

    const response = await fetch(`${DATAPLANE_URL}/v1/default/banks/${bankId}/reflections`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API error creating reflection:", errorText);
      return NextResponse.json(
        { error: errorText || "Failed to create reflection" },
        { status: response.status }
      );
    }

    const data = await response.json();
    // Returns operation_id - content is generated in background
    return NextResponse.json(data, { status: 202 });
  } catch (error) {
    console.error("Error creating reflection:", error);
    return NextResponse.json({ error: "Failed to create reflection" }, { status: 500 });
  }
}
