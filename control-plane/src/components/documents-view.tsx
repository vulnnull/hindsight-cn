'use client';

import { useState } from 'react';
import { dataplaneClient } from '@/lib/api';
import { useAgent } from '@/lib/agent-context';

export function DocumentsView() {
  const { currentAgent } = useAgent();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [total, setTotal] = useState(0);

  const loadDocuments = async () => {
    if (!currentAgent) return;

    setLoading(true);
    try {
      const data: any = await dataplaneClient.listDocuments({
        agent_id: currentAgent,
        q: searchQuery,
        limit: 100,
      });
      setDocuments(data.items || []);
      setTotal(data.total || 0);
    } catch (error) {
      console.error('Error loading documents:', error);
      alert('Error loading documents: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const viewDocumentText = async (documentId: string) => {
    if (!currentAgent) return;

    try {
      const doc: any = await dataplaneClient.getDocument(documentId, currentAgent);
      alert(`Document: ${doc.id}\n\nCreated: ${doc.created_at}\nMemory Units: ${doc.memory_unit_count}\n\n${doc.original_text}`);
    } catch (error) {
      console.error('Error loading document:', error);
      alert('Error loading document: ' + (error as Error).message);
    }
  };

  return (
    <div>
      <div className="mb-4 p-2.5 bg-card rounded-lg border-2 border-primary flex gap-4 items-center flex-wrap">
        <button
          onClick={loadDocuments}
          disabled={loading}
          className="px-5 py-2 bg-primary text-primary-foreground rounded font-bold text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? '⏳ Loading...' : documents.length > 0 ? '🔄 Refresh Documents' : '📄 Load Documents'}
        </button>
        {documents.length > 0 && (
          <span className="text-muted-foreground text-sm">({total} total documents)</span>
        )}
      </div>

      <input
        type="text"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        placeholder="Search documents (ID)..."
        className="w-full max-w-2xl px-2.5 py-2 mb-4 mx-5 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
      />

      <div className="overflow-x-auto px-5 pb-5">
        <table className="w-full border-collapse text-xs max-w-7xl">
          <thead>
            <tr>
              <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Document ID</th>
              <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Created</th>
              <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Updated</th>
              <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Text Length</th>
              <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Memory Units</th>
              <th className="p-2.5 text-left border border-border bg-card text-card-foreground">Actions</th>
            </tr>
          </thead>
          <tbody>
            {documents.length > 0 ? (
              documents.map((doc) => (
                <tr key={doc.id} className="bg-background hover:bg-muted">
                  <td className="p-2 border border-border" title={doc.id}>
                    {doc.id.length > 30 ? doc.id.substring(0, 30) + '...' : doc.id}
                  </td>
                  <td className="p-2 border border-border">
                    {doc.created_at ? new Date(doc.created_at).toLocaleString() : 'N/A'}
                  </td>
                  <td className="p-2 border border-border">
                    {doc.updated_at ? new Date(doc.updated_at).toLocaleString() : 'N/A'}
                  </td>
                  <td className="p-2 border border-border">{doc.text_length?.toLocaleString()} chars</td>
                  <td className="p-2 border border-border">{doc.memory_unit_count}</td>
                  <td className="p-2 border border-border">
                    <button
                      onClick={() => viewDocumentText(doc.id)}
                      className="px-2.5 py-1 bg-primary text-primary-foreground rounded text-xs font-bold hover:opacity-90"
                      title="View original text"
                    >
                      View Text
                    </button>
                  </td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={6} className="p-10 text-center text-muted-foreground bg-muted">
                  Click "Load Documents" to view data
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
