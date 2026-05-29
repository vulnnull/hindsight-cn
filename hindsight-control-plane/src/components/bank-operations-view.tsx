"use client";

import { useState, useEffect, useCallback } from "react";
import { useTranslations } from "next-intl";
import { useBank } from "@/lib/bank-context";
import { client } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  RefreshCw,
  Clock,
  AlertCircle,
  CheckCircle,
  Loader2,
  X,
  RotateCcw,
  Code,
  Ban,
} from "lucide-react";

interface Operation {
  id: string;
  task_type: string;
  items_count: number;
  document_id: string | null;
  created_at: string;
  status: string;
  error_message: string | null;
}

interface ChildOperationStatus {
  operation_id: string;
  status: string;
  sub_batch_index: number | null;
  items_count: number | null;
  error_message: string | null;
}

type OperationDetails =
  | {
      operation_id: string;
      status: string;
      operation_type: string | null;
      created_at: string | null;
      updated_at: string | null;
      completed_at: string | null;
      error_message: string | null;
      result_metadata?: {
        items_count?: number;
        total_tokens?: number;
        num_sub_batches?: number;
        is_parent?: boolean;
        [key: string]: any;
      } | null;
      child_operations?: ChildOperationStatus[] | null;
      task_payload?: Record<string, unknown> | null;
      error?: never; // Not present in success case
    }
  | {
      error: string; // Error state when loading fails
      operation_id?: never;
      status?: never;
      operation_type?: never;
      created_at?: never;
      updated_at?: never;
      completed_at?: never;
      error_message?: never;
      result_metadata?: never;
      child_operations?: never;
      task_payload?: never;
    };

const OPERATION_TYPE_OPTIONS = [
  { value: "all", label: "全部类型" },
  { value: "retain", label: "存储" },
  { value: "consolidation", label: "归纳" },
  { value: "refresh_mental_model", label: "知识摘要刷新" },
  { value: "file_convert_retain", label: "文件转换与存储" },
  { value: "webhook_delivery", label: "Webhook 投递" },
];

