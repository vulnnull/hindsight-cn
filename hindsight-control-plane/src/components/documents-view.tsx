'use client';

import { useState, useEffect } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { X } from 'lucide-react';

export function DocumentsView() {
  const { currentBank } = useBank();
  const [documents, setDocuments] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [total, setTotal] = useState(0);

  // Document view panel state
  const [selectedDocument, setSelectedDocument] = useState<any>(null);
  const [loadingDocument, setLoadingDocument] = useState(false);

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

    setLoadingDocument(true);
    setSelectedDocument({ id: documentId }); // Set placeholder to show loading

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

  // Auto-load documents when component mounts
  useEffect(() => {
    if (currentBank) {
      loadDocuments();
    }
  }, [currentBank]);

  return (
    <div>
      {/* Documents List Section */}
      {loading ? (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="text-4xl mb-2">⏳</div>
            <div className="text-sm text-muted-foreground">Loading documents...</div>
          </div>
        </div>
      ) : documents.length > 0 ? (
        <div className="mb-4 text-sm text-muted-foreground">
          {total} total documents
        </div>
      ) : (
        <div className="flex items-center justify-center py-20">
          <div className="text-center">
            <div className="text-4xl mb-2">📄</div>
            <div className="text-sm text-muted-foreground">No documents found</div>
          </div>
        </div>
      )}

      {/* Documents List and Detail Panel */}
      {documents.length > 0 && (
        <div className="flex gap-4">
          {/* Documents Table */}
          <div className={`transition-all ${selectedDocument ? 'w-1/2' : 'w-full'}`}>
          <div className="px-5 mb-4">
            <Input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search documents (ID)..."
              className="max-w-2xl"
            />
          </div>

          <div className="overflow-x-auto px-5 pb-5">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Document ID</TableHead>
                  <TableHead>Created</TableHead>
                  <TableHead>Context</TableHead>
                  <TableHead>Text Length</TableHead>
                  <TableHead>Memory Units</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {documents.length > 0 ? (
                  documents.map((doc) => (
                    <TableRow
                      key={doc.id}
                      className={selectedDocument?.id === doc.id ? 'bg-accent' : ''}
                    >
                      <TableCell title={doc.id}>
                        {doc.id.length > 30 ? doc.id.substring(0, 30) + '...' : doc.id}
                      </TableCell>
                      <TableCell>
                        {doc.created_at ? new Date(doc.created_at).toLocaleString() : 'N/A'}
                      </TableCell>
                      <TableCell>
                        {doc.retain_params?.context || '-'}
                      </TableCell>
                      <TableCell>{doc.text_length?.toLocaleString()} chars</TableCell>
                      <TableCell>{doc.memory_unit_count}</TableCell>
                      <TableCell>
                        <Button
                          onClick={() => viewDocumentText(doc.id)}
                          size="sm"
                          variant={selectedDocument?.id === doc.id ? 'default' : 'outline'}
                          title="View original text"
                        >
                          View Text
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))
                ) : (
                  <TableRow>
                    <TableCell colSpan={6} className="text-center">
                      Click "Load Documents" to view data
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        {/* Document Detail Panel */}
        {selectedDocument && (
          <div className="w-1/2 pr-5 pb-5">
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
                    {selectedDocument.retain_params && (
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-xs font-bold text-muted-foreground uppercase mb-1">Retain Parameters</div>
                        <div className="text-sm space-y-1">
                          {selectedDocument.retain_params.context && (
                            <div><span className="font-semibold">Context:</span> {selectedDocument.retain_params.context}</div>
                          )}
                          {selectedDocument.retain_params.event_date && (
                            <div><span className="font-semibold">Event Date:</span> {new Date(selectedDocument.retain_params.event_date).toLocaleString()}</div>
                          )}
                          {selectedDocument.retain_params.metadata && (
                            <div className="mt-2">
                              <span className="font-semibold">Metadata:</span>
                              <pre className="mt-1 text-xs">{JSON.stringify(selectedDocument.retain_params.metadata, null, 2)}</pre>
                            </div>
                          )}
                        </div>
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
        </div>
      )}
    </div>
  );
}
