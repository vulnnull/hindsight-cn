'use client';

import { useState } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Info } from 'lucide-react';
import JsonView from 'react18-json-view';
import 'react18-json-view/src/style.css';
import { MemoryDetailPanel } from './memory-detail-panel';

type Phase = 'retrieval' | 'rrf' | 'rerank' | 'final' | 'json';
type RetrievalMethod = 'semantic' | 'bm25' | 'graph' | 'temporal';
type FactType = 'world' | 'experience' | 'opinion';

type Budget = 'low' | 'mid' | 'high';

// Helper component for column headers with tooltips
const ColumnHeader = ({ label, tooltip }: { label: string; tooltip: string }) => (
  <div className="flex items-center gap-1">
    <span>{label}</span>
    <Popover>
      <PopoverTrigger asChild>
        <button className="inline-flex cursor-help hover:text-foreground">
          <Info className="w-3 h-3 text-muted-foreground" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="text-xs max-w-xs" side="top">
        {tooltip}
      </PopoverContent>
    </Popover>
  </div>
);

interface SearchPane {
  id: number;
  query: string;
  factTypes: FactType[];
  budget: Budget;
  maxTokens: number;
  queryDate: string;
  includeChunks: boolean;
  includeEntities: boolean;
  results: any[] | null;
  entities: any[] | null;
  chunks: any[] | null;
  trace: any | null;
  loading: boolean;
  currentPhase: Phase;
  currentRetrievalMethod: RetrievalMethod;
  currentRetrievalFactType: FactType | null;
  showRawJson: boolean;
}

