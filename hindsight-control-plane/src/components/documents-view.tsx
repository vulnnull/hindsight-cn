'use client';

import { useState } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { ChevronDown, ChevronUp } from 'lucide-react';

export function DocumentsView() {
  const { currentBank } = useBank();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [total, setTotal] = useState(0);

  // Add memory form state
  const [showAddMemory, setShowAddMemory] = useState(false);
  const [content, setContent] = useState('');
  const [context, setContext] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [async, setAsync] = useState(false);
  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitResult, setSubmitResult] = useState<string | null>(null);

  const loadDocuments = async () => {
    if (!currentBank) return;

    setLoading(true);
    try {
      const data: any = await client.listDocuments({
        bank_id: currentBank,
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
    if (!currentBank) return;

    try {
      const doc: any = await client.getDocument(documentId, currentBank);
      alert(`Document: ${doc.id}\n\nCreated: ${doc.created_at}\nMemory Units: ${doc.memory_unit_count}\n\n${doc.original_text}`);
    } catch (error) {
      console.error('Error loading document:', error);
      alert('Error loading document: ' + (error as Error).message);
    }
  };

  const submitMemory = async () => {
    if (!currentBank || !content) {
      alert('Please enter content');
      return;
    }

    setSubmitLoading(true);
    setSubmitResult(null);

    try {
      const item: any = { content };
      if (context) item.context = context;
      if (eventDate) item.event_date = eventDate;

      const params: any = {
        bank_id: currentBank,
        items: [item],
      };

      if (documentId) params.document_id = documentId;

      let data: any;
      if (async) {
        data = await client.retain({ ...params, async: true });
      } else {
        data = await client.retain(params);
      }

      setSubmitResult(data.message as string);
      setContent('');
      setContext('');
      setEventDate('');
      setDocumentId('');

      // Refresh documents list
      loadDocuments();
    } catch (error) {
      console.error('Error submitting memory:', error);
      setSubmitResult('Error: ' + (error as Error).message);
    } finally {
      setSubmitLoading(false);
    }
  };

  return (
    <div>
      {/* Retain Memory Section */}
      <div className="mb-6 bg-card rounded-lg border-2 border-primary overflow-hidden">
        <button
          onClick={() => setShowAddMemory(!showAddMemory)}
          className="w-full flex items-center justify-between p-4 hover:bg-accent transition-colors"
        >
          <div className="flex items-center gap-2">
            <span className="text-lg font-semibold text-card-foreground">Retain Memory</span>
            <span className="text-sm text-muted-foreground">Add new memories to this memory bank</span>
          </div>
          {showAddMemory ? <ChevronUp className="w-5 h-5" /> : <ChevronDown className="w-5 h-5" />}
        </button>

        {showAddMemory && (
          <div className="p-4 border-t border-border bg-background">
            <div className="max-w-3xl">
              <div className="mb-4">
                <label className="font-bold block mb-1 text-card-foreground">Content *</label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  placeholder="Enter the memory content..."
                  className="w-full min-h-[100px] px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div className="mb-4">
                <label className="font-bold block mb-1 text-card-foreground">Context</label>
                <input
                  type="text"
                  value={context}
                  onChange={(e) => setContext(e.target.value)}
                  placeholder="Optional context about this memory..."
                  className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div>
                  <label className="font-bold block mb-1 text-card-foreground">Event Date</label>
                  <input
                    type="datetime-local"
                    value={eventDate}
                    onChange={(e) => setEventDate(e.target.value)}
                    className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>

                <div>
                  <label className="font-bold block mb-1 text-card-foreground">Document ID</label>
                  <input
                    type="text"
                    value={documentId}
                    onChange={(e) => setDocumentId(e.target.value)}
                    placeholder="Optional document identifier..."
                    className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                  />
                </div>
              </div>

              <div className="mb-4">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={async}
                    onChange={(e) => setAsync(e.target.checked)}
                    className="mr-2 w-4 h-4 cursor-pointer"
                  />
                  <span className="text-sm text-card-foreground">Async (process in background)</span>
                </label>
              </div>

              <button
                onClick={submitMemory}
                disabled={submitLoading || !content}
                className="px-6 py-2.5 bg-primary text-primary-foreground rounded font-bold text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitLoading ? 'Retaining...' : 'Retain Memory'}
              </button>

              {submitResult && (
                <div className={`mt-4 p-3 rounded-lg border-2 text-sm ${submitResult.startsWith('Error') ? 'bg-destructive/10 border-destructive text-destructive' : 'bg-primary/10 border-primary text-primary'}`}>
                  {submitResult}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Documents List Section */}
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
