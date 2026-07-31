import { defineConfig } from "vitest/config";
import { tmpdir } from "node:os";
import { join } from "node:path";

export default defineConfig({
  test: {
    env: {
      // Unit tests exercise code paths that emit diagnostics; keep them out of the REAL
      // /tmp/hindsight-plugin.log so a developer's diag trail isn't polluted with test noise.
      HINDSIGHT_DIAG_FILE: join(tmpdir(), "hindsight-plugin-test.log"),
      HINDSIGHT_LOG_FILE: join(tmpdir(), "hindsight-plugin-test-leveled.log"),
    },
  },
});
