'use client';

import { useState } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';

export function ThinkView() {
  const { currentBank } = useBank();
  const [query, setQuery] = useState('');
  const [context, setContext] = useState('');
  const [budget, setBudget] = useState(50);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  const runReflect = async () => {
    if (!currentBank || !query) return;

    setLoading(true);
    try {
      const budgetValue = budget <= 30 ? 'low' : budget <= 70 ? 'mid' : 'high';
      const data: any = await client.reflect({
        bank_id: currentBank,
        query,
        budget: budgetValue,
        context: context || undefined,
      });
      setResult(data);
    } catch (error) {
      console.error('Error running reflect:', error);
      alert('Error running reflect: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl">
      <div className="bg-card p-5 rounded-lg border-2 border-primary mb-5 shadow">
        <div className="flex gap-4 items-end flex-wrap mb-4">
          <div className="flex-1 min-w-[300px]">
            <label className="font-bold block mb-1 text-card-foreground">Question:</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your question..."
              className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              onKeyDown={(e) => e.key === 'Enter' && runReflect()}
            />
          </div>
          <div>
            <label className="font-bold block mb-1 text-card-foreground">Budget:</label>
            <input
              type="number"
              value={budget}
              onChange={(e) => setBudget(parseInt(e.target.value))}
              min="10"
              max="1000"
              className="w-20 px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          <button
            onClick={runReflect}
            disabled={loading || !query}
            className="px-6 py-2 bg-primary text-primary-foreground rounded cursor-pointer font-bold text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            💭 Reflect
          </button>
        </div>
        <div className="flex-1 min-w-[300px]">
          <label className="font-bold block mb-1 text-card-foreground">Context (optional):</label>
          <textarea
            value={context}
            onChange={(e) => setContext(e.target.value)}
            placeholder="Additional context for the LLM (not used in search)..."
            className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            rows={3}
          />
        </div>
      </div>

      {loading && (
        <div className="text-center py-10 text-muted-foreground">
          <div className="text-5xl mb-2.5">💭</div>
          <div className="text-lg">Reflecting...</div>
        </div>
      )}

      {result && !loading && (
        <div>
          <div className="bg-card p-5 rounded-lg border-2 border-primary shadow mb-8">
            <h3 className="mt-0 text-card-foreground border-b-2 border-primary pb-2.5 font-bold">Answer</h3>
            <div className="p-4 bg-muted border-l-4 border-primary text-base leading-relaxed whitespace-pre-wrap text-foreground">
              {result.text}
            </div>
          </div>

          <div className="bg-card p-5 rounded-lg border-2 border-primary shadow">
            <h3 className="mt-0 text-card-foreground border-b-2 border-primary pb-2.5 font-bold">Based On</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-5 mt-4">
              <div>
                <h4 className="mt-0 mb-2.5 text-blue-700 font-semibold">World Facts (General Knowledge)</h4>
                <div className="bg-blue-50 p-4 rounded border-2 border-blue-700 min-h-[100px]">
                  {result.based_on?.world?.length > 0 ? (
                    <ul className="text-sm space-y-2">
                      {result.based_on.world.map((fact: any, i: number) => (
                        <li key={i} className="text-foreground">
                          {fact.text} <span className="text-muted-foreground">({fact.score?.toFixed(2)})</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-muted-foreground text-sm">None</p>
                  )}
                </div>
              </div>

              <div>
                <h4 className="mt-0 mb-2.5 text-orange-700 font-semibold">Bank Facts (Identity)</h4>
                <div className="bg-orange-50 p-4 rounded border-2 border-orange-700 min-h-[100px]">
                  {result.based_on?.bank?.length > 0 ? (
                    <ul className="text-sm space-y-2">
                      {result.based_on.bank.map((fact: any, i: number) => (
                        <li key={i} className="text-foreground">
                          {fact.text} <span className="text-muted-foreground">({fact.score?.toFixed(2)})</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-muted-foreground text-sm">None</p>
                  )}
                </div>
              </div>

              <div>
                <h4 className="mt-0 mb-2.5 text-purple-700 font-semibold">Opinions (Beliefs)</h4>
                <div className="bg-purple-50 p-4 rounded border-2 border-purple-700 min-h-[100px]">
                  {result.based_on?.opinion?.length > 0 ? (
                    <ul className="text-sm space-y-2">
                      {result.based_on.opinion.map((fact: any, i: number) => (
                        <li key={i} className="text-foreground">
                          {fact.text} <span className="text-muted-foreground">({fact.score?.toFixed(2)})</span>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <p className="text-muted-foreground text-sm">None</p>
                  )}
                </div>
              </div>
            </div>
          </div>

          {result.new_opinions && result.new_opinions.length > 0 && (
            <div className="mt-8 bg-green-50 p-5 rounded-lg border-2 border-green-500">
              <h3 className="mt-0 text-green-800 border-b-2 border-green-500 pb-2.5 font-bold">✨ New Opinions Formed</h3>
              <div className="mt-4 space-y-2">
                {result.new_opinions.map((opinion: any, i: number) => (
                  <div key={i} className="p-3 bg-card rounded border border-green-300">
                    <div className="font-semibold text-foreground">{opinion.text}</div>
                    <div className="text-sm text-muted-foreground">Confidence: {opinion.confidence?.toFixed(2)}</div>
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
