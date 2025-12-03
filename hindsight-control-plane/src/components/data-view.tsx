'use client';

import { useState, useEffect, useRef, useMemo } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import cytoscape from 'cytoscape';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Copy, Check, X, Calendar, ZoomIn, ZoomOut, ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight, FileText, Layers } from 'lucide-react';
import { MemoryDetailPanel } from './memory-detail-panel';

type FactType = 'world' | 'bank' | 'opinion';
type ViewMode = 'graph' | 'table' | 'timeline';

interface DataViewProps {
  factType: FactType;
}

export function DataView({ factType }: DataViewProps) {
  const { currentBank } = useBank();
  const [viewMode, setViewMode] = useState<ViewMode>('graph');
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [nodeLimit, setNodeLimit] = useState(50);
  const [layout, setLayout] = useState('circle');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [loadingDocument, setLoadingDocument] = useState(false);
  const [selectedChunk, setSelectedChunk] = useState<any>(null);
  const [loadingChunk, setLoadingChunk] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedGraphNode, setSelectedGraphNode] = useState<any>(null);
  const [selectedTableMemory, setSelectedTableMemory] = useState<any>(null);
  const itemsPerPage = 100;
  const cyRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(text);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const viewDocument = async (documentId: string) => {
    if (!currentBank || !documentId) return;

    setLoadingDocument(true);
    setSelectedDocument({ id: documentId });
    setSelectedChunk(null); // Clear chunk when viewing document

    try {
      const doc: any = await client.getDocument(documentId, currentBank);
      setSelectedDocument(doc);
    } catch (error) {
      console.error('Error loading document:', error);
      alert('Error loading document: ' + (error as Error).message);
      setSelectedDocument(null);
    } finally {
      setLoadingDocument(false);
    }
  };

  const viewChunk = async (chunkId: string) => {
    if (!chunkId) return;

    setLoadingChunk(true);
    setSelectedChunk({ chunk_id: chunkId });
    setSelectedDocument(null); // Clear document when viewing chunk

    try {
      const chunk: any = await client.getChunk(chunkId);
      setSelectedChunk(chunk);
    } catch (error) {
      console.error('Error loading chunk:', error);
      alert('Error loading chunk: ' + (error as Error).message);
      setSelectedChunk(null);
    } finally {
      setLoadingChunk(false);
    }
  };

  const loadData = async () => {
    if (!currentBank) return;

    setLoading(true);
    try {
      const graphData: any = await client.getGraph({
        bank_id: currentBank,
        type: factType,
      });
      console.log('Loaded graph data:', {
        total_units: graphData.total_units,
        nodes: graphData.nodes?.length,
        edges: graphData.edges?.length,
        table_rows: graphData.table_rows?.length,
      });
      setData(graphData);
    } catch (error) {
      console.error('Error loading data:', error);
      alert(`Error loading ${factType} data: ` + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const renderGraph = () => {
    if (!data || !containerRef.current || !data.nodes || !data.edges) return;

    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const limitedNodes = (data.nodes || []).slice(0, nodeLimit);
    const nodeIds = new Set(limitedNodes.map((n: any) => n.data.id));
    const limitedEdges = (data.edges || []).filter((e: any) =>
      nodeIds.has(e.data.source) && nodeIds.has(e.data.target)
    );

    const layouts: any = {
      circle: {
        name: 'circle',
        animate: false,
        radius: 300,
        spacingFactor: 1.5,
      },
      grid: {
        name: 'grid',
        animate: false,
        rows: Math.ceil(Math.sqrt(limitedNodes.length)),
        cols: Math.ceil(Math.sqrt(limitedNodes.length)),
        spacingFactor: 2,
      },
      cose: {
        name: 'cose',
        animate: false,
        nodeRepulsion: 15000,
        idealEdgeLength: 150,
        edgeElasticity: 100,
        nestingFactor: 1.2,
        gravity: 1,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0,
      },
    };

    cyRef.current = cytoscape({
      container: containerRef.current,
      elements: [
        ...limitedNodes.map((n: any) => ({ data: n.data })),
        ...limitedEdges.map((e: any) => ({ data: e.data })),
      ],
      style: [
        {
          selector: 'node',
          style: {
            'background-color': 'data(color)' as any,
            label: 'data(label)' as any,
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'font-weight': 'bold',
            'text-wrap': 'wrap',
            'text-max-width': '100px',
            width: 40,
            height: 40,
            'border-width': 2,
            'border-color': '#333',
          },
        },
        {
          selector: 'edge',
          style: {
            width: 1,
            'line-color': 'data(color)' as any,
            'line-style': 'data(lineStyle)' as any,
            'target-arrow-shape': 'triangle',
            'target-arrow-color': 'data(color)' as any,
            'curve-style': 'bezier',
            opacity: 0.6,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': 4,
            'border-color': '#000',
          },
        },
      ] as any,
      layout: layouts[layout] || layouts.circle,
    });

    // Add click handler for nodes
    cyRef.current.on('tap', 'node', (evt: any) => {
      const nodeId = evt.target.id();
      // Find the corresponding table row data
      const nodeData = data.table_rows?.find((row: any) => row.id === nodeId);
      if (nodeData) {
        setSelectedGraphNode(nodeData);
      }
    });

    // Click on background to deselect
    cyRef.current.on('tap', (evt: any) => {
      if (evt.target === cyRef.current) {
        setSelectedGraphNode(null);
      }
    });
  };

  useEffect(() => {
    if (viewMode === 'graph' && data) {
      renderGraph();
    }
  }, [viewMode, data, nodeLimit, layout]);

  // Reset to first page when search query changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchQuery]);

  // Auto-load data when component mounts or factType/currentBank changes
  useEffect(() => {
    if (currentBank) {
      loadData();
    }
  }, [factType, currentBank]);

  return (
    <div>
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="text-4xl mb-2">⏳</div>
            <div className="text-sm text-muted-foreground">Loading memories...</div>
          </div>
        </div>
      ) : data ? (
        <>
          <div className="flex items-center justify-between mb-6">
            <div className="text-sm text-muted-foreground">
              {data.total_units} total memories
            </div>
            <div className="flex items-center gap-2 bg-muted rounded-lg p-1">
              <button
                onClick={() => setViewMode('graph')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'graph'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Graph View
              </button>
              <button
                onClick={() => setViewMode('table')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'table'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Table View
              </button>
              <button
                onClick={() => setViewMode('timeline')}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  viewMode === 'timeline'
                    ? 'bg-background text-foreground shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                }`}
              >
                Timeline View
              </button>
            </div>
          </div>

          {viewMode === 'graph' && (
            <div className="flex gap-4">
              <div className={`relative transition-all ${selectedGraphNode ? 'w-2/3' : 'w-full'}`}>
                <div className="p-4 bg-card border-b-2 border-primary flex gap-4 items-center flex-wrap">
                  <div className="flex items-center gap-2">
                    <label className="font-semibold text-card-foreground">Limit nodes:</label>
                    <Input
                      type="number"
                      value={nodeLimit}
                      onChange={(e) => setNodeLimit(parseInt(e.target.value))}
                      min="10"
                      max="1000"
                      step="10"
                      className="w-20"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="font-semibold text-card-foreground">Layout:</label>
                    <Select value={layout} onValueChange={setLayout}>
                      <SelectTrigger className="w-[180px]">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="circle">Circle (fast)</SelectItem>
                        <SelectItem value="grid">Grid (fast)</SelectItem>
                        <SelectItem value="cose">Force-directed (slow)</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="text-sm text-muted-foreground ml-auto">
                    Click on a node to view details
                  </div>
                </div>
                <div ref={containerRef} className="w-full h-[800px] bg-background" />
                <div className="absolute top-20 left-5 bg-card p-4 border-2 border-primary rounded-lg shadow-lg max-w-[250px]">
                  <h3 className="font-bold mb-2 border-b-2 border-primary pb-1 text-card-foreground">Legend</h3>
                  <h4 className="font-bold mt-2 mb-1 text-sm text-card-foreground">Link Types:</h4>
                  <div className="flex items-center my-2">
                    <div className="w-8 h-0.5 mr-2.5 bg-cyan-500 border-t border-dashed border-cyan-500" />
                    <span className="text-sm"><strong>Temporal</strong></span>
                  </div>
                  <div className="flex items-center my-2">
                    <div className="w-8 h-0.5 mr-2.5 bg-pink-500" />
                    <span className="text-sm"><strong>Semantic</strong></span>
                  </div>
                  <div className="flex items-center my-2">
                    <div className="w-8 h-0.5 mr-2.5 bg-yellow-500" />
                    <span className="text-sm"><strong>Entity</strong></span>
                  </div>
                  <h4 className="font-bold mt-2 mb-1 text-sm">Nodes:</h4>
                  <div className="flex items-center my-2">
                    <div className="w-5 h-5 mr-2.5 bg-gray-300 border border-gray-500 rounded" />
                    <span className="text-sm">No entities</span>
                  </div>
                  <div className="flex items-center my-2">
                    <div className="w-5 h-5 mr-2.5 bg-blue-300 border border-gray-500 rounded" />
                    <span className="text-sm">1 entity</span>
                  </div>
                  <div className="flex items-center my-2">
                    <div className="w-5 h-5 mr-2.5 bg-blue-500 border border-gray-500 rounded" />
                    <span className="text-sm">2+ entities</span>
                  </div>
                </div>
              </div>

              {/* Memory Detail Panel for Graph View */}
              {selectedGraphNode && (
                <div className="w-1/3">
                  <MemoryDetailPanel
                    memory={selectedGraphNode}
                    onClose={() => setSelectedGraphNode(null)}
                    onViewDocument={(docId) => {
                      viewDocument(docId);
                      setSelectedGraphNode(null);
                      setViewMode('table');
                    }}
                    onViewChunk={(chunkId) => {
                      viewChunk(chunkId);
                      setSelectedGraphNode(null);
                      setViewMode('table');
                    }}
                  />
                </div>
              )}
            </div>
          )}

          {viewMode === 'table' && (
            <div className="flex gap-4">
              <div className={`transition-all ${selectedDocument || selectedChunk || selectedTableMemory ? 'w-2/3' : 'w-full'}`}>
                <div className="px-5 mb-4">
                  <Input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Search memories (text, context)..."
                    className="max-w-2xl"
                  />
                </div>
                <div className="px-5 pb-5">
                  {data.table_rows && data.table_rows.length > 0 ? (
                    (() => {
                      const filteredRows = data.table_rows.filter((row: any) => {
                        if (!searchQuery) return true;
                        const query = searchQuery.toLowerCase();
                        return (
                          row.text?.toLowerCase().includes(query) ||
                          row.context?.toLowerCase().includes(query)
                        );
                      });

                      const totalPages = Math.ceil(filteredRows.length / itemsPerPage);
                      const startIndex = (currentPage - 1) * itemsPerPage;
                      const endIndex = startIndex + itemsPerPage;
                      const paginatedRows = filteredRows.slice(startIndex, endIndex);

                      return (
                        <>
                          <div className="grid gap-3">
                            {paginatedRows.map((row: any, idx: number) => {
                              const occurredDisplay = row.occurred_start
                                ? new Date(row.occurred_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
                                : null;

                              return (
                                <div
                                  key={row.id || idx}
                                  onClick={() => setSelectedTableMemory(row)}
                                  className={`group p-4 bg-card border rounded-lg cursor-pointer transition-all hover:border-primary hover:shadow-md ${
                                    selectedTableMemory?.id === row.id ? 'border-primary ring-2 ring-primary/20' : 'border-border'
                                  }`}
                                >
                                  <div className="flex items-start gap-4">
                                    {/* Main content */}
                                    <div className="flex-1 min-w-0">
                                      <p className="text-sm text-foreground line-clamp-2 mb-2">
                                        {row.text}
                                      </p>
                                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-muted-foreground">
                                        {occurredDisplay && (
                                          <span className="flex items-center gap-1">
                                            <Calendar className="h-3 w-3" />
                                            {occurredDisplay}
                                          </span>
                                        )}
                                        {row.context && (
                                          <span className="truncate max-w-[200px]" title={row.context}>
                                            {row.context}
                                          </span>
                                        )}
                                        <span className="font-mono opacity-50" title={row.id}>
                                          {row.id.substring(0, 8)}...
                                        </span>
                                      </div>
                                      {row.entities && (
                                        <div className="flex gap-1 mt-2 flex-wrap">
                                          {row.entities.split(', ').slice(0, 5).map((entity: string, i: number) => (
                                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-secondary text-secondary-foreground">
                                              {entity}
                                            </span>
                                          ))}
                                          {row.entities.split(', ').length > 5 && (
                                            <span className="text-[10px] text-muted-foreground">
                                              +{row.entities.split(', ').length - 5}
                                            </span>
                                          )}
                                        </div>
                                      )}
                                    </div>

                                    {/* Action buttons */}
                                    <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                      {row.document_id && (
                                        <Button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            viewDocument(row.document_id);
                                          }}
                                          size="sm"
                                          variant="ghost"
                                          className="h-8 w-8 p-0"
                                          title="View Document"
                                        >
                                          <FileText className="h-4 w-4" />
                                        </Button>
                                      )}
                                      {row.chunk_id && (
                                        <Button
                                          onClick={(e) => {
                                            e.stopPropagation();
                                            viewChunk(row.chunk_id);
                                          }}
                                          size="sm"
                                          variant="ghost"
                                          className="h-8 w-8 p-0"
                                          title="View Chunk"
                                        >
                                          <Layers className="h-4 w-4" />
                                        </Button>
                                      )}
                                      <Button
                                        onClick={(e) => {
                                          e.stopPropagation();
                                          copyToClipboard(row.id);
                                        }}
                                        size="sm"
                                        variant="ghost"
                                        className="h-8 w-8 p-0"
                                        title="Copy ID"
                                      >
                                        {copiedId === row.id ? (
                                          <Check className="h-4 w-4 text-green-600" />
                                        ) : (
                                          <Copy className="h-4 w-4" />
                                        )}
                                      </Button>
                                    </div>
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {/* Pagination Controls */}
                          {totalPages > 1 && (
                            <div className="flex items-center justify-between mt-4 pt-4 border-t">
                              <div className="text-sm text-muted-foreground">
                                Showing {startIndex + 1} to {Math.min(endIndex, filteredRows.length)} of {filteredRows.length}
                              </div>
                              <div className="flex items-center gap-1">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setCurrentPage(1)}
                                  disabled={currentPage === 1}
                                  className="h-8 w-8 p-0"
                                >
                                  <ChevronsLeft className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                                  disabled={currentPage === 1}
                                  className="h-8 w-8 p-0"
                                >
                                  <ChevronLeft className="h-4 w-4" />
                                </Button>
                                <span className="text-sm px-3">
                                  {currentPage} / {totalPages}
                                </span>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                                  disabled={currentPage === totalPages}
                                  className="h-8 w-8 p-0"
                                >
                                  <ChevronRight className="h-4 w-4" />
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => setCurrentPage(totalPages)}
                                  disabled={currentPage === totalPages}
                                  className="h-8 w-8 p-0"
                                >
                                  <ChevronsRight className="h-4 w-4" />
                                </Button>
                              </div>
                            </div>
                          )}
                        </>
                      );
                    })()
                  ) : (
                    <div className="text-center py-12 text-muted-foreground">
                      {data.table_rows ? 'No memories match your search' : 'No memories found'}
                    </div>
                  )}
                </div>
              </div>

            {/* Memory Detail Panel for Table View */}
            {selectedTableMemory && !selectedDocument && !selectedChunk && (
              <div className="w-1/3 pr-5 pb-5">
                <MemoryDetailPanel
                  memory={selectedTableMemory}
                  onClose={() => setSelectedTableMemory(null)}
                  onViewDocument={(docId) => {
                    viewDocument(docId);
                    setSelectedTableMemory(null);
                  }}
                  onViewChunk={(chunkId) => {
                    viewChunk(chunkId);
                    setSelectedTableMemory(null);
                  }}
                />
              </div>
            )}

            {/* Document Detail Panel */}
            {selectedDocument && (
              <div className="w-1/3 pr-5 pb-5">
                <div className="bg-card border-2 border-primary rounded-lg p-4 sticky top-4 max-h-[calc(100vh-120px)] overflow-y-auto">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-card-foreground">Document Details</h3>
                      <p className="text-sm text-muted-foreground">View the original document text and metadata</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedDocument(null)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  {loadingDocument ? (
                    <div className="flex items-center justify-center py-20">
                      <div className="text-center">
                        <div className="text-4xl mb-2">⏳</div>
                        <div className="text-sm text-muted-foreground">Loading document...</div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="space-y-3">
                        <div className="p-3 bg-muted rounded-lg">
                          <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Document ID</div>
                          <div className="text-sm font-mono break-all">{selectedDocument.id}</div>
                        </div>
                        {selectedDocument.created_at && (
                          <div className="grid grid-cols-2 gap-3">
                            <div className="p-3 bg-muted rounded-lg">
                              <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Created</div>
                              <div className="text-sm">{new Date(selectedDocument.created_at).toLocaleString()}</div>
                            </div>
                            <div className="p-3 bg-muted rounded-lg">
                              <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Memory Units</div>
                              <div className="text-sm">{selectedDocument.memory_unit_count}</div>
                            </div>
                          </div>
                        )}
                        {selectedDocument.original_text && (
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Text Length</div>
                            <div className="text-sm">{selectedDocument.original_text.length.toLocaleString()} characters</div>
                          </div>
                        )}
                      </div>

                      {selectedDocument.original_text && (
                        <div>
                          <div className="text-sm font-bold text-foreground mb-2">Original Text</div>
                          <div className="p-4 bg-muted rounded-lg border border-border">
                            <pre className="text-sm whitespace-pre-wrap font-mono">{selectedDocument.original_text}</pre>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Chunk Detail Panel */}
            {selectedChunk && (
              <div className="w-1/3 pr-5 pb-5">
                <div className="bg-card border-2 border-primary rounded-lg p-4 sticky top-4 max-h-[calc(100vh-120px)] overflow-y-auto">
                  <div className="flex justify-between items-start mb-4">
                    <div>
                      <h3 className="text-lg font-bold text-card-foreground">Chunk Details</h3>
                      <p className="text-sm text-muted-foreground">View the chunk text and metadata</p>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => setSelectedChunk(null)}
                      className="h-8 w-8 p-0"
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>

                  {loadingChunk ? (
                    <div className="flex items-center justify-center py-20">
                      <div className="text-center">
                        <div className="text-4xl mb-2">⏳</div>
                        <div className="text-sm text-muted-foreground">Loading chunk...</div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4">
                      <div className="space-y-3">
                        <div className="p-3 bg-muted rounded-lg">
                          <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Chunk ID</div>
                          <div className="text-sm font-mono break-all">{selectedChunk.chunk_id}</div>
                        </div>
                        <div className="grid grid-cols-2 gap-3">
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Document ID</div>
                            <div className="text-sm font-mono break-all">{selectedChunk.document_id}</div>
                          </div>
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Chunk Index</div>
                            <div className="text-sm">{selectedChunk.chunk_index}</div>
                          </div>
                        </div>
                        {selectedChunk.created_at && (
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Created</div>
                            <div className="text-sm">{new Date(selectedChunk.created_at).toLocaleString()}</div>
                          </div>
                        )}
                        {selectedChunk.chunk_text && (
                          <div className="p-3 bg-muted rounded-lg">
                            <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Text Length</div>
                            <div className="text-sm">{selectedChunk.chunk_text.length.toLocaleString()} characters</div>
                          </div>
                        )}
                      </div>

                      {selectedChunk.chunk_text && (
                        <div>
                          <div className="text-sm font-bold text-foreground mb-2">Chunk Text</div>
                          <div className="p-4 bg-muted rounded-lg border border-border">
                            <pre className="text-sm whitespace-pre-wrap font-mono">{selectedChunk.chunk_text}</pre>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
          )}

          {viewMode === 'timeline' && (
            <TimelineView data={data} onViewDocument={viewDocument} />
          )}
        </>
      ) : (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="text-4xl mb-2">📊</div>
            <div className="text-sm text-muted-foreground">No data available</div>
          </div>
        </div>
      )}
    </div>
  );
}

// Timeline View Component - Custom compact timeline with zoom and navigation
type Granularity = 'year' | 'month' | 'week' | 'day';

function TimelineView({ data, onViewDocument }: { data: any; onViewDocument: (id: string) => void }) {
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [granularity, setGranularity] = useState<Granularity>('month');
  const [currentIndex, setCurrentIndex] = useState(0);
  const timelineRef = useRef<HTMLDivElement>(null);

  // Filter and sort items that have occurred_start dates
  const { sortedItems, itemsWithoutDates } = useMemo(() => {
    if (!data?.table_rows) return { sortedItems: [], itemsWithoutDates: [] };

    const withDates = data.table_rows
      .filter((row: any) => row.occurred_start)
      .sort((a: any, b: any) => {
        const dateA = new Date(a.occurred_start).getTime();
        const dateB = new Date(b.occurred_start).getTime();
        return dateA - dateB;
      });

    const withoutDates = data.table_rows.filter((row: any) => !row.occurred_start);

    // Debug logging
    console.log('Timeline data:', {
      total: data.table_rows.length,
      withDates: withDates.length,
      withoutDates: withoutDates.length,
      sampleWithDate: withDates[0],
      sampleWithoutDate: withoutDates[0]
    });

    return { sortedItems: withDates, itemsWithoutDates: withoutDates };
  }, [data]);

  // Group items by granularity
  const timelineGroups = useMemo(() => {
    if (sortedItems.length === 0) return [];

    const getGroupKey = (date: Date): string => {
      const year = date.getFullYear();
      const month = date.getMonth();
      const day = date.getDate();

      switch (granularity) {
        case 'year':
          return `${year}`;
        case 'month':
          return `${year}-${String(month + 1).padStart(2, '0')}`;
        case 'week':
          const startOfWeek = new Date(date);
          startOfWeek.setDate(day - date.getDay());
          return `${startOfWeek.getFullYear()}-W${String(Math.ceil((startOfWeek.getDate()) / 7)).padStart(2, '0')}-${String(startOfWeek.getMonth() + 1).padStart(2, '0')}-${String(startOfWeek.getDate()).padStart(2, '0')}`;
        case 'day':
          return `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      }
    };

    const getGroupLabel = (key: string, date: Date): string => {
      switch (granularity) {
        case 'year':
          return key;
        case 'month':
          return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
        case 'week':
          const endOfWeek = new Date(date);
          endOfWeek.setDate(date.getDate() + 6);
          return `${date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} - ${endOfWeek.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}`;
        case 'day':
          return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' });
      }
    };

    const groups: { [key: string]: { items: any[]; date: Date } } = {};
    sortedItems.forEach((row: any) => {
      const date = new Date(row.occurred_start);
      const key = getGroupKey(date);
      if (!groups[key]) {
        // For week, parse the start date from key
        let groupDate = date;
        if (granularity === 'week') {
          const parts = key.split('-');
          groupDate = new Date(parseInt(parts[0]), parseInt(parts[2]) - 1, parseInt(parts[3]));
        }
        groups[key] = { items: [], date: groupDate };
      }
      groups[key].items.push(row);
    });

    return Object.entries(groups)
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([key, { items, date }]) => ({
        key,
        label: getGroupLabel(key, date),
        items,
        date,
      }));
  }, [sortedItems, granularity]);

  // Get date range info
  const dateRange = useMemo(() => {
    if (sortedItems.length === 0) return null;
    const first = new Date(sortedItems[0].occurred_start);
    const last = new Date(sortedItems[sortedItems.length - 1].occurred_start);
    return { first, last };
  }, [sortedItems]);

  // Navigation
  const scrollToGroup = (index: number) => {
    const clampedIndex = Math.max(0, Math.min(index, timelineGroups.length - 1));
    setCurrentIndex(clampedIndex);
    const element = document.getElementById(`timeline-group-${clampedIndex}`);
    element?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const zoomIn = () => {
    const levels: Granularity[] = ['year', 'month', 'week', 'day'];
    const currentIdx = levels.indexOf(granularity);
    if (currentIdx < levels.length - 1) {
      setGranularity(levels[currentIdx + 1]);
    }
  };

  const zoomOut = () => {
    const levels: Granularity[] = ['year', 'month', 'week', 'day'];
    const currentIdx = levels.indexOf(granularity);
    if (currentIdx > 0) {
      setGranularity(levels[currentIdx - 1]);
    }
  };

  if (sortedItems.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12">
        <Calendar className="w-12 h-12 text-muted-foreground mb-3" />
        <div className="text-base font-medium text-foreground mb-1">No Timeline Data</div>
        <div className="text-xs text-muted-foreground text-center max-w-md">
          No memories have occurred_at dates.
          {itemsWithoutDates.length > 0 && (
            <span className="block mt-1">
              {itemsWithoutDates.length} memories without dates in Table View.
            </span>
          )}
        </div>
      </div>
    );
  }

  const formatDateTime = (dateStr: string) => {
    const date = new Date(dateStr);
    const dateFormatted = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    const timeFormatted = date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false });
    return { date: dateFormatted, time: timeFormatted };
  };

  const granularityLabels: Record<Granularity, string> = {
    year: 'Year',
    month: 'Month',
    week: 'Week',
    day: 'Day',
  };

  return (
    <div className="flex gap-3 px-4">
      {/* Timeline */}
      <div className={`transition-all ${selectedItem ? 'w-2/3' : 'w-full'}`}>
        {/* Controls */}
        <div className="flex items-center justify-between mb-3 gap-4">
          <div className="text-xs text-muted-foreground">
            {sortedItems.length} memories
            {itemsWithoutDates.length > 0 && ` · ${itemsWithoutDates.length} without dates`}
            {dateRange && (
              <span className="ml-2 text-foreground">
                ({dateRange.first.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} → {dateRange.last.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })})
              </span>
            )}
          </div>

          <div className="flex items-center gap-1">
            {/* Zoom controls */}
            <div className="flex items-center border border-border rounded mr-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={zoomOut}
                disabled={granularity === 'year'}
                className="h-7 w-7 p-0"
                title="Zoom out"
              >
                <ZoomOut className="h-3 w-3" />
              </Button>
              <span className="text-[10px] px-2 min-w-[50px] text-center border-x border-border">
                {granularityLabels[granularity]}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={zoomIn}
                disabled={granularity === 'day'}
                className="h-7 w-7 p-0"
                title="Zoom in"
              >
                <ZoomIn className="h-3 w-3" />
              </Button>
            </div>

            {/* Navigation controls */}
            <div className="flex items-center border border-border rounded">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => scrollToGroup(0)}
                disabled={timelineGroups.length <= 1}
                className="h-7 w-7 p-0"
                title="First"
              >
                <ChevronsLeft className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => scrollToGroup(currentIndex - 1)}
                disabled={currentIndex === 0}
                className="h-7 w-7 p-0"
                title="Previous"
              >
                <ChevronLeft className="h-3 w-3" />
              </Button>
              <span className="text-[10px] px-2 min-w-[60px] text-center border-x border-border">
                {currentIndex + 1} / {timelineGroups.length}
              </span>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => scrollToGroup(currentIndex + 1)}
                disabled={currentIndex >= timelineGroups.length - 1}
                className="h-7 w-7 p-0"
                title="Next"
              >
                <ChevronRight className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => scrollToGroup(timelineGroups.length - 1)}
                disabled={timelineGroups.length <= 1}
                className="h-7 w-7 p-0"
                title="Last"
              >
                <ChevronsRight className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>

        <div ref={timelineRef} className="relative max-h-[550px] overflow-y-auto pr-2">
          {/* Vertical line */}
          <div className="absolute left-[60px] top-0 bottom-0 w-0.5 bg-border" />

          {timelineGroups.map((group, groupIdx) => (
            <div key={group.key} id={`timeline-group-${groupIdx}`} className="mb-4">
              {/* Group header */}
              <div
                className="flex items-center mb-2 cursor-pointer hover:opacity-80"
                onClick={() => setCurrentIndex(groupIdx)}
              >
                <div className="w-[60px] text-right pr-3">
                  <span className="text-xs font-semibold text-primary">{group.label}</span>
                </div>
                <div className="w-2 h-2 rounded-full bg-primary z-10" />
                <span className="ml-2 text-[10px] text-muted-foreground">
                  {group.items.length} {group.items.length === 1 ? 'item' : 'items'}
                </span>
              </div>

              {/* Items in this month */}
              <div className="space-y-1">
                {group.items.map((item: any, idx: number) => (
                  <div
                    key={item.id || idx}
                    onClick={() => setSelectedItem(item)}
                    className={`flex items-start cursor-pointer group ${
                      selectedItem?.id === item.id ? 'opacity-100' : 'hover:opacity-80'
                    }`}
                  >
                    {/* Date & Time */}
                    <div className="w-[60px] text-right pr-3 pt-1 flex-shrink-0">
                      <div className="text-[10px] text-muted-foreground">
                        {formatDateTime(item.occurred_start).date}
                      </div>
                      <div className="text-[9px] text-muted-foreground/70">
                        {formatDateTime(item.occurred_start).time}
                      </div>
                    </div>

                    {/* Connector dot */}
                    <div className="flex-shrink-0 pt-2">
                      <div className={`w-1.5 h-1.5 rounded-full z-10 ${
                        selectedItem?.id === item.id ? 'bg-primary' : 'bg-muted-foreground/50 group-hover:bg-primary'
                      }`} />
                    </div>

                    {/* Card */}
                    <div className={`ml-3 flex-1 p-2 rounded border transition-colors ${
                      selectedItem?.id === item.id
                        ? 'bg-primary/10 border-primary'
                        : 'bg-card border-border hover:border-primary/50'
                    }`}>
                      <p className="text-xs text-foreground line-clamp-2 leading-relaxed">
                        {item.text}
                      </p>
                      {item.context && (
                        <p className="text-[10px] text-muted-foreground mt-1 truncate">
                          {item.context}
                        </p>
                      )}
                      {item.entities && (
                        <div className="flex gap-1 mt-1 flex-wrap">
                          {item.entities.split(', ').slice(0, 3).map((entity: string, i: number) => (
                            <span key={i} className="text-[9px] px-1 py-0.5 rounded bg-secondary text-secondary-foreground">
                              {entity}
                            </span>
                          ))}
                          {item.entities.split(', ').length > 3 && (
                            <span className="text-[9px] text-muted-foreground">
                              +{item.entities.split(', ').length - 3}
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Detail Panel */}
      {selectedItem && (
        <div className="w-1/3">
          <MemoryDetailPanel
            memory={selectedItem}
            onClose={() => setSelectedItem(null)}
            onViewDocument={onViewDocument}
            compact
          />
        </div>
      )}
    </div>
  );
}
