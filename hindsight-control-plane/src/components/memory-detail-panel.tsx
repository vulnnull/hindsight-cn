'use client';

import { Button } from '@/components/ui/button';
import { Copy, Check, X } from 'lucide-react';
import { useState } from 'react';

interface MemoryDetailPanelProps {
  memory: any;
  onClose: () => void;
  onViewDocument?: (documentId: string) => void;
  onViewChunk?: (chunkId: string) => void;
  compact?: boolean;
}

export function MemoryDetailPanel({
  memory,
  onClose,
  onViewDocument,
  onViewChunk,
  compact = false,
}: MemoryDetailPanelProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(text);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  if (!memory) return null;

  const padding = compact ? 'p-3' : 'p-4';
  const titleSize = compact ? 'text-sm' : 'text-lg';
  const labelSize = compact ? 'text-[10px]' : 'text-xs';
  const textSize = compact ? 'text-xs' : 'text-sm';
  const gap = compact ? 'space-y-2' : 'space-y-4';

  return (
    <div className={`bg-card border-2 border-primary rounded-lg ${padding} sticky top-4 max-h-[calc(100vh-120px)] overflow-y-auto`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className={`${titleSize} font-bold text-card-foreground`}>Memory Details</h3>
          {!compact && (
            <p className="text-sm text-muted-foreground">Full memory content and metadata</p>
          )}
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClose}
          className={compact ? 'h-6 w-6 p-0' : 'h-8 w-8 p-0'}
        >
          <X className={compact ? 'h-3 w-3' : 'h-4 w-4'} />
        </Button>
      </div>

      <div className={gap}>
        {/* Full Text */}
        <div className={`${compact ? 'p-2' : 'p-3'} bg-muted rounded-lg`}>
          <div className={`${labelSize} font-bold text-muted-foreground uppercase mb-1`}>Full Text</div>
          <div className={`${textSize} whitespace-pre-wrap`}>{memory.text}</div>
        </div>

        {/* Context */}
        {memory.context && (
          <div className={`${compact ? 'p-2' : 'p-3'} bg-muted rounded-lg`}>
            <div className={`${labelSize} font-bold text-muted-foreground uppercase mb-1`}>Context</div>
            <div className={textSize}>{memory.context}</div>
          </div>
        )}

        {/* Dates */}
        <div className="grid grid-cols-2 gap-2">
          <div className={`${compact ? 'p-2' : 'p-3'} bg-muted rounded-lg`}>
            <div className={`${labelSize} font-bold text-muted-foreground uppercase mb-1`}>Occurred</div>
            <div className={textSize}>
              {memory.occurred_start
                ? new Date(memory.occurred_start).toLocaleString()
                : 'N/A'}
            </div>
          </div>
          <div className={`${compact ? 'p-2' : 'p-3'} bg-muted rounded-lg`}>
            <div className={`${labelSize} font-bold text-muted-foreground uppercase mb-1`}>Mentioned</div>
            <div className={textSize}>
              {memory.mentioned_at
                ? new Date(memory.mentioned_at).toLocaleString()
                : 'N/A'}
            </div>
          </div>
        </div>

        {/* Entities */}
        {memory.entities && (
          <div className={`${compact ? 'p-2' : 'p-3'} bg-muted rounded-lg`}>
            <div className={`${labelSize} font-bold text-muted-foreground uppercase mb-2`}>Entities</div>
            <div className="flex flex-wrap gap-1">
              {memory.entities.split(', ').map((entity: string, i: number) => (
                <span
                  key={i}
                  className={`${compact ? 'text-[10px] px-1.5 py-0.5' : 'text-xs px-2 py-1'} rounded bg-secondary text-secondary-foreground`}
                >
                  {entity}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* ID */}
        <div className={`${compact ? 'p-2' : 'p-3'} bg-muted rounded-lg`}>
          <div className={`${labelSize} font-bold text-muted-foreground uppercase mb-1`}>Memory ID</div>
          <div className="flex items-center gap-2">
            <span className={`${compact ? 'text-[10px]' : 'text-sm'} font-mono break-all`}>{memory.id}</span>
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0 flex-shrink-0"
              onClick={() => copyToClipboard(memory.id)}
            >
              {copiedId === memory.id ? (
                <Check className="h-3 w-3 text-green-600" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>
          </div>
        </div>

        {/* Document/Chunk buttons */}
        {(memory.document_id || memory.chunk_id) && (
          <div className={`flex gap-2 ${compact ? 'pt-1' : ''}`}>
            {memory.document_id && onViewDocument && (
              <Button
                onClick={() => onViewDocument(memory.document_id)}
                size="sm"
                variant="outline"
                className={`flex-1 ${compact ? 'h-7 text-xs' : ''}`}
              >
                View Document
              </Button>
            )}
            {memory.chunk_id && onViewChunk && (
              <Button
                onClick={() => onViewChunk(memory.chunk_id)}
                size="sm"
                variant="outline"
                className={`flex-1 ${compact ? 'h-7 text-xs' : ''}`}
              >
                View Chunk
              </Button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
