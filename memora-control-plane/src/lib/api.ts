/**
 * API client for the control plane API (which proxies to the dataplane)
 */

export class DataplaneClient {
  private async fetchApi<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    // Call the control plane API routes, not the dataplane directly
    const response = await fetch(path, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  /**
   * Search memory using semantic similarity
   */
  async search(params: {
    query: string;
    fact_type: ('world' | 'agent' | 'opinion')[];
    agent_id: string;
    thinking_budget?: number;
    max_tokens?: number;
    reranker?: string;
    trace?: boolean;
  }) {
    const { agent_id, ...body } = params;
    return this.fetchApi(`/api/v1/agents/${agent_id}/memories/search`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Think and generate answer
   */
  async think(params: {
    query: string;
    agent_id: string;
    thinking_budget?: number;
  }) {
    const { agent_id, ...body } = params;
    return this.fetchApi(`/api/v1/agents/${agent_id}/think`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Store multiple memories in batch
   */
  async batchPut(params: {
    agent_id: string;
    items: Array<{
      content: string;
      event_date?: string;
      context?: string;
    }>;
    document_id?: string;
  }) {
    const { agent_id, ...body } = params;
    return this.fetchApi(`/api/v1/agents/${agent_id}/memories`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * Store multiple memories asynchronously
   * Note: If document_id is provided and already exists, the document will be automatically replaced (upsert behavior).
   */
  async batchPutAsync(params: {
    agent_id: string;
    items: Array<{
      content: string;
      event_date?: string;
      context?: string;
    }>;
    document_id?: string;
  }) {
    const { agent_id, ...body } = params;
    return this.fetchApi(`/api/v1/agents/${agent_id}/memories/async`, {
      method: 'POST',
      body: JSON.stringify(body),
    });
  }

  /**
   * List all agents
   */
  async listAgents() {
    return this.fetchApi<{ agents: any[] }>('/api/v1/agents', { cache: 'no-store' });
  }

  /**
   * Get agent statistics
   */
  async getAgentStats(agentId: string) {
    return this.fetchApi(`/api/v1/agents/${agentId}/stats`);
  }

  /**
   * Get graph data for visualization
   */
  async getGraphData(params: {
    agent_id: string;
    fact_type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params.fact_type) queryParams.append('fact_type', params.fact_type);

    const path = `/api/v1/agents/${params.agent_id}/graph${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.fetchApi(path);
  }

  /**
   * List memory units
   */
  async listMemoryUnits(params: {
    agent_id: string;
    fact_type?: string;
    q?: string;
    limit?: number;
    offset?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params.fact_type) queryParams.append('fact_type', params.fact_type);
    if (params.q) queryParams.append('q', params.q);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset) queryParams.append('offset', params.offset.toString());

    const path = `/api/v1/agents/${params.agent_id}/memories/list${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.fetchApi(path);
  }

  /**
   * List documents
   */
  async listDocuments(params: {
    agent_id: string;
    q?: string;
    limit?: number;
    offset?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params.q) queryParams.append('q', params.q);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.offset) queryParams.append('offset', params.offset.toString());

    const path = `/api/v1/agents/${params.agent_id}/documents${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.fetchApi(path);
  }

  /**
   * Get document by ID
   */
  async getDocument(documentId: string, agentId: string) {
    return this.fetchApi(`/api/v1/agents/${agentId}/documents/${documentId}`);
  }

  /**
   * List async operations for an agent
   */
  async listOperations(agentId: string) {
    return this.fetchApi(`/api/v1/agents/${agentId}/operations`);
  }

  /**
   * Cancel a pending async operation
   */
  async cancelOperation(agentId: string, operationId: string) {
    return this.fetchApi(`/api/v1/agents/${agentId}/operations/${operationId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Delete a memory unit
   */
  async deleteMemoryUnit(agentId: string, unitId: string) {
    return this.fetchApi(`/api/v1/agents/${agentId}/memories/${unitId}`, {
      method: 'DELETE',
    });
  }
}

// Export a singleton instance
export const dataplaneClient = new DataplaneClient();

/**
 * Server-side dataplane client that calls the dataplane directly
 * Only use this on the server side (in API routes)
 */
export class ServerDataplaneClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.MEMORA_CP_DATAPLANE_API_URL || 'http://localhost:8080';
  }

  async fetchDataplane<T>(
    path: string,
    options?: RequestInit
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;

    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`Dataplane Error: ${response.status} - ${error}`);
    }

    return response.json();
  }
}

export const serverDataplaneClient = new ServerDataplaneClient();
