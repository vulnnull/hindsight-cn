'use client';

import { useState } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';

type Phase = 'retrieval' | 'rrf' | 'rerank' | 'final';
type RetrievalMethod = 'semantic' | 'bm25' | 'graph' | 'temporal';
type FactType = 'world' | 'bank' | 'opinion';

interface SearchPane {
  id: number;
  query: string;
  factTypes: FactType[];
  thinkingBudget: number;
  maxTokens: number;
  results: any[] | null;
  trace: any | null;
  loading: boolean;
  currentPhase: Phase;
  currentRetrievalMethod: RetrievalMethod;
  currentRetrievalFactType: FactType | null;
}

export function SearchDebugView() {
  const { currentBank } = useBank();
  const [panes, setPanes] = useState<SearchPane[]>([
    {
      id: 1,
      query: '',
      factTypes: ['world'],
      thinkingBudget: 100,
      maxTokens: 4096,
      results: null,
      trace: null,
      loading: false,
      currentPhase: 'retrieval',
      currentRetrievalMethod: 'semantic',
      currentRetrievalFactType: null,
    },
  ]);
  const [nextPaneId, setNextPaneId] = useState(2);

  const addPane = () => {
    setPanes([
      ...panes,
      {
        id: nextPaneId,
        query: '',
        factTypes: ['world'],
        thinkingBudget: 100,
        maxTokens: 4096,
        results: null,
        trace: null,
        loading: false,
        currentPhase: 'retrieval',
        currentRetrievalMethod: 'semantic',
        currentRetrievalFactType: null,
      },
    ]);
    setNextPaneId(nextPaneId + 1);
  };

  const removePane = (id: number) => {
    if (panes.length > 1) {
      setPanes(panes.filter((p) => p.id !== id));
    }
  };

  const updatePane = (id: number, updates: Partial<SearchPane>) => {
    setPanes(panes.map((p) => (p.id === id ? { ...p, ...updates } : p)));
  };

  const runSearch = async (paneId: number) => {
    if (!currentBank) {
      alert('Please select a memory bank first');
      return;
    }

    const pane = panes.find((p) => p.id === paneId);
    if (!pane || !pane.query || pane.factTypes.length === 0) {
      if (pane?.factTypes.length === 0) {
        alert('Please select at least one fact type');
      }
      return;
    }

    updatePane(paneId, { loading: true });

    try {
      // Always pass fact types as array for consistent behavior
      // Map numeric budget to budget level
      const budgetValue = pane.thinkingBudget <= 30 ? 'low' : pane.thinkingBudget <= 70 ? 'mid' : 'high';
      const data: any = await client.recall({
        bank_id: currentBank,
        query: pane.query,
        types: pane.factTypes,
        budget: budgetValue,
        max_tokens: pane.maxTokens,
        trace: true,
      });

      // Set default fact type for retrieval view (first selected fact type)
      const defaultFactType = pane.currentRetrievalFactType || pane.factTypes[0];

      updatePane(paneId, {
        results: data.results || [],
        trace: data.trace || null,
        loading: false,
        currentRetrievalFactType: defaultFactType,
      });
    } catch (error) {
      console.error('Error running search:', error);
      alert('Error running search: ' + (error as Error).message);
      updatePane(paneId, { loading: false });
    }
  };

  const renderRetrievalResults = (pane: SearchPane) => {
    if (!pane.trace || !pane.trace.retrieval_results) {
      return <div className="p-5 text-center text-muted-foreground">No retrieval data available</div>;
    }

    // Filter by retrieval method
    const methodData = pane.trace.retrieval_results.find(
      (m: any) => m.method_name === pane.currentRetrievalMethod
    );

    if (!methodData || !methodData.results || methodData.results.length === 0) {
      return (
        <div className="p-5 text-center text-muted-foreground">
          No results from this retrieval method
        </div>
      );
    }

    return (
      <div className="p-4 overflow-auto">
        <h3 className="text-base font-bold mb-2 text-foreground">
          {methodData.method_name.toUpperCase()} Retrieval
          {' '}({methodData.results.length} results, {methodData.duration_seconds?.toFixed(3)}s)
        </h3>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="bg-card border-2 border-primary">
              <th className="p-2 text-left border border-border text-card-foreground">Rank</th>
              <th className="p-2 text-left border border-border text-card-foreground">Text</th>
              <th className="p-2 text-left border border-border text-card-foreground">Score</th>
            </tr>
          </thead>
          <tbody>
            {methodData.results.map((result: any, idx: number) => (
              <tr key={idx} className="border border-border bg-background">
                <td className="p-2 border border-border font-bold">#{result.rank}</td>
                <td className="p-2 border border-border max-w-md">{result.text}</td>
                <td className="p-2 border border-border">{result.score?.toFixed(4)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  const renderRRFMerge = (pane: SearchPane) => {
    if (!pane.trace || !pane.trace.rrf_merged || pane.trace.rrf_merged.length === 0) {
      return <div className="p-5 text-center text-muted-foreground">No RRF merge data available</div>;
    }

    return (
      <div className="p-4 overflow-auto">
        <h3 className="text-base font-bold mb-2 text-foreground">
          RRF Merge Results ({pane.trace.rrf_merged.length} candidates)
          {pane.factTypes.length > 1 && (
            <span className="ml-2 text-sm font-normal bg-primary/20 px-2 py-0.5 rounded">
              Unified across all fact types
            </span>
          )}
        </h3>
        <p className="text-xs text-muted-foreground mb-3">
          Reciprocal Rank Fusion combines rankings from different retrieval methods
          {pane.factTypes.length > 1 ? ' and fact types' : ''}.
        </p>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="bg-card border-2 border-primary">
              <th className="p-2 text-left border border-border text-card-foreground">RRF Rank</th>
              <th className="p-2 text-left border border-border text-card-foreground">Text</th>
              <th className="p-2 text-left border border-border text-card-foreground">RRF Score</th>
              <th className="p-2 text-left border border-border text-card-foreground">Source Ranks</th>
            </tr>
          </thead>
          <tbody>
            {pane.trace.rrf_merged.map((result: any, idx: number) => {
              const sourceRanks = Object.entries(result.source_ranks || {})
                .map(([method, rank]) => `${method}: #${rank}`)
                .join(', ');

              return (
                <tr key={idx} className="border border-border bg-background">
                  <td className="p-2 border border-border font-bold">
                    #{result.final_rrf_rank}
                  </td>
                  <td className="p-2 border border-border max-w-md">{result.text}</td>
                  <td className="p-2 border border-border">{result.rrf_score?.toFixed(4)}</td>
                  <td className="p-2 border border-border text-xs">{sourceRanks}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  const renderReranking = (pane: SearchPane) => {
    if (!pane.trace || !pane.trace.reranked || pane.trace.reranked.length === 0) {
      return <div className="p-5 text-center text-muted-foreground">No reranking data available</div>;
    }

    return (
      <div className="p-4 overflow-auto">
        <h3 className="text-base font-bold mb-2 text-foreground">
          Reranking Results ({pane.trace.reranked.length} results)
          {pane.factTypes.length > 1 && (
            <span className="ml-2 text-sm font-normal bg-primary/20 px-2 py-0.5 rounded">
              Unified across all fact types
            </span>
          )}
        </h3>
        <p className="text-xs text-muted-foreground mb-3">
          Cross-encoder reranker adjusts scores based on semantic relevance.{' '}
          <span className="bg-secondary/30 px-2 py-0.5 rounded">Highlight</span> = rank improved
          vs RRF
        </p>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="bg-card border-2 border-primary">
              <th className="p-2 text-left border border-border text-card-foreground">Rerank</th>
              <th className="p-2 text-left border border-border text-card-foreground">RRF Rank</th>
              <th className="p-2 text-left border border-border text-card-foreground">Change</th>
              <th className="p-2 text-left border border-border text-card-foreground">Text</th>
              <th className="p-2 text-left border border-border text-card-foreground">Score</th>
              <th className="p-2 text-left border border-border text-card-foreground">Components</th>
            </tr>
          </thead>
          <tbody>
            {pane.trace.reranked.map((result: any, idx: number) => {
              const improved = result.rank_change > 0;
              const rowBg = improved ? 'bg-secondary/20' : 'bg-background';
              const changeDisplay =
                result.rank_change > 0
                  ? `↑${result.rank_change}`
                  : result.rank_change < 0
                  ? `↓${Math.abs(result.rank_change)}`
                  : '=';
              const changeColor =
                result.rank_change > 0
                  ? 'text-green-700'
                  : result.rank_change < 0
                  ? 'text-red-700'
                  : 'text-gray-600';

              const components = Object.entries(result.score_components || {})
                .map(([key, val]: [string, any]) => `${key.replace('_', ' ')}: ${val.toFixed(3)}`)
                .join(', ');

              return (
                <tr key={idx} className={`border border-border ${rowBg}`}>
                  <td className="p-2 border border-border font-bold">#{result.rerank_rank}</td>
                  <td className="p-2 border border-border">#{result.rrf_rank}</td>
                  <td className={`p-2 border border-border font-bold ${changeColor}`}>
                    {changeDisplay}
                  </td>
                  <td className="p-2 border border-border max-w-sm">{result.text}</td>
                  <td className="p-2 border border-border font-bold">
                    {result.rerank_score?.toFixed(4)}
                  </td>
                  <td className="p-2 border border-border text-xs">{components}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  const renderFinalResults = (pane: SearchPane) => {
    if (!pane.results || pane.results.length === 0) {
      return <div className="p-5 text-center text-muted-foreground">No final results</div>;
    }

    const calculateRanks = (values: number[]) => {
      const indexed = values.map((val, idx) => ({ idx, val }));
      indexed.sort((a, b) => b.val - a.val);
      const ranks = new Map();
      indexed.forEach((item, rank) => {
        ranks.set(item.idx, rank + 1);
      });
      return ranks;
    };

    const frequencies = pane.results.map((result: any) => {
      const visit = pane.trace?.visits?.find((v: any) => v.node_id === result.id);
      return visit ? visit.weights.frequency || 0 : 0;
    });

    const frequencyRanks = calculateRanks(frequencies);

    return (
      <div className="p-4 overflow-auto">
        <h3 className="text-base font-bold mb-2 text-foreground">
          Final Results ({pane.results.length} memories)
        </h3>
        <p className="text-xs text-muted-foreground mb-3">
          Query: &quot;{pane.trace?.query?.query_text || pane.query}&quot;
        </p>
        <table className="w-full border-collapse text-xs">
          <thead>
            <tr className="bg-card border-2 border-primary">
              <th className="p-2 text-left border border-border text-card-foreground">Rank</th>
              <th className="p-2 text-left border border-border text-card-foreground">Text</th>
              <th className="p-2 text-left border border-border text-card-foreground">Context</th>
              <th className="p-2 text-left border border-border text-card-foreground">Occurred</th>
              <th className="p-2 text-left border border-border text-card-foreground">Mentioned</th>
              <th className="p-2 text-left border border-border text-card-foreground" title="Final weighted score">
                Final Score
              </th>
              <th className="p-2 text-left border border-border text-card-foreground" title="Frequency boost">
                Frequency
              </th>
            </tr>
          </thead>
          <tbody>
            {pane.results.map((result: any, idx: number) => {
              const visit = pane.trace?.visits?.find((v: any) => v.node_id === result.id);
              const finalScore = visit ? visit.weights.final_weight : result.score || 0;
              const frequency = visit ? visit.weights.frequency || 0 : 0;

              // Format temporal range
              let occurredDisplay = 'N/A';
              if (result.occurred_start && result.occurred_end) {
                const start = new Date(result.occurred_start).toLocaleDateString();
                const end = new Date(result.occurred_end).toLocaleDateString();
                occurredDisplay = start === end ? start : `${start} - ${end}`;
              } else if (result.event_date) {
                occurredDisplay = new Date(result.event_date).toLocaleDateString();
              }

              const mentionedDisplay = result.mentioned_at
                ? new Date(result.mentioned_at).toLocaleDateString()
                : 'N/A';

              return (
                <tr key={idx} className="border border-border bg-background">
                  <td className="p-2 border border-border font-bold">#{idx + 1}</td>
                  <td className="p-2 border border-border max-w-xs">{result.text}</td>
                  <td className="p-2 border border-border max-w-32">
                    {result.context || 'N/A'}
                  </td>
                  <td className="p-2 border border-border whitespace-nowrap">
                    {occurredDisplay}
                  </td>
                  <td className="p-2 border border-border whitespace-nowrap">
                    {mentionedDisplay}
                  </td>
                  <td className="p-2 border border-border font-bold">
                    {finalScore.toFixed(4)}
                  </td>
                  <td className="p-2 border border-border">
                    {frequency.toFixed(4)}{' '}
                    <span className="text-muted-foreground text-xs">(#{frequencyRanks.get(idx)})</span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    );
  };

  if (!currentBank) {
    return (
      <div className="p-10 text-center text-muted-foreground bg-muted rounded-lg">
        <h3 className="text-xl font-semibold mb-2">No Bank Selected</h3>
        <p>Please select a memory bank from the dropdown above to use recall debug.</p>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-4">
        <button
          onClick={addPane}
          className="px-5 py-2 bg-secondary text-secondary-foreground rounded font-bold text-sm hover:opacity-90"
        >
          + Add Recall Pane
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {panes.map((pane) => (
          <div key={pane.id} className="border-2 border-primary rounded-lg overflow-hidden flex flex-col shadow-md">
            {/* Header */}
            <div className="bg-card p-2.5 border-b-2 border-primary font-bold flex justify-between items-center">
              <span className="text-card-foreground">Recall Trace #{pane.id}</span>
              {panes.length > 1 && (
                <button
                  onClick={() => removePane(pane.id)}
                  className="px-3 py-1 bg-destructive text-destructive-foreground rounded text-xs hover:opacity-90"
                >
                  Remove
                </button>
              )}
            </div>

            {/* Recall Controls */}
            <div className="p-2.5 bg-accent border-b-2 border-primary">
              <div className="flex gap-2 flex-wrap items-end">
                <div>
                  <label className="block text-xs font-bold mb-1 text-accent-foreground">Query:</label>
                  <input
                    type="text"
                    value={pane.query}
                    onChange={(e) => updatePane(pane.id, { query: e.target.value })}
                    placeholder="Enter recall query..."
                    className="w-64 px-2 py-1 border-2 border-border bg-background text-foreground rounded text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                    onKeyDown={(e) => e.key === 'Enter' && runSearch(pane.id)}
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold mb-1 text-accent-foreground">Fact Types:</label>
                  <div className="flex gap-3">
                    {(['world', 'bank', 'opinion'] as FactType[]).map((ft) => (
                      <label key={ft} className="flex items-center gap-1 cursor-pointer">
                        <input
                          type="checkbox"
                          checked={pane.factTypes.includes(ft)}
                          onChange={(e) => {
                            const newFactTypes = e.target.checked
                              ? [...pane.factTypes, ft]
                              : pane.factTypes.filter((t) => t !== ft);
                            updatePane(pane.id, { factTypes: newFactTypes });
                          }}
                          className="cursor-pointer"
                        />
                        <span className="text-xs">{ft.charAt(0).toUpperCase() + ft.slice(1)}</span>
                      </label>
                    ))}
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-bold mb-1 text-accent-foreground">Budget:</label>
                  <input
                    type="number"
                    value={pane.thinkingBudget}
                    onChange={(e) =>
                      updatePane(pane.id, { thinkingBudget: parseInt(e.target.value) })
                    }
                    className="w-16 px-2 py-1 border-2 border-border bg-background text-foreground rounded text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold mb-1 text-accent-foreground">Max Tokens:</label>
                  <input
                    type="number"
                    value={pane.maxTokens}
                    onChange={(e) =>
                      updatePane(pane.id, { maxTokens: parseInt(e.target.value) })
                    }
                    className="w-20 px-2 py-1 border-2 border-border bg-background text-foreground rounded text-xs focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <button
                  onClick={() => runSearch(pane.id)}
                  disabled={pane.loading || !pane.query}
                  className="px-4 py-1 bg-primary text-primary-foreground rounded font-bold text-xs hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {pane.loading ? 'Recalling...' : '🔍 Recall'}
                </button>
              </div>
            </div>

            {/* Status Bar */}
            {pane.trace?.summary && (
              <div className="px-4 py-2 bg-secondary/20 border-b-2 border-primary text-xs flex gap-4 flex-wrap">
                <span className="text-secondary-foreground font-bold">✓ Search complete</span>
                <span className="text-muted-foreground">|</span>
                <span>
                  <strong>Nodes visited:</strong> {pane.trace.summary.total_nodes_visited}
                </span>
                <span className="text-muted-foreground">|</span>
                <span>
                  <strong>Entry points:</strong> {pane.trace.summary.entry_points_found}
                </span>
                <span className="text-muted-foreground">|</span>
                <span>
                  <strong>Budget used:</strong> {pane.trace.summary.budget_used} /{' '}
                  {pane.trace.summary.budget_used + pane.trace.summary.budget_remaining}
                </span>
                <span className="text-muted-foreground">|</span>
                <span>
                  <strong>Results:</strong> {pane.trace.summary.results_returned}
                </span>
                <span className="text-muted-foreground">|</span>
                <span>
                  <strong>Duration:</strong> {pane.trace.summary.total_duration_seconds?.toFixed(2)}
                  s
                </span>
              </div>
            )}

            {!pane.trace?.summary && !pane.loading && (
              <div className="px-4 py-2 bg-muted border-b-2 border-primary text-xs text-muted-foreground">
                Ready to search
              </div>
            )}

            {/* Phase Controls */}
            {pane.trace && (
              <div className="p-2.5 bg-card border-b-2 border-primary flex gap-3">
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name={`phase-${pane.id}`}
                    checked={pane.currentPhase === 'retrieval'}
                    onChange={() => updatePane(pane.id, { currentPhase: 'retrieval' })}
                  />
                  <span className="text-xs font-bold">1. Retrieval</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name={`phase-${pane.id}`}
                    checked={pane.currentPhase === 'rrf'}
                    onChange={() => updatePane(pane.id, { currentPhase: 'rrf' })}
                  />
                  <span className="text-xs font-bold">2. RRF Merge</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name={`phase-${pane.id}`}
                    checked={pane.currentPhase === 'rerank'}
                    onChange={() => updatePane(pane.id, { currentPhase: 'rerank' })}
                  />
                  <span className="text-xs font-bold">3. Reranking</span>
                </label>
                <label className="flex items-center gap-1.5 cursor-pointer">
                  <input
                    type="radio"
                    name={`phase-${pane.id}`}
                    checked={pane.currentPhase === 'final'}
                    onChange={() => updatePane(pane.id, { currentPhase: 'final' })}
                  />
                  <span className="text-xs font-bold">4. Final Results</span>
                </label>
              </div>
            )}

            {/* Content */}
            <div className="bg-white overflow-auto" style={{ minHeight: '400px', maxHeight: '600px' }}>
              {pane.loading && (
                <div className="flex items-center justify-center h-96 text-gray-600">
                  <div>
                    <div className="text-4xl mb-2 text-center">🔄</div>
                    <div className="text-sm">Recalling...</div>
                  </div>
                </div>
              )}

              {!pane.loading && !pane.trace && (
                <div className="flex items-center justify-center h-96 text-gray-400">
                  <div className="text-center">
                    <div className="text-4xl mb-2">🔍</div>
                    <div className="text-sm">Enter a query and click Search</div>
                  </div>
                </div>
              )}

              {!pane.loading && pane.trace && (
                <>
                  {/* Retrieval Phase */}
                  {pane.currentPhase === 'retrieval' && (
                    <div>
                      {/* Fact Type Tabs (only show if multiple fact types) */}
                      {pane.factTypes.length > 1 && (
                        <div className="flex gap-0 border-b-2 border-primary bg-accent">
                          {pane.factTypes.map((ft) => (
                            <button
                              key={ft}
                              onClick={() =>
                                updatePane(pane.id, {
                                  currentRetrievalFactType: ft,
                                })
                              }
                              className={`px-4 py-2 text-xs font-bold border-r border-border hover:opacity-80 ${
                                pane.currentRetrievalFactType === ft
                                  ? 'bg-secondary text-secondary-foreground'
                                  : 'bg-card text-card-foreground'
                              }`}
                            >
                              {ft.charAt(0).toUpperCase() + ft.slice(1)} Facts
                            </button>
                          ))}
                        </div>
                      )}
                      {/* Retrieval Method Tabs */}
                      <div className="flex gap-0 border-b-2 border-primary bg-muted">
                        {['semantic', 'bm25', 'graph', 'temporal'].map((method) => (
                          <button
                            key={method}
                            onClick={() =>
                              updatePane(pane.id, {
                                currentRetrievalMethod: method as RetrievalMethod,
                              })
                            }
                            className={`px-4 py-2 text-xs font-bold border-r border-border hover:bg-accent ${
                              pane.currentRetrievalMethod === method
                                ? 'bg-primary text-primary-foreground'
                                : 'bg-background text-foreground'
                            }`}
                          >
                            {method.charAt(0).toUpperCase() + method.slice(1)}
                          </button>
                        ))}
                      </div>
                      {renderRetrievalResults(pane)}
                    </div>
                  )}

                  {/* RRF Merge Phase */}
                  {pane.currentPhase === 'rrf' && renderRRFMerge(pane)}

                  {/* Reranking Phase */}
                  {pane.currentPhase === 'rerank' && renderReranking(pane)}

                  {/* Final Results Phase */}
                  {pane.currentPhase === 'final' && renderFinalResults(pane)}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
