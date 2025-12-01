'use client';

import { useState, useEffect } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RefreshCw, AlertCircle, CheckCircle, Clock } from 'lucide-react';

export function StatsView() {
  const { currentBank } = useBank();
  const [stats, setStats] = useState<any>(null);
  const [operations, setOperations] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const loadStats = async () => {
    if (!currentBank) return;

    setLoading(true);
    try {
      const [stats, ops] = await Promise.all([
        client.getBankStats(currentBank),
        client.listOperations(currentBank),
      ]);
      setStats(stats);
      setOperations((ops as any)?.operations || []);
    } catch (error) {
      console.error('Error loading stats:', error);
      alert('Error loading stats: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (currentBank) {
      loadStats();
      // Refresh every 5 seconds
      const interval = setInterval(loadStats, 5000);
      return () => clearInterval(interval);
    }
  }, [currentBank]);

  if (!currentBank) {
    return (
      <Card>
        <CardContent className="p-10 text-center">
          <h3 className="text-xl font-semibold mb-2 text-card-foreground">No Bank Selected</h3>
          <p className="text-muted-foreground">Please select a memory bank from the dropdown above to view statistics.</p>
        </CardContent>
      </Card>
    );
  }

  if (loading && !stats) {
    return (
      <Card>
        <CardContent className="text-center py-10">
          <Clock className="w-12 h-12 mx-auto mb-3 text-muted-foreground animate-pulse" />
          <div className="text-lg text-muted-foreground">Loading statistics...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Section */}
      {stats && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Memory Statistics</CardTitle>
                <CardDescription>Overview of stored memories and connections</CardDescription>
              </div>
              <Button
                onClick={loadStats}
                size="sm"
                variant="outline"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Total Nodes</div>
                <div className="text-3xl font-bold text-foreground">{stats.total_nodes || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">World Facts</div>
                <div className="text-3xl font-bold text-foreground">{stats.nodes_by_fact_type?.world || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Bank Facts</div>
                <div className="text-3xl font-bold text-foreground">{stats.nodes_by_fact_type?.bank || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Opinions</div>
                <div className="text-3xl font-bold text-foreground">{stats.nodes_by_fact_type?.opinion || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Total Links</div>
                <div className="text-3xl font-bold text-foreground">{stats.total_links || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Temporal Links</div>
                <div className="text-3xl font-bold text-foreground">{stats.links_by_link_type?.temporal || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Semantic Links</div>
                <div className="text-3xl font-bold text-foreground">{stats.links_by_link_type?.semantic || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Entity Links</div>
                <div className="text-3xl font-bold text-foreground">{stats.links_by_link_type?.entity || 0}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center transition-all hover:bg-muted">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-2">Documents</div>
                <div className="text-3xl font-bold text-foreground">{stats.total_documents || 0}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Operations Section */}
      <Card>
        <CardHeader>
          <CardTitle>Async Operations</CardTitle>
          <CardDescription>Background tasks and their status</CardDescription>
        </CardHeader>
        <CardContent>
          {stats && (stats.pending_operations > 0 || stats.failed_operations > 0) && (
            <div className="mb-4 p-3 bg-amber-50 dark:bg-amber-950 border border-amber-200 dark:border-amber-800 rounded-lg">
              <div className="flex gap-4">
                {stats.pending_operations > 0 && (
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-amber-600 dark:text-amber-400" />
                    <span className="text-amber-700 dark:text-amber-300 font-semibold">Pending:</span>
                    <span className="text-amber-900 dark:text-amber-100 font-bold">{stats.pending_operations}</span>
                  </div>
                )}
                {stats.failed_operations > 0 && (
                  <div className="flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-destructive" />
                    <span className="text-destructive font-semibold">Failed:</span>
                    <span className="text-destructive font-bold">{stats.failed_operations}</span>
                  </div>
                )}
              </div>
            </div>
          )}

        {operations.length > 0 ? (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Items</TableHead>
                  <TableHead>Document ID</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Error</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {operations.map((op) => (
                  <TableRow key={op.id} className={op.status === 'failed' ? 'bg-destructive/5' : ''}>
                    <TableCell title={op.id} className="font-mono text-xs">
                      {op.id.substring(0, 8)}...
                    </TableCell>
                    <TableCell>{op.task_type}</TableCell>
                    <TableCell>{op.items_count}</TableCell>
                    <TableCell className="font-mono text-xs">{op.document_id || 'N/A'}</TableCell>
                    <TableCell className="text-sm">
                      {new Date(op.created_at).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        {op.status === 'pending' && (
                          <>
                            <Clock className="w-3 h-3 text-amber-600" />
                            <span className="px-2 py-1 rounded text-xs font-semibold bg-amber-100 dark:bg-amber-950 text-amber-800 dark:text-amber-200 border border-amber-200 dark:border-amber-800">
                              {op.status}
                            </span>
                          </>
                        )}
                        {op.status === 'failed' && (
                          <>
                            <AlertCircle className="w-3 h-3 text-destructive" />
                            <span className="px-2 py-1 rounded text-xs font-semibold bg-destructive/10 text-destructive border border-destructive/20">
                              {op.status}
                            </span>
                          </>
                        )}
                        {op.status === 'completed' && (
                          <>
                            <CheckCircle className="w-3 h-3 text-green-600 dark:text-green-400" />
                            <span className="px-2 py-1 rounded text-xs font-semibold bg-green-100 dark:bg-green-950 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800">
                              {op.status}
                            </span>
                          </>
                        )}
                      </div>
                    </TableCell>
                    <TableCell>
                      {op.error_message ? (
                        <span className="text-destructive text-sm" title={op.error_message}>
                          {op.error_message.substring(0, 50)}...
                        </span>
                      ) : (
                        <span className="text-muted-foreground">None</span>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          <p className="text-muted-foreground text-center py-5">No operations found</p>
        )}
        </CardContent>
      </Card>
    </div>
  );
}
