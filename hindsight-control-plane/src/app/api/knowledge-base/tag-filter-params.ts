import type { NextRequest } from "next/server";

/** The knowledge-base tag filter (tags, tags_match) of `request`, as a query string. */
export function tagFilterParams(request: NextRequest): string {
  const out = new URLSearchParams();
  for (const key of ["tags", "tags_match"]) {
    request.nextUrl.searchParams.getAll(key).forEach((v) => out.append(key, v));
  }
  return out.toString();
}
