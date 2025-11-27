'use client';

import { useState, useEffect, useRef } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import cytoscape from 'cytoscape';

type FactType = 'world' | 'bank' | 'opinion';
type ViewMode = 'graph' | 'table';

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
  const cyRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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
            opacity: 0.7,
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
  };

  useEffect(() => {
    if (viewMode === 'graph' && data) {
      renderGraph();
    }
  }, [viewMode, data, nodeLimit, layout]);

  return (
    <div>
      <div className="mb-4 p-2.5 bg-card rounded-lg border-2 border-primary flex gap-4 items-center flex-wrap">
        <button
          onClick={loadData}
          disabled={loading}
          className="px-5 py-2 bg-primary text-primary-foreground rounded font-bold text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Loading...' : data ? `🔄 Refresh ${factType.charAt(0).toUpperCase() + factType.slice(1)} Facts` : `📊 Load ${factType.charAt(0).toUpperCase() + factType.slice(1)} Facts`}
        </button>
        {data && (
          <span className="text-muted-foreground text-sm">
            ({data.total_units} total facts)
          </span>
        )}
      </div>

      {data && (
        <>
          <div className="bg-accent px-5 py-2.5 border-b-2 border-primary flex gap-2.5 mb-4">
            <button
              onClick={() => setViewMode('graph')}
              className={`px-4 py-1.5 font-bold text-sm rounded transition-all border-2 ${
                viewMode === 'graph'
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background text-foreground border-border hover:bg-muted'
              }`}
            >
              Graph
            </button>
            <button
              onClick={() => setViewMode('table')}
              className={`px-4 py-1.5 font-bold text-sm rounded transition-all border-2 ${
                viewMode === 'table'
                  ? 'bg-primary text-primary-foreground border-primary'
                  : 'bg-background text-foreground border-border hover:bg-muted'
              }`}
            >
              Table
            </button>
          </div>

          {viewMode === 'graph' && (
            <div className="relative">
              <div className="p-4 bg-card border-b-2 border-primary flex gap-4 items-center flex-wrap">
                <div>
                  <label className="mr-2 font-semibold text-card-foreground">Limit nodes:</label>
                  <input
                    type="number"
                    value={nodeLimit}
                    onChange={(e) => setNodeLimit(parseInt(e.target.value))}
                    min="10"
                    max="1000"
                    step="10"
                    className="w-20 px-2 py-1 border-2 border-border bg-background text-foreground rounded focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
                <div>
                  <label className="mr-2 font-semibold text-card-foreground">Layout:</label>
                  <select
                    value={layout}
                    onChange={(e) => setLayout(e.target.value)}
                    className="px-2 py-1 border-2 border-border bg-background text-foreground rounded focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="circle">Circle (fast)</option>
                    <option value="grid">Grid (fast)</option>
                    <option value="cose">Force-directed (slow)</option>
                  </select>
                </div>
                <button
                  onClick={renderGraph}
                  className="px-4 py-1.5 bg-secondary text-secondary-foreground rounded font-bold hover:opacity-90"
                >
                  Apply Layout
                </button>
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
          )}

          {viewMode === 'table' && (
            <div>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search memories (text, context)..."
                className="w-full max-w-2xl px-2.5 py-2 mb-4 mx-5 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              <div className="overflow-x-auto px-5 pb-5">
                <table className="w-full border-collapse text-xs max-w-7xl">
                  <thead>
                    <tr>
                      <th className="p-2.5 text-left border border-border bg-card text-card-foreground">ID</th>
                      <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Text</th>
                      <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Context</th>
                      <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Occurred</th>
                      <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Mentioned</th>
                      <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Entities</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.table_rows && data.table_rows.length > 0 ? (
                      data.table_rows
                        .filter((row: any) => {
                          if (!searchQuery) return true;
                          const query = searchQuery.toLowerCase();
                          return (
                            row.text?.toLowerCase().includes(query) ||
                            row.context?.toLowerCase().includes(query)
                          );
                        })
                        .map((row: any, idx: number) => {
                          // Format temporal range
                          let occurredDisplay = 'N/A';
                          if (row.occurred_start && row.occurred_end) {
                            const start = new Date(row.occurred_start).toLocaleDateString();
                            const end = new Date(row.occurred_end).toLocaleDateString();
                            occurredDisplay = start === end ? start : `${start} - ${end}`;
                          } else if (row.date) {
                            // Fallback to old date field
                            occurredDisplay = row.date;
                          }

                          const mentionedDisplay = row.mentioned_at
                            ? new Date(row.mentioned_at).toLocaleDateString()
                            : 'N/A';

                          return (
                            <tr key={idx} className="bg-background hover:bg-muted">
                              <td className="p-2 border border-border" title={row.id}>{row.id}</td>
                              <td className="p-2 border border-border">{row.text}</td>
                              <td className="p-2 border border-border">{row.context || 'N/A'}</td>
                              <td className="p-2 border border-border">{occurredDisplay}</td>
                              <td className="p-2 border border-border">{mentionedDisplay}</td>
                              <td className="p-2 border border-border">{row.entities || 'None'}</td>
                            </tr>
                          );
                        })
                    ) : (
                      <tr>
                        <td colSpan={6} className="p-10 text-center text-muted-foreground bg-muted">
                          {data.table_rows ? 'No facts match your search' : 'No facts found for this agent and fact type'}
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
