/**
 * Shared Hindsight API client instance for the control plane.
 * Configured to connect to the dataplane API server.
 */

import { HindsightClient, createClient, createConfig, sdk } from "@vectorize-io/hindsight-client";

const DATAPLANE_URL = process.env.HINDSIGHT_CP_DATAPLANE_API_URL || "http://localhost:8888";

/**
 * High-level client with convenience methods
 */
export const hindsightClient = new HindsightClient({ baseUrl: DATAPLANE_URL });

/**
 * Low-level client for direct SDK access
 */
export const lowLevelClient = createClient(createConfig({ baseUrl: DATAPLANE_URL }));

/**
 * Export SDK functions for direct API access
 */
export { sdk };
