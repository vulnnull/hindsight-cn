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
    agent_id?: string;
    thinking_budget?: number;
    max_tokens?: number;
    reranker?: string;
    trace?: boolean;
  }) {
    return this.fetchApi('/api/search', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: params.agent_id || 'default',
        ...params,
      }),
    });
  }

  /**
   * Think and generate answer
   */
  async think(params: {
    query: string;
    agent_id?: string;
    thinking_budget?: number;
  }) {
    return this.fetchApi('/api/think', {
      method: 'POST',
      body: JSON.stringify({
        agent_id: params.agent_id || 'default',
        ...params,
      }),
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
    return this.fetchApi('/api/memories/batch', {
      method: 'POST',
      body: JSON.stringify(params),
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
    return this.fetchApi('/api/memories/batch_async', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  }

  /**
   * List all agents
   */
  async listAgents() {
    return this.fetchApi<{ agents: string[] }>('/api/agents', { cache: 'no-store' });
  }

  /**
   * Get agent statistics
   */
  async getAgentStats(agentId: string) {
    return this.fetchApi(`/api/stats/${agentId}`);
  }

  /**
   * Get graph data for visualization
   */
  async getGraphData(params?: {
    agent_id?: string;
    fact_type?: string;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.agent_id) queryParams.append('agent_id', params.agent_id);
    if (params?.fact_type) queryParams.append('fact_type', params.fact_type);

    const path = `/api/graph${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.fetchApi(path);
  }

  /**
   * List memory units
   */
  async listMemoryUnits(params?: {
    agent_id?: string;
    fact_type?: string;
    q?: string;
    limit?: number;
    offset?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.agent_id) queryParams.append('agent_id', params.agent_id);
    if (params?.fact_type) queryParams.append('fact_type', params.fact_type);
    if (params?.q) queryParams.append('q', params.q);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const path = `/api/list${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.fetchApi(path);
  }

  /**
   * List documents
   */
  async listDocuments(params?: {
    agent_id?: string;
    q?: string;
    limit?: number;
    offset?: number;
  }) {
    const queryParams = new URLSearchParams();
    if (params?.agent_id) queryParams.append('agent_id', params.agent_id);
    if (params?.q) queryParams.append('q', params.q);
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.offset) queryParams.append('offset', params.offset.toString());

    const path = `/api/documents${queryParams.toString() ? `?${queryParams}` : ''}`;
    return this.fetchApi(path);
  }

  /**
   * Get document by ID
   */
  async getDocument(documentId: string, agentId: string) {
    const queryParams = new URLSearchParams({ agent_id: agentId });
    return this.fetchApi(`/api/documents/${documentId}?${queryParams}`);
  }

  /**
   * List async operations for an agent
   */
  async listOperations(agentId: string) {
    return this.fetchApi(`/api/operations/${agentId}`);
  }

  /**
   * Cancel a pending async operation
   */
  async cancelOperation(operationId: string) {
    return this.fetchApi(`/api/operations/${operationId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Delete a memory unit
   */
  async deleteMemoryUnit(unitId: string) {
    return this.fetchApi(`/api/memory/${unitId}`, {
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
    this.baseUrl = process.env.DATAPLANE_API_URL || 'http://localhost:8080';
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
