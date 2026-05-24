"use client";

import { useState, useEffect, useCallback } from "react";
import { useBank } from "@/lib/bank-context";
import { client, AuditLogEntry, AuditStatsBucket } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { RefreshCw, ChevronLeft, ChevronRight } from "lucide-react";
import { LineChart, Line, XAxis, Tooltip, ResponsiveContainer } from "recharts";

const ACTION_OPTIONS = [
  { value: "all", label: "所有操作" },
  { value: "retain", label: "记忆入库" },
  { value: "recall", label: "召回" },
  { value: "reflect", label: "反思" },
  { value: "create_bank", label: "创建记忆库" },
  { value: "update_bank", label: "更新记忆库" },
  { value: "delete_bank", label: "删除记忆库" },
  { value: "clear_memories", label: "清除记忆" },
  { value: "consolidation", label: "整合" },
  { value: "batch_retain", label: "批量入库" },
  { value: "create_mental_model", label: "创建思维模型" },
  { value: "refresh_mental_model", label: "刷新思维模型" },
  { value: "delete_mental_model", label: "删除思维模型" },
  { value: "create_directive", label: "创建指令" },
  { value: "delete_directive", label: "删除指令" },
  { value: "file_convert_retain", label: "文件转换入库" },
  { value: "webhook_delivery", label: "Webhook 投递" },
];

const TRANSPORT_OPTIONS = [
  { value: "all", label: "所有传输方式" },
  { value: "http", label: "HTTP" },
  { value: "mcp", label: "MCP" },
  { value: "system", label: "系统" },
];

const PERIOD_OPTIONS = [
  { value: "1d", label: "今天" },
  { value: "7d", label: "过去 7 天" },
  { value: "30d", label: "过去 30 天" },
];

