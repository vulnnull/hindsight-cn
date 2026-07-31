import { describe, expect, it } from "vitest";
import { parseDevinMessages } from "./transcript-devin";

describe("parseDevinMessages", () => {
  it("uses the final streamed assistant update", () => {
    expect(
      parseDevinMessages([
        {
          node_id: 1,
          chat_message: JSON.stringify({
            message_id: "u",
            role: "user",
            content: "Explain this repo",
          }),
        },
        {
          node_id: 2,
          chat_message: JSON.stringify({ message_id: "a", role: "assistant", content: "Partial" }),
        },
        {
          node_id: 3,
          chat_message: JSON.stringify({
            message_id: "a",
            role: "assistant",
            content: "Complete answer",
          }),
        },
      ])
    ).toEqual([
      { role: "user", content: "Explain this repo" },
      { role: "assistant", content: "Complete answer" },
    ]);
  });
});
