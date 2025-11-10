'use client';

import { useAgent } from '@/lib/agent-context';

export function AgentSelector() {
  const { currentAgent, setCurrentAgent, agents, loadAgents } = useAgent();

  return (
    <div className="bg-card text-card-foreground px-5 py-3 border-b-4 border-primary">
      <div className="flex items-center gap-2.5 text-sm">
        <span className="font-medium">Memory Graph</span>
        <span className="text-muted-foreground font-bold">/</span>
        <span className="font-medium">Agent:</span>
        <select
          value={currentAgent || ''}
          onChange={(e) => setCurrentAgent(e.target.value || null)}
          className="px-3 py-1.5 border-2 border-primary rounded bg-background text-foreground text-sm font-bold cursor-pointer transition-all hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Select an agent...</option>
          {agents.map((agent) => (
            <option key={agent} value={agent}>
              {agent}
            </option>
          ))}
        </select>
        <button
          onClick={loadAgents}
          className="ml-2 px-2 py-1 text-xs bg-primary text-primary-foreground hover:opacity-90 rounded transition-colors"
          title="Refresh agents"
        >
          🔄
        </button>
      </div>
    </div>
  );
}
