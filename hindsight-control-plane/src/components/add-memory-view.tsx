'use client';

import { useState } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';

export function AddMemoryView() {
  const { currentBank } = useBank();
  const [content, setContent] = useState('');
  const [context, setContext] = useState('');
  const [eventDate, setEventDate] = useState('');
  const [documentId, setDocumentId] = useState('');
  const [async, setAsync] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<string | null>(null);

  const clearForm = () => {
    setContent('');
    setContext('');
    setEventDate('');
    setDocumentId('');
    setAsync(false);
    setResult(null);
  };

  const submitMemory = async () => {
    if (!currentBank || !content) {
      alert('Please enter content');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const item: any = { content };
      if (context) item.context = context;
      if (eventDate) item.timestamp = eventDate;

      const data: any = await client.retain({
        bank_id: currentBank,
        items: [item],
        document_id: documentId,
        async,
      });

      setResult(data.message as string);
      setContent('');
    } catch (error) {
      console.error('Error submitting memory:', error);
      setResult('Error: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl">
      <p className="text-muted-foreground mb-4">
        Retain memories to the selected memory bank. You can add one or multiple memories at once.
      </p>

      <div className="max-w-3xl">
        <div className="bg-card p-5 rounded-lg mb-5 border-2 border-primary">
          <h3 className="mt-0 text-card-foreground">Memory Entry</h3>

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

          <div className="mb-4">
            <label className="font-bold block mb-1 text-card-foreground">Event Date</label>
            <input
              type="datetime-local"
              value={eventDate}
              onChange={(e) => setEventDate(e.target.value)}
              className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div className="mb-4">
            <label className="font-bold block mb-1 text-card-foreground">Document ID</label>
            <input
              type="text"
              value={documentId}
              onChange={(e) => setDocumentId(e.target.value)}
              placeholder="Optional document identifier (automatically upserts if document exists)..."
              className="w-full px-2.5 py-2 border-2 border-border bg-background text-foreground rounded text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
            <small className="text-muted-foreground text-xs mt-1 block">
              Note: If a document with this ID already exists, it will be automatically replaced with the new content.
            </small>
          </div>

          <div className="mb-4">
            <label className="flex items-center cursor-pointer">
              <input
                type="checkbox"
                checked={async}
                onChange={(e) => setAsync(e.target.checked)}
                className="mr-2 w-4 h-4 cursor-pointer"
              />
              <span className="font-bold text-card-foreground">Async (process in background)</span>
            </label>
          </div>

          <div className="flex gap-2.5">
            <button
              onClick={submitMemory}
              disabled={loading}
              className="px-6 py-3 bg-primary text-primary-foreground rounded cursor-pointer font-bold text-sm hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Retaining...' : 'Retain Memory'}
            </button>
            <button
              onClick={clearForm}
              className="px-6 py-3 bg-secondary text-secondary-foreground rounded cursor-pointer font-bold text-sm hover:opacity-90"
            >
              Clear Form
            </button>
          </div>
        </div>

        {result && (
          <div className={`mt-5 p-5 rounded-lg border-2 ${result.startsWith('Error') ? 'bg-destructive/10 border-destructive text-destructive' : 'bg-primary/10 border-primary text-primary'}`}>
            <div className="font-semibold">{result}</div>
          </div>
        )}

        {loading && (
          <div className="text-center py-10 text-muted-foreground">
            <div className="text-5xl mb-2.5">⏳</div>
            <div className="text-lg">Retaining memory...</div>
          </div>
        )}
      </div>
    </div>
  );
}
