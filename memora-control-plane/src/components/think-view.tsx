'use client';

import { useState } from 'react';
import { dataplaneClient } from '@/lib/api';
import { useAgent } from '@/lib/agent-context';

export function ThinkView() {
  const { currentAgent } = useAgent();
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [budget, setBudget] = useState(50);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runThink = async () => {
    if (!currentAgent || !query) return;

    setLoading(true);
    try {
      const data: any = await dataplaneClient.think({
        query,
        agent_id: currentAgent,
        thinking_budget: budget,
        context: context || undefined,
      });
      setResult(data);
    } catch (error) {
      console.error('Error running think:', error);
      alert('Error running think: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl">
      <p className="text-gray-600 mb-4">
        Ask questions and get AI-generated answers based on agent identity and world facts.
      </p>

      <div className="bg-gray-50 p-5 rounded-lg border-2 border-slate-800 mb-5">
        <div className="flex gap-4 items-end flex-wrap mb-4">
          <div className="flex-1 min-w-[300px]">
            <label className="font-bold block mb-1">Question:</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your question..."
              className="w-full px-2.5 py-2 border-2 border-gray-300 rounded text-sm"
              onKeyDown={(e) => e.key === 'Enter' && runThink()}
            />
          </div>
          <div>
            <label className="font-bold block mb-1">Budget:</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(parseInt(e.target.value))}
              min="10"
              max="1000"
              className="w-20 px-2.5 py-2 border-2 border-gray-300 rounded text-sm"
            />
          </div>
          <button
            onClick={runThink}
            disabled={loading || !query}
            className="px-6 py-2 bg-green-500 text-white rounded cursor-pointer font-bold text-sm hover:bg-green-600 disabled:bg-gray-400"
          >
            💭 Think
          </button>
        </div>
        <div className="flex-1 min-w-[300px]">
          <label className="font-bold block mb-1">Context (optional):</label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Additional context for the LLM (not used in search)..."
            className="w-full px-2.5 py-2 border-2 border-gray-300 rounded text-sm"
            rows={3}
          />
        </div>
      </div>

      {loading && (
        <div className="text-center py-10 text-gray-600">
          <div className="text-5xl mb-2.5">💭</div>
          <div className="text-lg">Thinking...</div>
        </div>
      )}

      {result && !loading && (
        <div>
          <div className="bg-white p-5 rounded-lg border-2 border-slate-800 shadow mb-8">
            <h3 className="mt-0 text-slate-800 border-b-2 border-slate-800 pb-2.5">Answer</h3>
            <div className="p-4 bg-gray-50 border-l-4 border-green-500 text-base leading-relaxed whitespace-pre-wrap">
              {result.text}
            </div>
          </div>

          <div className="bg-white p-5 rounded-lg border-2 border-slate-800 shadow">
            <h3 className="mt-0 text-slate-800 border-b-2 border-slate-800 pb-2.5">Based On</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
              <div>
                <h4 className="mt-0 mb-2.5 text-blue-700">World Facts (General Knowledge)</h4>
                <div className="bg-blue-50 p-4 rounded border-2 border-blue-700 min-h-[100px]">
                  {result.based_on?.world?.length > 0 ? (
                    <ul className="text-sm">
                      {result.based_on.world.map((fact: any, i: number) => (
                        <li key={i} className="mb-2">
                          {fact.text} <span className="text-gray-500">({fact.score?.toFixed(2)})</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500 text-sm">None</p>
                  )}
                </div>
              </div>

              <div>
                <h4 className="mt-0 mb-2.5 text-orange-700">Agent Facts (Identity)</h4>
                <div className="bg-orange-50 p-4 rounded border-2 border-orange-700 min-h-[100px]">
                  {result.based_on?.agent?.length > 0 ? (
                    <ul className="text-sm">
                      {result.based_on.agent.map((fact: any, i: number) => (
                        <li key={i} className="mb-2">
                          {fact.text} <span className="text-gray-500">({fact.score?.toFixed(2)})</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500 text-sm">None</p>
                  )}
                </div>
              </div>

              <div>
                <h4 className="mt-0 mb-2.5 text-purple-700">Opinions (Agent Beliefs)</h4>
                <div className="bg-purple-50 p-4 rounded border-2 border-purple-700 min-h-[100px]">
                  {result.based_on?.opinion?.length > 0 ? (
                    <ul className="text-sm">
                      {result.based_on.opinion.map((fact: any, i: number) => (
                        <li key={i} className="mb-2">
                          {fact.text} <span className="text-gray-500">({fact.score?.toFixed(2)})</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-gray-500 text-sm">None</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {result.new_opinions && result.new_opinions.length > 0 && (
            <div className="mt-8 bg-green-50 p-5 rounded-lg border-2 border-green-500">
              <h3 className="mt-0 text-green-800 border-b-2 border-green-500 pb-2.5">✨ New Opinions Formed</h3>
              <div className="mt-4">
                {result.new_opinions.map((opinion: any, i: number) => (
                  <div key={i} className="mb-2 p-3 bg-white rounded border border-green-300">
                    <div className="font-semibold">{opinion.text}</div>
                    <div className="text-sm text-gray-600">Confidence: {opinion.confidence?.toFixed(2)}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