export function SearchDebugView() {
  const { currentBank } = useBank();
  const [panes, setPanes] = useState<SearchPane[]>([
    {
      id: 1,
      query: '',
      factTypes: ['world'],
      budget: 'mid',
      maxTokens: 4096,
      queryDate: '',
      includeChunks: false,
      includeEntities: false,
      results: null,
      entities: null,
      chunks: null,
      trace: null,
      loading: false,
      currentPhase: 'retrieval',
      currentRetrievalMethod: 'semantic',
      currentRetrievalFactType: null,
      showRawJson: false,
    },
  ]);
  const [nextPaneId, setNextPaneId] = useState(2);
  const [selectedMemory, setSelectedMemory] = useState<any | null>(null);

  const addPane = () => {
    setPanes([
      ...panes,
      {
        id: nextPaneId,
        query: '',
        factTypes: ['world'],
        budget: 'mid',
        maxTokens: 4096,
        queryDate: '',
        includeChunks: false,
        includeEntities: false,
        results: null,
        entities: null,
        chunks: null,
        trace: null,
        loading: false,
        currentPhase: 'retrieval',
        currentRetrievalMethod: 'semantic',
        currentRetrievalFactType: null,
        showRawJson: false,
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
      const requestBody: any = {
        bank_id: currentBank,
        query: pane.query,
        types: pane.factTypes,
        budget: pane.budget,
        max_tokens: pane.maxTokens,
        trace: true,
        include: {
          entities: pane.includeEntities ? { max_tokens: 500 } : null,
          chunks: pane.includeChunks ? { max_tokens: 8192 } : null
        },
        ...(pane.queryDate && { query_timestamp: pane.queryDate })
      };

      const data: any = await client.recall(requestBody);

      // Set default fact type for retrieval view (first selected fact type)
      const defaultFactType = pane.currentRetrievalFactType || pane.factTypes[0];

      updatePane(paneId, {
        results: data.results || [],
        entities: data.entities || null,
        chunks: data.chunks || null,
        trace: data.trace || null,
        loading: false,
        currentRetrievalFactType: defaultFactType,
        currentPhase: 'final',
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

    // Filter by fact type if multiple fact types are selected
    let filteredResults = methodData.results;
    if (pane.factTypes.length > 1 && pane.currentRetrievalFactType) {
      filteredResults = methodData.results.filter(
        (result: any) => result.fact_type === pane.currentRetrievalFactType
      );
    }

    // Get method-specific score description
    const scoreTooltips: Record<string, string> = {
      semantic: "Vector similarity score - measures conceptual similarity and paraphrasing (higher = more relevant)",
      bm25: "BM25 exact match score - measures keyword/phrase overlap for names, technical terms (higher = more exact matches)",
      graph: "Entity traversal score - measures connection strength through related entities and indirect relationships (higher = stronger connection)",
      temporal: "Time-filtered relevance score - combines temporal proximity with semantic relevance for time-based queries (higher = better match in timeframe)"
    };

    const scoreTooltip = scoreTooltips[pane.currentRetrievalMethod] || "Relevance score from this retrieval method (higher = more relevant)";

    return (
      <div className="p-4 overflow-auto">
        <h3 className="text-base font-bold mb-2 text-foreground">
          {methodData.method_name.toUpperCase()} Retrieval
          {pane.currentRetrievalFactType && pane.factTypes.length > 1 && (
            <span className="ml-2 text-sm font-normal bg-primary/20 px-2 py-0.5 rounded">
              {pane.currentRetrievalFactType} facts only
            </span>
          )}
          {' '}({filteredResults.length} results{pane.factTypes.length > 1 && ` of ${methodData.results.length}`}, {methodData.duration_seconds?.toFixed(3)}s)
        </h3>
        <Table>
          <TableHeader>
            <TableRow className="bg-card border-2 border-primary">
              <TableHead><ColumnHeader label="Rank" tooltip="Position in this retrieval method's results" /></TableHead>
              <TableHead><ColumnHeader label="Text" tooltip="The memory content" /></TableHead>
              {pane.factTypes.length > 1 && (
                <TableHead><ColumnHeader label="Type" tooltip="Fact type (world, experience, opinion)" /></TableHead>
              )}
              <TableHead><ColumnHeader label="Score" tooltip={scoreTooltip} /></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredResults.map((result: any, idx: number) => (
              <TableRow
                key={idx}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => setSelectedMemory(result)}
              >
                <TableCell className="font-bold">#{result.rank}</TableCell>
                <TableCell className="max-w-md">{result.text}</TableCell>
                {pane.factTypes.length > 1 && (
                  <TableCell>
                    <span className="px-2 py-0.5 rounded text-xs font-medium bg-primary/20">
                      {result.fact_type || 'unknown'}
                    </span>
                  </TableCell>
                )}
                <TableCell>{result.score?.toFixed(4)}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
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
        <Table>
          <TableHeader>
            <TableRow className="bg-card border-2 border-primary">
              <TableHead><ColumnHeader label="RRF Rank" tooltip="Final rank after combining all retrieval methods using Reciprocal Rank Fusion" /></TableHead>
              <TableHead><ColumnHeader label="Text" tooltip="The memory content" /></TableHead>
              <TableHead><ColumnHeader label="RRF Score" tooltip="Combined score from all retrieval methods (higher = found by more methods and ranked higher)" /></TableHead>
              <TableHead><ColumnHeader label="Source Ranks" tooltip="Original rank from each retrieval method (e.g., semantic: #3, bm25: #1)" /></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pane.trace.rrf_merged.map((result: any, idx: number) => {
              // Try multiple possible field names for source ranks
              const sourceRanksData = result.source_ranks || result.sourceRanks || result.ranks || {};
              const sourceRanks = Object.entries(sourceRanksData).length > 0
                ? Object.entries(sourceRanksData)
                    .map(([method, rank]) => `${method}: #${rank}`)
                    .join(', ')
                : 'N/A';

              return (
                <TableRow
                  key={idx}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => setSelectedMemory(result)}
                >
                  <TableCell className="font-bold">
                    #{result.final_rrf_rank || result.finalRrfRank || result.rank}
                  </TableCell>
                  <TableCell className="max-w-md">{result.text}</TableCell>
                  <TableCell>{(result.rrf_score || result.rrfScore || result.score)?.toFixed(4)}</TableCell>
                  <TableCell className="text-xs">{sourceRanks}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
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
        <Table>
          <TableHeader>
            <TableRow className="bg-card border-2 border-primary">
              <TableHead><ColumnHeader label="Rerank" tooltip="Final position after cross-encoder reranking" /></TableHead>
              <TableHead><ColumnHeader label="RRF Rank" tooltip="Position before reranking (from RRF merge)" /></TableHead>
              <TableHead><ColumnHeader label="Change" tooltip="How many positions this result moved (↑ = improved, ↓ = dropped)" /></TableHead>
              <TableHead><ColumnHeader label="Text" tooltip="The memory content" /></TableHead>
              <TableHead><ColumnHeader label="Final Score" tooltip="Combined score: cross-encoder + heuristics" /></TableHead>
              <TableHead><ColumnHeader label="Score Breakdown" tooltip="Individual components: cross_encoder (semantic), heuristic scores (recency, frequency, etc.)" /></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pane.trace.reranked.map((result: any, idx: number) => {
              const improved = result.rank_change > 0;
              const rowBg = improved ? 'bg-secondary/20' : '';
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

              // Format score components with better structure
              const components = result.score_components || {};
              const crossEncoder = components.cross_encoder || components.crossEncoder || 0;
              const heuristics = Object.entries(components)
                .filter(([key]) => key !== 'cross_encoder' && key !== 'crossEncoder')
                .map(([key, val]: [string, any]) => `${key}: ${val.toFixed(3)}`)
                .join(', ');

              const componentDisplay = (
                <div className="space-y-1">
                  <div className="font-semibold">Cross-Encoder: {crossEncoder.toFixed(4)}</div>
                  {heuristics && <div className="text-xs">Heuristics: {heuristics}</div>}
                </div>
              );

              return (
                <TableRow
                  key={idx}
                  className={`cursor-pointer hover:bg-muted/50 ${rowBg}`}
                  onClick={() => setSelectedMemory(result)}
                >
                  <TableCell className="font-bold">#{result.rerank_rank}</TableCell>
                  <TableCell>#{result.rrf_rank}</TableCell>
                  <TableCell className={`font-bold ${changeColor}`}>
                    {changeDisplay}
                  </TableCell>
                  <TableCell className="max-w-sm">{result.text}</TableCell>
                  <TableCell className="font-bold">
                    {result.rerank_score?.toFixed(4)}
                  </TableCell>
                  <TableCell className="text-xs">{componentDisplay}</TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
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
        <Table>
          <TableHeader>
            <TableRow className="bg-card border-2 border-primary">
              <TableHead><ColumnHeader label="Rank" tooltip="Final ranking position in the results" /></TableHead>
              <TableHead><ColumnHeader label="Text" tooltip="The memory content" /></TableHead>
              <TableHead><ColumnHeader label="Context" tooltip="Additional context about when/how this was mentioned" /></TableHead>
              <TableHead><ColumnHeader label="Occurred" tooltip="When this event happened (temporal range: start - end)" /></TableHead>
              <TableHead><ColumnHeader label="Mentioned" tooltip="When this memory was added to the system" /></TableHead>
              <TableHead><ColumnHeader label="Final Score" tooltip="Combined weighted score after all reranking and graph traversal" /></TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {pane.results.map((result: any, idx: number) => {
              const visit = pane.trace?.visits?.find((v: any) => v.node_id === result.id);
              const finalScore = visit ? visit.weights.final_weight : result.score || 0;

              // Format temporal range with clearer display
              let occurredDisplay: React.ReactNode = 'N/A';
              if (result.occurred_start && result.occurred_end) {
                const start = new Date(result.occurred_start).toLocaleDateString();
                const end = new Date(result.occurred_end).toLocaleDateString();
                occurredDisplay = start === end ? start : (
                  <div className="text-xs">
                    <div>Start: {start}</div>
                    <div>End: {end}</div>
                  </div>
                );
              } else if (result.event_date) {
                occurredDisplay = new Date(result.event_date).toLocaleDateString();
              }

              const mentionedDisplay = result.mentioned_at
                ? new Date(result.mentioned_at).toLocaleDateString()
                : 'N/A';

              return (
                <TableRow
                  key={idx}
                  className="cursor-pointer hover:bg-muted/50"
                  onClick={() => setSelectedMemory(result)}
                >
                  <TableCell className="font-bold">#{idx + 1}</TableCell>
                  <TableCell className="max-w-xs">{result.text}</TableCell>
                  <TableCell className="max-w-32">
                    {result.context || 'N/A'}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {occurredDisplay}
                  </TableCell>
                  <TableCell className="whitespace-nowrap">
                    {mentionedDisplay}
                  </TableCell>
                  <TableCell className="font-bold">
                    {finalScore.toFixed(4)}
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
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
      <div className="w-full">
        <div className="mb-4">
          <Button
            onClick={addPane}
            variant="secondary"
          >
            + Add Recall Pane
          </Button>
        </div>

        <div className="grid grid-cols-1 gap-5">
        {panes.map((pane) => (
          <div key={pane.id} className="border-2 border-primary rounded-lg overflow-hidden flex flex-col shadow-md">
            {/* Header */}
            <div className="bg-card p-2.5 border-b-2 border-primary font-bold flex justify-between items-center">
              <span className="text-card-foreground">Recall Trace #{pane.id}</span>
              {panes.length > 1 && (
                <Button
                  onClick={() => removePane(pane.id)}
                  variant="destructive"
                  size="sm"
                >
                  Remove
                </Button>
              )}
            </div>

            {/* Recall Controls */}
            <div className="p-4 bg-accent border-b-2 border-primary">
              <div className="space-y-4">
                {/* Query */}
                <div className="flex gap-4 items-end">
                  <div className="flex-1">
                    <label className="block text-sm font-bold mb-2 text-accent-foreground">Query:</label>
                    <Input
                      type="text"
                      value={pane.query}
                      onChange={(e) => updatePane(pane.id, { query: e.target.value })}
                      placeholder="Enter recall query..."
                      onKeyDown={(e) => e.key === 'Enter' && runSearch(pane.id)}
                    />
                  </div>
                  <Button
                    onClick={() => runSearch(pane.id)}
                    disabled={pane.loading || !pane.query}
                  >
                    {pane.loading ? 'Recalling...' : '🔍 Recall'}
                  </Button>
                </div>

                {/* Parameters Grid */}
                <div className="grid grid-cols-5 gap-4">
                  <div>
                    <label className="block text-sm font-bold mb-2 text-accent-foreground">Fact Types:</label>
                    <div className="flex flex-col gap-2">
                      {(['world', 'experience', 'opinion'] as FactType[]).map((ft) => (
                        <div key={ft} className="flex items-center gap-2">
                          <Checkbox
                            id={`${pane.id}-${ft}`}
                            checked={pane.factTypes.includes(ft)}
                            onCheckedChange={(checked) => {
                              const newFactTypes = checked
                                ? [...pane.factTypes, ft]
                                : pane.factTypes.filter((t) => t !== ft);
                              updatePane(pane.id, { factTypes: newFactTypes });
                            }}
                          />
                          <label htmlFor={`${pane.id}-${ft}`} className="text-sm cursor-pointer">
                            {ft.charAt(0).toUpperCase() + ft.slice(1)}
                          </label>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-bold mb-2 text-accent-foreground">Budget:</label>
                    <Select
                      value={pane.budget}
                      onValueChange={(value) =>
                        updatePane(pane.id, { budget: value as Budget })
                      }
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="mid">Mid</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-bold mb-2 text-accent-foreground">Max Tokens:</label>
                    <Input
                      type="number"
                      value={pane.maxTokens}
                      onChange={(e) =>
                        updatePane(pane.id, { maxTokens: parseInt(e.target.value) })
                      }
                      className="w-full"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-bold mb-2 text-accent-foreground">Query Date:</label>
                    <Input
                      type="datetime-local"
                      value={pane.queryDate}
                      onChange={(e) =>
                        updatePane(pane.id, { queryDate: e.target.value })
                      }
                      className="w-full"
                      placeholder="Optional"
                    />
                    <p className="text-xs text-muted-foreground mt-1">When is the query being asked</p>
                  </div>

                  <div>
                    <label className="block text-sm font-bold mb-2 text-accent-foreground">Include:</label>
                    <div className="flex flex-col gap-2">
                      <div className="flex items-center gap-2">
                        <Checkbox
                          id={`${pane.id}-chunks`}
                          checked={pane.includeChunks}
                          onCheckedChange={(checked) =>
                            updatePane(pane.id, { includeChunks: checked as boolean })
                          }
                        />
                        <label htmlFor={`${pane.id}-chunks`} className="text-sm cursor-pointer">
                          Chunks
                        </label>
                      </div>
                      <div className="flex items-center gap-2">
                        <Checkbox
                          id={`${pane.id}-entities`}
                          checked={pane.includeEntities}
                          onCheckedChange={(checked) =>
                            updatePane(pane.id, { includeEntities: checked as boolean })
                          }
                        />
                        <label htmlFor={`${pane.id}-entities`} className="text-sm cursor-pointer">
                          Entities
                        </label>
                      </div>
                    </div>
                  </div>
                </div>
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
              <div className="p-2.5 bg-card border-b-2 border-primary">
                <RadioGroup
                  value={pane.currentPhase}
                  onValueChange={(value) => updatePane(pane.id, { currentPhase: value as Phase })}
                  className="flex gap-3"
                >
                  <div className="flex items-center gap-1.5">
                    <RadioGroupItem value="retrieval" id={`phase-retrieval-${pane.id}`} />
                    <Label htmlFor={`phase-retrieval-${pane.id}`} className="text-xs font-bold cursor-pointer">
                      1. Retrieval
                    </Label>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <RadioGroupItem value="rrf" id={`phase-rrf-${pane.id}`} />
                    <Label htmlFor={`phase-rrf-${pane.id}`} className="text-xs font-bold cursor-pointer">
                      2. RRF Merge
                    </Label>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <RadioGroupItem value="rerank" id={`phase-rerank-${pane.id}`} />
                    <Label htmlFor={`phase-rerank-${pane.id}`} className="text-xs font-bold cursor-pointer">
                      3. Reranking
                    </Label>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <RadioGroupItem value="json" id={`phase-json-${pane.id}`} />
                    <Label htmlFor={`phase-json-${pane.id}`} className="text-xs font-bold cursor-pointer">
                      4. Raw JSON
                    </Label>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <RadioGroupItem value="final" id={`phase-final-${pane.id}`} />
                    <Label htmlFor={`phase-final-${pane.id}`} className="text-xs font-bold cursor-pointer">
                      5. Final Results
                    </Label>
                  </div>
                </RadioGroup>
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
                            <Button
                              key={ft}
                              variant={pane.currentRetrievalFactType === ft ? 'secondary' : 'ghost'}
                              onClick={() =>
                                updatePane(pane.id, {
                                  currentRetrievalFactType: ft,
                                })
                              }
                              className="px-4 py-2 text-xs font-bold border-r border-border rounded-none"
                            >
                              {ft.charAt(0).toUpperCase() + ft.slice(1)} Facts
                            </Button>
                          ))}
                        </div>
                      )}
                      {/* Retrieval Method Tabs */}
                      <div className="flex gap-0 border-b-2 border-primary bg-muted">
                        {['semantic', 'bm25', 'graph', 'temporal'].map((method) => (
                          <Button
                            key={method}
                            variant={pane.currentRetrievalMethod === method ? 'default' : 'ghost'}
                            onClick={() =>
                              updatePane(pane.id, {
                                currentRetrievalMethod: method as RetrievalMethod,
                              })
                            }
                            className="px-4 py-2 text-xs font-bold border-r border-border rounded-none"
                          >
                            {method.charAt(0).toUpperCase() + method.slice(1)}
                          </Button>
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

                  {/* Raw JSON Phase */}
                  {pane.currentPhase === 'json' && (
                    <div className="p-4 overflow-auto">
                      <h3 className="text-base font-bold mb-2 text-foreground">Raw JSON Response</h3>
                      <p className="text-xs text-muted-foreground mb-3">
                        Results from the API (trace data excluded)
                      </p>
                      <div className="bg-muted p-4 rounded border border-border overflow-auto max-h-[800px]">
                        <JsonView
                          src={{
                            results: pane.results,
                            ...(pane.entities && { entities: pane.entities }),
                            ...(pane.chunks && { chunks: pane.chunks }),
                          }}
                          collapsed={1}
                          theme="default"
                        />
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
        </div>
      </div>

      {/* Memory Detail Panel - Fixed on Right */}
      {selectedMemory && (
        <div className="fixed right-0 top-0 h-screen w-[420px] bg-card border-l-2 border-primary shadow-2xl z-50 overflow-y-auto animate-in slide-in-from-right duration-300 ease-out">
          <MemoryDetailPanel
            memory={selectedMemory}
            onClose={() => setSelectedMemory(null)}
            inPanel
          />
        </div>
      )}
    </div>
  );
}
