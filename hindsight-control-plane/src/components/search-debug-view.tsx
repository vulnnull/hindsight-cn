'use client';

import { useState } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Search, Clock, Zap, ChevronRight, Database, FileText, Users } from 'lucide-react';
import JsonView from 'react18-json-view';
import 'react18-json-view/src/style.css';
import { MemoryDetailPanel } from './memory-detail-panel';

type FactType = 'world' | 'experience' | 'opinion';
type Budget = 'low' | 'mid' | 'high';
type ViewMode = 'results' | 'trace' | 'json';

export function SearchDebugView() {
  const { currentBank } = useBank();

  // Query state
  const [query, setQuery] = useState('');
  const [factTypes, setFactTypes] = useState<FactType[]>(['world']);
  const [budget, setBudget] = useState<Budget>('mid');
  const [maxTokens, setMaxTokens] = useState(4096);
  const [queryDate, setQueryDate] = useState('');
  const [includeChunks, setIncludeChunks] = useState(false);
  const [includeEntities, setIncludeEntities] = useState(false);

  // Results state
  const [results, setResults] = useState<any[] | null>(null);
  const [entities, setEntities] = useState<any[] | null>(null);
  const [chunks, setChunks] = useState<any[] | null>(null);
  const [trace, setTrace] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>('results');
  const [selectedMemory, setSelectedMemory] = useState<any | null>(null);

  const runSearch = async () => {
    if (!currentBank) {
      alert('Please select a memory bank first');
      return;
    }

    if (!query || factTypes.length === 0) {
      if (factTypes.length === 0) {
        alert('Please select at least one fact type');
      }
      return;
    }

    setLoading(true);

    try {
      const requestBody: any = {
        bank_id: currentBank,
        query: query,
        types: factTypes,
        budget: budget,
        max_tokens: maxTokens,
        trace: true,
        include: {
          entities: includeEntities ? { max_tokens: 500 } : null,
          chunks: includeChunks ? { max_tokens: 8192 } : null
        },
        ...(queryDate && { query_timestamp: queryDate })
      };

      const data: any = await client.recall(requestBody);

      setResults(data.results || []);
      setEntities(data.entities || null);
      setChunks(data.chunks || null);
      setTrace(data.trace || null);
      setViewMode('results');
    } catch (error) {
      console.error('Error running search:', error);
      alert('Error running search: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const toggleFactType = (ft: FactType) => {
    setFactTypes(prev =>
      prev.includes(ft)
        ? prev.filter(t => t !== ft)
        : [...prev, ft]
    );
  };

  if (!currentBank) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex flex-col items-center justify-center py-16">
          <Database className="h-12 w-12 text-muted-foreground mb-4" />
          <h3 className="text-xl font-semibold mb-2">No Bank Selected</h3>
          <p className="text-muted-foreground">Select a memory bank to start recalling.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search Input */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="What would you like to recall?"
                className="pl-10 h-12 text-lg"
                onKeyDown={(e) => e.key === 'Enter' && runSearch()}
              />
            </div>
            <Button
              onClick={runSearch}
              disabled={loading || !query}
              className="h-12 px-8"
            >
              {loading ? 'Searching...' : 'Recall'}
            </Button>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-6 mt-4 pt-4 border-t">
            {/* Fact Types */}
            <div className="flex items-center gap-4">
              <span className="text-sm font-medium text-muted-foreground">Types:</span>
              <div className="flex gap-3">
                {(['world', 'experience', 'opinion'] as FactType[]).map((ft) => (
                  <label key={ft} className="flex items-center gap-2 cursor-pointer">
                    <Checkbox
                      checked={factTypes.includes(ft)}
                      onCheckedChange={() => toggleFactType(ft)}
                    />
                    <span className="text-sm capitalize">{ft}</span>
                  </label>
                ))}
              </div>
            </div>

            <div className="h-6 w-px bg-border" />

            {/* Budget */}
            <div className="flex items-center gap-2">
              <Zap className="h-4 w-4 text-muted-foreground" />
              <Select value={budget} onValueChange={(v) => setBudget(v as Budget)}>
                <SelectTrigger className="w-24 h-8">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">Low</SelectItem>
                  <SelectItem value="mid">Mid</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Max Tokens */}
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Tokens:</span>
              <Input
                type="number"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-24 h-8"
              />
            </div>

            {/* Query Date */}
            <div className="flex items-center gap-2">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <Input
                type="datetime-local"
                value={queryDate}
                onChange={(e) => setQueryDate(e.target.value)}
                className="h-8"
                placeholder="Query date"
              />
            </div>

            <div className="h-6 w-px bg-border" />

            {/* Include options */}
            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={includeChunks}
                  onCheckedChange={(c) => setIncludeChunks(c as boolean)}
                />
                <FileText className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Chunks</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <Checkbox
                  checked={includeEntities}
                  onCheckedChange={(c) => setIncludeEntities(c as boolean)}
                />
                <Users className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm">Entities</span>
              </label>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Results */}
      {loading && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4" />
            <p className="text-muted-foreground">Searching memories...</p>
          </CardContent>
        </Card>
      )}

      {!loading && results && (
        <div className="space-y-4">
          {/* Summary Stats */}
          {trace?.summary && (
            <div className="flex items-center gap-6 text-sm">
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Results:</span>
                <span className="font-semibold">{results.length}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Duration:</span>
                <span className="font-semibold">{trace.summary.total_duration_seconds?.toFixed(2)}s</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-muted-foreground">Nodes visited:</span>
                <span className="font-semibold">{trace.summary.total_nodes_visited}</span>
              </div>

              <div className="flex-1" />

              {/* View Mode Tabs */}
              <div className="flex gap-1 bg-muted p-1 rounded-lg">
                {(['results', 'trace', 'json'] as ViewMode[]).map((mode) => (
                  <button
                    key={mode}
                    onClick={() => setViewMode(mode)}
                    className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                      viewMode === mode
                        ? 'bg-background shadow-sm'
                        : 'text-muted-foreground hover:text-foreground'
                    }`}
                  >
                    {mode === 'results' ? 'Results' : mode === 'trace' ? 'Trace' : 'JSON'}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results View */}
          {viewMode === 'results' && (
            <div className="space-y-3">
              {results.length === 0 ? (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Search className="h-12 w-12 text-muted-foreground mb-4" />
                    <p className="text-muted-foreground">No memories found for this query.</p>
                  </CardContent>
                </Card>
              ) : (
                results.map((result: any, idx: number) => {
                  const visit = trace?.visits?.find((v: any) => v.node_id === result.id);
                  const score = visit ? visit.weights.final_weight : result.score || 0;

                  return (
                    <Card
                      key={idx}
                      className="cursor-pointer hover:border-primary/50 transition-colors"
                      onClick={() => setSelectedMemory(result)}
                    >
                      <CardContent className="py-4">
                        <div className="flex items-start gap-4">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="text-sm font-semibold text-primary">{idx + 1}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-foreground">{result.text}</p>
                            <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                              <span className="px-2 py-0.5 rounded bg-muted capitalize">{result.type || 'world'}</span>
                              {result.context && (
                                <span className="truncate max-w-xs">{result.context}</span>
                              )}
                              {result.occurred_start && (
                                <span>{new Date(result.occurred_start).toLocaleDateString()}</span>
                              )}
                            </div>
                          </div>
                          <div className="flex-shrink-0 text-right">
                            <div className="text-sm font-semibold">{score.toFixed(3)}</div>
                            <div className="text-xs text-muted-foreground">score</div>
                          </div>
                          <ChevronRight className="h-5 w-5 text-muted-foreground flex-shrink-0" />
                        </div>
                      </CardContent>
                    </Card>
                  );
                })
              )}
            </div>
          )}

          {/* Trace View */}
          {viewMode === 'trace' && trace && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Recall Trace</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Retrieval Methods */}
                {trace.retrieval_results && (
                  <div>
                    <h4 className="font-semibold mb-3">Retrieval Methods</h4>
                    <div className="grid grid-cols-2 gap-4">
                      {trace.retrieval_results.map((method: any, idx: number) => (
                        <div key={idx} className="p-4 rounded-lg bg-muted/50">
                          <div className="flex items-center justify-between mb-2">
                            <span className="font-medium capitalize">{method.method_name}</span>
                            <span className="text-sm text-muted-foreground">
                              {method.duration_seconds?.toFixed(3)}s
                            </span>
                          </div>
                          <div className="text-2xl font-bold">{method.results?.length || 0}</div>
                          <div className="text-xs text-muted-foreground">results</div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* RRF Merge */}
                {trace.rrf_merged && (
                  <div>
                    <h4 className="font-semibold mb-3">RRF Merge</h4>
                    <div className="p-4 rounded-lg bg-muted/50">
                      <div className="text-2xl font-bold">{trace.rrf_merged.length}</div>
                      <div className="text-xs text-muted-foreground">candidates after fusion</div>
                    </div>
                  </div>
                )}

                {/* Reranking */}
                {trace.reranked && (
                  <div>
                    <h4 className="font-semibold mb-3">Reranking</h4>
                    <div className="p-4 rounded-lg bg-muted/50">
                      <div className="text-2xl font-bold">{trace.reranked.length}</div>
                      <div className="text-xs text-muted-foreground">results after cross-encoder</div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* JSON View */}
          {viewMode === 'json' && (
            <Card>
              <CardHeader>
                <CardTitle className="text-lg">Raw Response</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="bg-muted p-4 rounded-lg overflow-auto max-h-[600px]">
                  <JsonView
                    src={{
                      results,
                      ...(entities && { entities }),
                      ...(chunks && { chunks }),
                      trace
                    }}
                    collapsed={2}
                    theme="default"
                  />
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      )}

      {/* Empty State */}
      {!loading && !results && (
        <Card className="border-dashed">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Search className="h-12 w-12 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Ready to Recall</h3>
            <p className="text-muted-foreground text-center max-w-md">
              Enter a query above to search through your memories. Use filters to narrow down by fact type, budget, and more.
            </p>
          </CardContent>
        </Card>
      )}

      {/* Memory Detail Panel */}
      {selectedMemory && (
        <div className="fixed right-0 top-0 h-screen w-[420px] bg-card border-l shadow-2xl z-50 overflow-y-auto">
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
