"use client";

import { useState, useEffect } from "react";
import { client } from "@/lib/api";
import { useBank } from "@/lib/bank-context";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

interface DocumentChunkModalProps {
  type: "document" | "chunk";
  id: string | null;
  onClose: () => void;
}

export function DocumentChunkModal({ type, id, onClose }: DocumentChunkModalProps) {
  const { currentBank } = useBank();
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        if (type === "document") {
          if (!currentBank) {
            setError("未选择记忆库");
            return;
          }
          const doc = await client.getDocument(id, currentBank);
          setData(doc);
        } else {
          const chunk = await client.getChunk(id);
          setData(chunk);
        }
      } catch (err) {
        console.error(`加载 ${type} 时出错:`, err);
        setError((err as Error).message);
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [id, type, currentBank]);

  const isOpen = id !== null;

  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-3xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>{type === "document" ? "文档详情" : "片段详情"}</DialogTitle>
          <DialogDescription>
            {type === "document"
              ? "查看原始文档文本和元数据"
              : "查看片段文本和元数据"}
          </DialogDescription>
        </DialogHeader>

        <div className="flex-1 overflow-y-auto">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="text-4xl mb-2">⏳</div>
                <div className="text-sm text-muted-foreground">正在加载 {type === "document" ? "文档" : "片段"}...</div>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center text-destructive">
                <div className="text-4xl mb-2">❌</div>
                <div className="text-sm">错误: {error}</div>
              </div>
            </div>
          ) : data ? (
            <div className="space-y-4">
              {type === "document" ? (
                <>
                  <div className="space-y-3">
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                        文档 ID
                      </div>
                      <div className="text-sm font-mono break-all text-foreground">{data.id}</div>
                    </div>
                    {data.created_at && (
                      <div className="grid grid-cols-2 gap-3">
                        <div className="p-3 bg-muted rounded-lg">
                          <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                            创建时间
                          </div>
                          <div className="text-sm text-foreground">
                            {new Date(data.created_at).toLocaleString()}
                          </div>
                        </div>
                        <div className="p-3 bg-muted rounded-lg">
                          <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                            记忆单元数
                          </div>
                          <div className="text-sm text-foreground">{data.memory_unit_count}</div>
                        </div>
                      </div>
                    )}
                    {data.original_text && (
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                          文本长度
                        </div>
                        <div className="text-sm text-foreground">
                          {data.original_text.length.toLocaleString()} 字符
                        </div>
                      </div>
                    )}
                  </div>

                  {data.original_text && (
                    <div>
                      <div className="text-sm font-bold text-foreground mb-2">原始文本</div>
                      <div className="p-4 bg-muted rounded-lg border border-border max-h-[300px] overflow-y-auto">
                        <pre className="text-sm whitespace-pre-wrap font-mono text-foreground">
                          {data.original_text}
                        </pre>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <>
                  <div className="space-y-3">
                    <div className="p-3 bg-muted rounded-lg">
                      <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                        片段 ID
                      </div>
                      <div className="text-sm font-mono break-all text-foreground">
                        {data.chunk_id}
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                          文档 ID
                        </div>
                        <div className="text-sm font-mono break-all text-foreground">
                          {data.document_id}
                        </div>
                      </div>
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                          片段索引
                        </div>
                        <div className="text-sm text-foreground">{data.chunk_index}</div>
                      </div>
                    </div>
                    {data.created_at && (
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                          创建时间
                        </div>
                        <div className="text-sm text-foreground">
                          {new Date(data.created_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                    {data.chunk_text && (
                      <div className="p-3 bg-muted rounded-lg">
                        <div className="text-xs font-bold text-muted-foreground uppercase mb-1">
                          文本长度
                        </div>
                        <div className="text-sm text-foreground">
                          {data.chunk_text.length.toLocaleString()} 字符
                        </div>
                      </div>
                    )}
                  </div>

                  {data.chunk_text && (
                    <div>
                      <div className="text-sm font-bold text-foreground mb-2">片段文本</div>
                      <div className="p-4 bg-muted rounded-lg border border-border max-h-[300px] overflow-y-auto">
                        <pre className="text-sm whitespace-pre-wrap font-mono text-foreground">
                          {data.chunk_text}
                        </pre>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
