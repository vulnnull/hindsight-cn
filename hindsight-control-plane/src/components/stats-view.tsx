'use client';

import { useState, useEffect } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';

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
      setOperations(ops?.operations || []);
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
      <div className="p-10 text-center text-gray-600 bg-gray-50">
        <h3 className="text-xl font-semibold mb-2">No Agent Selected</h3>
        <p>Please select an agent from the dropdown above to view statistics.</p>
      </div>
    );
  }

  if (loading && !stats) {
    return (
      <div className="text-center py-10 text-gray-600">
        <div className="text-5xl mb-2.5">📊</div>
        <div className="text-lg">Loading statistics...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Stats Section */}
      {stats && (
        <div className="bg-white border-2 border-slate-800 rounded-lg p-5 mb-5 shadow">
          <h3 className="mt-0 mb-5 text-slate-800 text-lg font-bold flex items-center justify-between">
            <span>📊 Memory Statistics</span>
            <button
              onClick={loadStats}
              className="px-3 py-1 text-sm bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              🔄 Refresh
            </button>
          </h3>
          <div className="grid grid-cols-3 gap-4">
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Total Nodes</div>
              <div className="text-3xl font-bold text-slate-800">{stats.total_nodes || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">World Facts</div>
              <div className="text-3xl font-bold text-slate-800">{stats.nodes_by_type?.world || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Agent Facts</div>
              <div className="text-3xl font-bold text-slate-800">{stats.nodes_by_type?.agent || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Opinions</div>
              <div className="text-3xl font-bold text-slate-800">{stats.nodes_by_type?.opinion || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Total Links</div>
              <div className="text-3xl font-bold text-slate-800">{stats.total_links || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Temporal Links</div>
              <div className="text-3xl font-bold text-slate-800">{stats.links_by_type?.temporal || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Semantic Links</div>
              <div className="text-3xl font-bold text-slate-800">{stats.links_by_type?.semantic || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Entity Links</div>
              <div className="text-3xl font-bold text-slate-800">{stats.links_by_type?.entity || 0}</div>
            </div>
            <div className="bg-gray-50 border-2 border-gray-300 rounded p-4 text-center transition-all hover:border-blue-400 hover:shadow">
              <div className="text-xs text-gray-600 font-semibold uppercase tracking-wide mb-2">Documents</div>
              <div className="text-3xl font-bold text-slate-800">{stats.total_documents || 0}</div>
            </div>
          </div>
        </div>
      )}

      {/* Operations Section */}
      <div className="bg-white border-2 border-slate-800 rounded-lg p-5 shadow">
        <h3 className="mt-0 mb-5 text-slate-800 text-lg font-bold">⚙️ Async Operations</h3>

        {stats && (stats.pending_operations > 0 || stats.failed_operations > 0) && (
          <div className="mb-4 p-3 bg-yellow-50 border border-yellow-300 rounded">
            <div className="flex gap-4">
              {stats.pending_operations > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-yellow-600 font-semibold">⏳ Pending:</span>
                  <span className="text-yellow-800 font-bold">{stats.pending_operations}</span>
                </div>
              )}
              {stats.failed_operations > 0 && (
                <div className="flex items-center gap-2">
                  <span className="text-red-600 font-semibold">❌ Failed:</span>
                  <span className="text-red-800 font-bold">{stats.failed_operations}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {operations.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full border-collapse text-xs">
              <thead>
                <tr>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">ID</th>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">Type</th>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">Items</th>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">Document ID</th>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">Created</th>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">Status</th>
                  <th className="p-2.5 text-left border border-gray-300 bg-gray-100">Error</th>
                </tr>
              </thead>
              <tbody>
                {operations.map((op) => (
                  <tr key={op.id} className={op.status === 'failed' ? 'bg-red-50' : ''}>
                    <td className="p-2 border border-gray-300" title={op.id}>
                      {op.id.substring(0, 8)}...
                    </td>
                    <td className="p-2 border border-gray-300">{op.task_type}</td>
                    <td className="p-2 border border-gray-300">{op.items_count}</td>
                    <td className="p-2 border border-gray-300">{op.document_id || 'N/A'}</td>
                    <td className="p-2 border border-gray-300">
                      {new Date(op.created_at).toLocaleString()}
                    </td>
                    <td className="p-2 border border-gray-300">
                      <span
                        className={`px-2 py-1 rounded text-xs font-bold ${
                          op.status === 'pending'
                            ? 'bg-yellow-100 text-yellow-800'
                            : op.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-green-100 text-green-800'
                        }`}
                      >
                        {op.status}
                      </span>
                    </td>
                    <td className="p-2 border border-gray-300">
                      {op.error_message ? (
                        <span className="text-red-600" title={op.error_message}>
                          {op.error_message.substring(0, 50)}...
                        </span>
                      ) : (
                        'None'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-gray-600 text-center py-5">No operations found</p>
        )}
      </div>
    </div>
  );
}