export function BankOperationsView() {
  const t = useTranslations("bankOperations");
  const { currentBank } = useBank();
  const [operations, setOperations] = useState<Operation[]>([]);
  const [totalOperations, setTotalOperations] = useState(0);
  const [statusFilter, setStatusFilter] = useState<string | null>(null);
  const [taskTypeFilter, setTaskTypeFilter] = useState<string | null>(null);
  const [limit] = useState(10);
  const [offset, setOffset] = useState(0);
  const [cancellingOpId, setCancellingOpId] = useState<string | null>(null);
  const [retryingOpId, setRetryingOpId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [selectedOperation, setSelectedOperation] = useState<OperationDetails | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [loadingPayload, setLoadingPayload] = useState(false);
  const [payloadLoadedFor, setPayloadLoadedFor] = useState<string | null>(null);

  const loadOperations = useCallback(
    async (
      newStatusFilter: string | null = statusFilter,
      newOffset: number = offset,
      newTaskTypeFilter: string | null = taskTypeFilter
    ) => {
      if (!currentBank) return;

      setLoading(true);
      try {
        const opsData = await client.listOperations(currentBank, {
          status: newStatusFilter || undefined,
          type: newTaskTypeFilter || undefined,
          limit,
          offset: newOffset,
          excludeParents: true,
        });
        setOperations(opsData.operations || []);
        setTotalOperations(opsData.total || 0);
      } catch (error) {
        console.error("Error loading operations:", error);
      } finally {
        setLoading(false);
      }
    },
    [currentBank, statusFilter, offset, taskTypeFilter, limit]
  );

  const handleFilterChange = (newFilter: string | null) => {
    setStatusFilter(newFilter);
    setOffset(0);
    loadOperations(newFilter, 0, taskTypeFilter);
  };

  const handleTaskTypeFilterChange = (newTaskType: string | null) => {
    setTaskTypeFilter(newTaskType);
    setOffset(0);
    loadOperations(statusFilter, 0, newTaskType);
  };

  const handlePageChange = (newOffset: number) => {
    setOffset(newOffset);
    loadOperations(statusFilter, newOffset, taskTypeFilter);
  };

  const handleCancelOperation = async (operationId: string) => {
    if (!currentBank) return;

    setCancellingOpId(operationId);
    try {
      await client.cancelOperation(currentBank, operationId);
      await loadOperations();
    } catch (error) {
      // Error toast is shown automatically by the API client interceptor
    } finally {
      setCancellingOpId(null);
    }
  };

  const handleRetryOperation = async (operationId: string) => {
    if (!currentBank) return;

    setRetryingOpId(operationId);
    try {
      await client.retryOperation(currentBank, operationId);
      await loadOperations();
    } catch (error) {
      // Error toast is shown automatically by the API client interceptor
    } finally {
      setRetryingOpId(null);
    }
  };

  const handleOperationClick = async (operationId: string) => {
    if (!currentBank) return;

    setLoadingDetails(true);
    setDialogOpen(true);
    setPayloadLoadedFor(null);
    try {
      const details = await client.getOperationStatus(currentBank, operationId);
      setSelectedOperation(details);
    } catch (error) {
      console.error("Error loading operation details:", error);
      setSelectedOperation({ error: "加载操作详情失败" });
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleLoadRaw = async () => {
    if (!currentBank || !selectedOperation?.operation_id) return;

    setLoadingPayload(true);
    try {
      const opId = selectedOperation.operation_id;
      const details = await client.getOperationStatus(currentBank, opId, {
        includePayload: true,
      });
      setSelectedOperation(details);
      setPayloadLoadedFor(opId);
    } catch (error) {
      console.error("Error loading raw payload:", error);
    } finally {
      setLoadingPayload(false);
    }
  };

  useEffect(() => {
    if (currentBank) {
      loadOperations(statusFilter, offset, taskTypeFilter);
      const interval = setInterval(
        () => loadOperations(statusFilter, offset, taskTypeFilter),
        5000
      );
      return () => clearInterval(interval);
    }
  }, [currentBank, statusFilter, offset, taskTypeFilter]);

  if (!currentBank) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-semibold">后台操作</h3>
            <button
              onClick={() => loadOperations()}
              className="p-1 rounded hover:bg-muted transition-colors"
              title="刷新操作"
              disabled={loading}
            >
              <RefreshCw
                className={`w-4 h-4 text-muted-foreground hover:text-foreground ${loading ? "animate-spin" : ""}`}
              />
            </button>
          </div>
          <p className="text-sm text-muted-foreground">
            {totalOperations} 个操作
            {statusFilter ? ` (${statusFilter})` : ""}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={taskTypeFilter ?? "all"}
            onValueChange={(val) => handleTaskTypeFilterChange(val === "all" ? null : val)}
          >
            <SelectTrigger className="h-9 w-[180px] text-sm">
              <SelectValue placeholder="全部类型" />
            </SelectTrigger>
            <SelectContent>
              {OPERATION_TYPE_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  <div>
                    <div>{opt.label}</div>
                    {opt.value !== "all" && (
                      <div className="text-xs text-muted-foreground font-mono">{opt.value}</div>
                    )}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <div className="flex gap-1 bg-muted p-1 rounded-lg">
            {[
              { value: null, label: "全部" },
              { value: "pending", label: "等待中" },
              { value: "processing", label: "处理中" },
              { value: "completed", label: "已完成" },
              { value: "failed", label: "失败" },
              { value: "cancelled", label: "已取消" },
            ].map((filter) => (
              <button
                key={filter.value ?? "all"}
                onClick={() => handleFilterChange(filter.value)}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  statusFilter === filter.value
                    ? "bg-background shadow-sm"
                    : "text-muted-foreground hover:text-foreground"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>
        </div>
      </div>
      <div>
        {operations.length > 0 ? (
          <>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[100px]">ID</TableHead>
                    <TableHead>类型</TableHead>
                    <TableHead>创建时间</TableHead>
                    <TableHead>状态</TableHead>
                    <TableHead className="w-[80px]"></TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {operations.map((op) => (
                    <TableRow
                      key={op.id}
                      className={`cursor-pointer hover:bg-muted/50 ${op.status === "failed" ? "bg-red-500/5" : ""}`}
                      onClick={() => handleOperationClick(op.id)}
                    >
                      <TableCell className="font-mono text-xs text-muted-foreground">
                        {op.id.substring(0, 8)}
                      </TableCell>
                      <TableCell className="font-medium">{op.task_type}</TableCell>
                      <TableCell className="text-sm text-muted-foreground">
                        {new Date(op.created_at).toLocaleString()}
                      </TableCell>
                      <TableCell>
                        {op.status === "pending" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                            <Clock className="w-3 h-3" />
                            等待中
                          </span>
                        )}
                        {op.status === "processing" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            处理中
                          </span>
                        )}
                        {op.status === "failed" && (
                          <span
                            className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20"
                            title={op.error_message ?? undefined}
                          >
                            <AlertCircle className="w-3 h-3" />
                            失败
                          </span>
                        )}
                        {op.status === "completed" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <CheckCircle className="w-3 h-3" />
                            已完成
                          </span>
                        )}
                        {op.status === "cancelled" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-500/10 text-gray-600 dark:text-gray-400 border border-gray-500/20">
                            <Ban className="w-3 h-3" />
                            已取消
                          </span>
                        )}
                      </TableCell>
                      <TableCell>
                        {op.status === "pending" && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs text-muted-foreground hover:text-red-600 dark:hover:text-red-400"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleCancelOperation(op.id);
                            }}
                            disabled={cancellingOpId === op.id}
                          >
                            {cancellingOpId === op.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <X className="w-3 h-3 mr-1" />
                            )}
                            {cancellingOpId === op.id ? "" : "取消"}
                          </Button>
                        )}
                        {(op.status === "failed" || op.status === "cancelled") && (
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-7 text-xs text-muted-foreground hover:text-blue-600 dark:hover:text-blue-400"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRetryOperation(op.id);
                            }}
                            disabled={retryingOpId === op.id}
                          >
                            {retryingOpId === op.id ? (
                              <Loader2 className="w-3 h-3 animate-spin" />
                            ) : (
                              <RotateCcw className="w-3 h-3 mr-1" />
                            )}
                            {retryingOpId === op.id ? "" : "重试"}
                          </Button>
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
            {/* Pagination */}
            {totalOperations > limit && (
              <div className="flex items-center justify-between mt-4 pt-4 border-t">
                <p className="text-sm text-muted-foreground">
                  显示第 {offset + 1}-{Math.min(offset + limit, totalOperations)} 条，共{" "}
                  {totalOperations} 条
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(Math.max(0, offset - limit))}
                    disabled={offset === 0}
                  >
                    上一页
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handlePageChange(offset + limit)}
                    disabled={offset + limit >= totalOperations}
                  >
                    下一页
                  </Button>
                </div>
              </div>
            )}
          </>
        ) : (
          <p className="text-muted-foreground text-center py-8 text-sm">
            暂无{statusFilter ? `${statusFilter} ` : ""}操作
          </p>
        )}
      </div>

      {/* Operation Details Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>操作详情</DialogTitle>
            <DialogDescription>
              {selectedOperation?.operation_id && (
                <span className="font-mono text-xs">{selectedOperation.operation_id}</span>
              )}
            </DialogDescription>
          </DialogHeader>
          {loadingDetails ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
            </div>
          ) : selectedOperation ? (
            <div className="space-y-4">
              {selectedOperation.error ? (
                <div className="text-red-600 dark:text-red-400">{selectedOperation.error}</div>
              ) : (
                <>
                  {/* Basic Info */}
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">状态</div>
                      <div className="mt-1">
                        {selectedOperation.status === "pending" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20">
                            <Clock className="w-3 h-3" />
                            等待中
                          </span>
                        )}
                        {selectedOperation.status === "processing" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20">
                            <Loader2 className="w-3 h-3 animate-spin" />
                            处理中
                          </span>
                        )}
                        {selectedOperation.status === "failed" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400 border border-red-500/20">
                            <AlertCircle className="w-3 h-3" />
                            失败
                          </span>
                        )}
                        {selectedOperation.status === "completed" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20">
                            <CheckCircle className="w-3 h-3" />
                            已完成
                          </span>
                        )}
                        {selectedOperation.status === "cancelled" && (
                          <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-500/10 text-gray-600 dark:text-gray-400 border border-gray-500/20">
                            <Ban className="w-3 h-3" />
                            已取消
                          </span>
                        )}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">类型</div>
                      <div className="mt-1 font-mono text-sm">
                        {selectedOperation.operation_type}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">创建时间</div>
                      <div className="mt-1 text-sm">
                        {selectedOperation.created_at
                          ? new Date(selectedOperation.created_at).toLocaleString()
                          : "无"}
                      </div>
                    </div>
                    <div>
                      <div className="text-sm font-medium text-muted-foreground">更新时间</div>
                      <div className="mt-1 text-sm">
                        {selectedOperation.updated_at
                          ? new Date(selectedOperation.updated_at).toLocaleString()
                          : "无"}
                      </div>
                    </div>
                    {selectedOperation.completed_at && (
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">完成时间</div>
                        <div className="mt-1 text-sm">
                          {new Date(selectedOperation.completed_at).toLocaleString()}
                        </div>
                      </div>
                    )}
                    {selectedOperation.result_metadata?.items_count !== undefined && (
                      <div>
                        <div className="text-sm font-medium text-muted-foreground">总条目数</div>
                        <div className="mt-1 text-sm">
                          {selectedOperation.result_metadata.items_count}
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Action buttons */}
                  {(selectedOperation.status === "pending" ||
                    selectedOperation.status === "failed" ||
                    selectedOperation.status === "cancelled") && (
                    <div className="flex gap-2">
                      {selectedOperation.status === "pending" && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          onClick={() => handleCancelOperation(selectedOperation.operation_id)}
                          disabled={cancellingOpId === selectedOperation.operation_id}
                        >
                          {cancellingOpId === selectedOperation.operation_id ? (
                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                          ) : (
                            <X className="w-3 h-3 mr-1" />
                          )}
                          取消
                        </Button>
                      )}
                      {(selectedOperation.status === "failed" ||
                        selectedOperation.status === "cancelled") && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="text-xs"
                          onClick={() => handleRetryOperation(selectedOperation.operation_id)}
                          disabled={retryingOpId === selectedOperation.operation_id}
                        >
                          {retryingOpId === selectedOperation.operation_id ? (
                            <Loader2 className="w-3 h-3 animate-spin mr-1" />
                          ) : (
                            <RotateCcw className="w-3 h-3 mr-1" />
                          )}
                          重试
                        </Button>
                      )}
                    </div>
                  )}

                  {/* Metadata */}
                  {selectedOperation.result_metadata &&
                    Object.keys(selectedOperation.result_metadata).length > 0 && (
                      <div>
                        <div className="text-sm font-medium text-muted-foreground mb-2">元数据</div>
                        <pre className="rounded-lg border bg-muted/30 p-3 text-xs font-mono overflow-x-auto max-h-96 whitespace-pre-wrap break-words">
                          {JSON.stringify(selectedOperation.result_metadata, null, 2)}
                        </pre>
                      </div>
                    )}

                  {/* Error Message */}
                  {selectedOperation.error_message && (
                    <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-3">
                      <div className="text-sm font-medium text-red-600 dark:text-red-400 mb-1">
                        错误
                      </div>
                      <div className="text-sm text-red-600/80 dark:text-red-400/80 font-mono">
                        {selectedOperation.error_message}
                      </div>
                    </div>
                  )}

                  {/* Child Operations (for parent operations) */}
                  {selectedOperation.child_operations &&
                    selectedOperation.child_operations.length > 0 && (
                      <div>
                        <div className="text-sm font-medium text-muted-foreground mb-2">
                          子批次（
                          {selectedOperation.result_metadata?.num_sub_batches ||
                            selectedOperation.child_operations.length}
                          ）
                        </div>
                        <Table>
                          <TableHeader>
                            <TableRow>
                              <TableHead className="w-[60px]">索引</TableHead>
                              <TableHead className="w-[100px]">ID</TableHead>
                              <TableHead className="w-[80px]">条目</TableHead>
                              <TableHead>状态</TableHead>
                            </TableRow>
                          </TableHeader>
                          <TableBody>
                            {selectedOperation.child_operations.map((child) => (
                              <TableRow key={child.operation_id}>
                                <TableCell className="text-sm">{child.sub_batch_index}</TableCell>
                                <TableCell className="font-mono text-xs text-muted-foreground">
                                  {child.operation_id.substring(0, 8)}
                                </TableCell>
                                <TableCell className="text-sm">{child.items_count}</TableCell>
                                <TableCell>
                                  {child.status === "pending" && (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-amber-500/10 text-amber-600 dark:text-amber-400">
                                      <Clock className="w-3 h-3" />
                                      等待中
                                    </span>
                                  )}
                                  {child.status === "processing" && (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-blue-500/10 text-blue-600 dark:text-blue-400">
                                      <Loader2 className="w-3 h-3 animate-spin" />
                                      处理中
                                    </span>
                                  )}
                                  {child.status === "failed" && (
                                    <span
                                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-500/10 text-red-600 dark:text-red-400"
                                      title={child.error_message ?? undefined}
                                    >
                                      <AlertCircle className="w-3 h-3" />
                                      失败
                                    </span>
                                  )}
                                  {child.status === "completed" && (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                                      <CheckCircle className="w-3 h-3" />
                                      已完成
                                    </span>
                                  )}
                                  {child.status === "cancelled" && (
                                    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-500/10 text-gray-600 dark:text-gray-400">
                                      <Ban className="w-3 h-3" />
                                      已取消
                                    </span>
                                  )}
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </div>
                    )}

                  {/* Raw payload */}
                  {(() => {
                    const loadedThisOp = payloadLoadedFor === selectedOperation.operation_id;
                    const hasPayload = !!selectedOperation.task_payload;
                    const isParent = !!selectedOperation.result_metadata?.is_parent;
                    return (
                      <div>
                        <div className="flex items-center justify-between mb-2">
                          <div className="text-sm font-medium text-muted-foreground">原始载荷</div>
                          {!loadedThisOp && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="h-7 text-xs"
                              onClick={handleLoadRaw}
                              disabled={loadingPayload}
                            >
                              {loadingPayload ? (
                                <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                              ) : (
                                <Code className="w-3 h-3 mr-1" />
                              )}
                              加载原始数据
                            </Button>
                          )}
                        </div>
                        {hasPayload ? (
                          <pre className="rounded-lg border bg-muted/30 p-3 text-xs font-mono overflow-x-auto max-h-96 whitespace-pre-wrap break-words">
                            {JSON.stringify(selectedOperation.task_payload, null, 2)}
                          </pre>
                        ) : loadedThisOp ? (
                          <p className="text-xs text-muted-foreground">
                            {isParent
                              ? "这是一个父操作 — 原始载荷存储在每个子批次中。请打开子操作查看其载荷。"
                              : "此操作没有存储原始载荷。"}
                          </p>
                        ) : (
                          <p className="text-xs text-muted-foreground">
                            显示操作提交时的完整参数（可能较大）。
                          </p>
                        )}
                      </div>
                    );
                  })()}
                </>
              )}
            </div>
          ) : null}
        </DialogContent>
      </Dialog>
    </div>
  );
}