function formatDuration(startedAt: string | null, endedAt: string | null): string {
  if (!startedAt || !endedAt) return "—";
  const start = new Date(startedAt).getTime();
  const end = new Date(endedAt).getTime();
  const ms = end - start;
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function formatDateTime(ts: string | null): string {
  if (!ts) return "—";
  const date = new Date(ts);
  return date.toLocaleString(undefined, {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
}

function formatChartLabel(ts: string, trunc: string): string {
  const date = new Date(ts);
  if (trunc === "hour") {
    return date.toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit" });
  }
  return date.toLocaleDateString(undefined, { month: "short", day: "numeric" });
}

function TransportBadge({ transport }: { transport: string }) {
  const styles: Record<string, string> = {
    http: "bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300",
    mcp: "bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300",
    system: "bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${styles[transport] || styles.system}`}
    >
      {transport}
    </span>
  );
}

// ---- Chart Section ----

function AuditChart({ bankId }: { bankId: string }) {
  const [period, setPeriod] = useState("7d");
  const [chartAction, setChartAction] = useState<string | null>(null);
  const [buckets, setBuckets] = useState<AuditStatsBucket[]>([]);
  const [trunc, setTrunc] = useState("day");
  const [loading, setLoading] = useState(false);

  const loadStats = useCallback(
    async (p: string = period, a: string | null = chartAction) => {
      setLoading(true);
      try {
        const data = await client.getAuditLogStats(bankId, {
          period: p,
          action: a || undefined,
        });
        setBuckets(data.buckets || []);
        setTrunc(data.trunc || "day");
      } catch (error) {
        console.error("Error loading audit stats:", error);
      } finally {
        setLoading(false);
      }
    },
    [bankId, period, chartAction]
  );

  useEffect(() => {
    loadStats();
  }, [bankId]);

  const chartData = buckets.map((b) => ({
    time: formatChartLabel(b.time, trunc),
    total: b.total,
  }));

  return (
    <Card>
      <CardHeader className="pb-2 flex flex-row items-center justify-between space-y-0 gap-3">
        <CardTitle className="text-sm font-semibold">请求量</CardTitle>
        <div className="flex gap-2">
          <Select
            value={chartAction || "all"}
            onValueChange={(v) => {
              const a = v === "all" ? null : v;
              setChartAction(a);
              loadStats(period, a);
            }}
          >
            <SelectTrigger className="w-[160px] h-8 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent position="popper" className="max-h-[300px] overflow-y-auto">
              {ACTION_OPTIONS.map((opt) => (
                <SelectItem key={opt.value} value={opt.value}>
                  {opt.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {PERIOD_OPTIONS.map((opt) => (
            <Button
              key={opt.value}
              variant={period === opt.value ? "default" : "outline"}
              size="sm"
              className="h-8 text-xs"
              onClick={() => {
                setPeriod(opt.value);
                loadStats(opt.value, chartAction);
              }}
            >
              {opt.label}
            </Button>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[120px]">
          {loading ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
            加载中…
            </div>
          ) : chartData.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground text-sm">
              此时间段暂无数据
            </div>
          ) : (
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 5, right: 5, bottom: 0, left: 5 }}>
                <XAxis
                  dataKey="time"
                  tick={{ fontSize: 10 }}
                  axisLine={false}
                  tickLine={false}
                  className="text-muted-foreground"
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "var(--popover)",
                    border: "1px solid var(--border)",
                    borderRadius: "6px",
                    fontSize: "12px",
                    padding: "4px 8px",
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="total"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  dot={false}
                  activeDot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

// ---- Main Component ----

export function AuditLogsView() {
  const { currentBank } = useBank();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [actionFilter, setActionFilter] = useState<string | null>(null);
  const [transportFilter, setTransportFilter] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<string>("all");
  const [limit] = useState(20);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLogEntry | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);

  const getDateRange = useCallback((range: string): { start_date?: string; end_date?: string } => {
    if (range === "all") return {};
    const now = new Date();
    const start = new Date();
    if (range === "1h") start.setHours(now.getHours() - 1);
    else if (range === "1d") start.setDate(now.getDate() - 1);
    else if (range === "7d") start.setDate(now.getDate() - 7);
    else if (range === "30d") start.setDate(now.getDate() - 30);
    return { start_date: start.toISOString() };
  }, []);

  const loadLogs = useCallback(
    async (
      newActionFilter: string | null = actionFilter,
      newTransportFilter: string | null = transportFilter,
      newDateRange: string = dateRange,
      newOffset: number = offset
    ) => {
      if (!currentBank) return;

      setLoading(true);
      try {
        const dates = getDateRange(newDateRange);
        const data = await client.listAuditLogs(currentBank, {
          action: newActionFilter || undefined,
          transport: newTransportFilter || undefined,
          start_date: dates.start_date,
          end_date: dates.end_date,
          limit,
          offset: newOffset,
        });
        setLogs(data.items || []);
        setTotal(data.total || 0);
      } catch (error) {
        console.error("Error loading audit logs:", error);
      } finally {
        setLoading(false);
      }
    },
    [currentBank, actionFilter, transportFilter, dateRange, offset, limit, getDateRange]
  );

  const handleActionFilterChange = (value: string) => {
    const filter = value === "all" ? null : value;
    setActionFilter(filter);
    setOffset(0);
    loadLogs(filter, transportFilter, dateRange, 0);
  };

  const handleTransportFilterChange = (value: string) => {
    const filter = value === "all" ? null : value;
    setTransportFilter(filter);
    setOffset(0);
    loadLogs(actionFilter, filter, dateRange, 0);
  };

  const handleDateRangeChange = (value: string) => {
    setDateRange(value);
    setOffset(0);
    loadLogs(actionFilter, transportFilter, value, 0);
  };

  const handlePageChange = (newOffset: number) => {
    setOffset(newOffset);
    loadLogs(actionFilter, transportFilter, dateRange, newOffset);
  };

  const handleLogClick = (log: AuditLogEntry) => {
    setSelectedLog(log);
    setDialogOpen(true);
  };

  useEffect(() => {
    if (currentBank) {
      loadLogs(actionFilter, transportFilter, dateRange, offset);
    }
  }, [currentBank]);

  const totalPages = Math.ceil(total / limit);
  const currentPage = Math.floor(offset / limit) + 1;

  if (!currentBank) return null;

  return (
    <div className="space-y-6">
      {/* Chart */}
      <AuditChart bankId={currentBank} />

      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <Select value={actionFilter || "all"} onValueChange={handleActionFilterChange}>
          <SelectTrigger className="w-[180px]">
            <SelectValue placeholder="所有操作" />
          </SelectTrigger>
          <SelectContent position="popper" className="max-h-[300px] overflow-y-auto">
            {ACTION_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={transportFilter || "all"} onValueChange={handleTransportFilterChange}>
          <SelectTrigger className="w-[160px]">
            <SelectValue placeholder="所有传输方式" />
          </SelectTrigger>
          <SelectContent position="popper" className="max-h-[300px] overflow-y-auto">
            {TRANSPORT_OPTIONS.map((opt) => (
              <SelectItem key={opt.value} value={opt.value}>
                {opt.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select value={dateRange} onValueChange={handleDateRangeChange}>
          <SelectTrigger className="w-[150px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent position="popper">
            <SelectItem value="all">全部时间</SelectItem>
            <SelectItem value="1h">过去 1 小时</SelectItem>
            <SelectItem value="1d">过去 24 小时</SelectItem>
            <SelectItem value="7d">过去 7 天</SelectItem>
            <SelectItem value="30d">过去 30 天</SelectItem>
          </SelectContent>
        </Select>

        <Button
          variant="outline"
          size="sm"
          onClick={() => loadLogs(actionFilter, transportFilter, dateRange, offset)}
          disabled={loading}
        >
          <RefreshCw className={`w-4 h-4 mr-1 ${loading ? "animate-spin" : ""}`} />
          刷新
        </Button>

        <span className="text-sm text-muted-foreground ml-auto">
          {total} 条
        </span>
      </div>

      {/* Table */}
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-[200px]">时间</TableHead>
            <TableHead>操作</TableHead>
            <TableHead className="w-[100px]">传输</TableHead>
            <TableHead className="w-[100px]">耗时</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {logs.length === 0 ? (
            <TableRow>
              <TableCell colSpan={4} className="text-center text-muted-foreground py-8">
                {loading ? "加载中…" : "暂无审计日志"}
              </TableCell>
            </TableRow>
          ) : (
            logs.map((log) => (
              <TableRow
                key={log.id}
                className="cursor-pointer hover:bg-muted/50"
                onClick={() => handleLogClick(log)}
              >
                <TableCell className="text-sm font-mono">
                  {formatDateTime(log.started_at)}
                </TableCell>
                <TableCell className="font-medium">{log.action}</TableCell>
                <TableCell>
                  <TransportBadge transport={log.transport} />
                </TableCell>
                <TableCell className="text-sm text-muted-foreground font-mono">
                  {formatDuration(log.started_at, log.ended_at)}
                </TableCell>
              </TableRow>
            ))
          )}
        </TableBody>
      </Table>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            第 {currentPage} 页，共 {totalPages} 页
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(Math.max(0, offset - limit))}
              disabled={offset === 0}
            >
              <ChevronLeft className="w-4 h-4 mr-1" />
              上一页
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => handlePageChange(offset + limit)}
              disabled={offset + limit >= total}
            >
              下一页
              <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </div>
        </div>
      )}

      {/* Detail Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>审计日志：{selectedLog?.action}</DialogTitle>
          </DialogHeader>
          {selectedLog && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="text-muted-foreground">操作：</span>{" "}
                  <span className="font-medium">{selectedLog.action}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">传输方式：</span>{" "}
                  <TransportBadge transport={selectedLog.transport} />
                </div>
                <div>
                  <span className="text-muted-foreground">开始时间：</span>{" "}
                  <span className="font-mono">{formatDateTime(selectedLog.started_at)}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">耗时：</span>{" "}
                  <span className="font-mono">
                    {formatDuration(selectedLog.started_at, selectedLog.ended_at)}
                  </span>
                </div>
              </div>

              {selectedLog.request && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">请求</h4>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto max-h-[200px] overflow-y-auto">
                    {JSON.stringify(selectedLog.request, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.response && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">响应</h4>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto max-h-[200px] overflow-y-auto">
                    {JSON.stringify(selectedLog.response, null, 2)}
                  </pre>
                </div>
              )}

              {selectedLog.metadata && Object.keys(selectedLog.metadata).length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">元数据</h4>
                  <pre className="bg-muted p-3 rounded-md text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.metadata, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
