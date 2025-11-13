'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { dataplaneClient } from './api';

interface AgentContextType {
  currentAgent: string | null;
  setCurrentAgent: (agent: string | null) => void;
  agents: string[];
  loadAgents: () => Promise<void>;
}

const AgentContext = createContext<AgentContextType | undefined>(undefined);

export function AgentProvider({ children }: { children: React.ReactNode }) {
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [agents, setAgents] = useState<string[]>([]);

  const loadAgents = async () => {
    try {
      const data = await dataplaneClient.listAgents();
      // Extract agent_id from each agent object
      const agentIds = data.agents.map((agent: any) => agent.agent_id);
      setAgents(agentIds);
    } catch (error) {
      console.error('Error loading agents:', error);
    }
  };

  useEffect(() => {
    loadAgents();
  }, []);

  return (
    <AgentContext.Provider value={{ currentAgent, setCurrentAgent, agents, loadAgents }}>
      {children}
    </AgentContext.Provider>
  );
}

export function useAgent() {
  const context = useContext(AgentContext);
  if (context === undefined) {
    throw new Error('useAgent must be used within an AgentProvider');
  }
  return context;
}
