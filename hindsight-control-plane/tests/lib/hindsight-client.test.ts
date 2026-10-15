import { describe, expect, it } from "vitest";
import { USER_AGENT, getDataplaneHeaders, lowLevelClient } from "@/lib/hindsight-client";
import { version } from "../../package.json";

describe("dataplane User-Agent", () => {
  it("identifies the control plane and its version", () => {
    expect(USER_AGENT).toBe(`hindsight-control-plane/${version}`);
  });

  it("is sent on direct fetches and by the low-level client", () => {
    expect(getDataplaneHeaders({ "Content-Type": "application/json" })).toMatchObject({
      "User-Agent": USER_AGENT,
      "Content-Type": "application/json",
    });
    const headers = lowLevelClient.getConfig().headers as Headers;
    expect(headers.get("User-Agent")).toBe(USER_AGENT);
  });
});
