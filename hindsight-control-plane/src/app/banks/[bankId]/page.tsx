"use client";

import { useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { toast } from "sonner";
import { BankSelector } from "@/components/bank-selector";
import { Sidebar } from "@/components/sidebar";
import { DataView } from "@/components/data-view";
import { DocumentsView } from "@/components/documents-view";
import { EntitiesView } from "@/components/entities-view";
import { ThinkView } from "@/components/think-view";
import { SearchDebugView } from "@/components/search-debug-view";
import { BankProfileView } from "@/components/bank-profile-view";
import { BankConfigView } from "@/components/bank-config-view";
import { BankStatsView } from "@/components/bank-stats-view";
import { BankOperationsView } from "@/components/bank-operations-view";
import { MentalModelsView } from "@/components/mental-models-view";
import { WebhooksView } from "@/components/webhooks-view";
import { AuditLogsView } from "@/components/audit-logs-view";
import { useFeatures } from "@/lib/features-context";
import { useBank } from "@/lib/bank-context";
import { bankRoute } from "@/lib/bank-url";
import { client } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Brain, Download, Trash2, Loader2, MoreVertical, Pencil, RotateCcw } from "lucide-react";

type NavItem = "recall" | "reflect" | "data" | "documents" | "entities" | "profile";
type DataSubTab = "world" | "experience" | "observations" | "mental-models";
type BankConfigTab = "general" | "configuration" | "webhooks" | "audit-logs";

export default function BankPage() {
  const params = useParams();
  const router = useRouter();
  const searchParams = useSearchParams();
  const { features } = useFeatures();
  const { currentBank: bankId, setCurrentBank, loadBanks } = useBank();

  const view = (searchParams.get("view") || "profile") as NavItem;
  const subTab = (searchParams.get("subTab") || "world") as DataSubTab;
  const bankConfigTab = (searchParams.get("bankConfigTab") || "general") as BankConfigTab;
  const observationsEnabled = features?.observations ?? false;
  const bankConfigEnabled = features?.bank_config_api ?? false;

  // Bank actions state
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [showClearObservationsDialog, setShowClearObservationsDialog] = useState(false);
  const [isClearingObservations, setIsClearingObservations] = useState(false);
  const [isConsolidating, setIsConsolidating] = useState(false);
  const [isRecoveringConsolidation, setIsRecoveringConsolidation] = useState(false);
  const [showResetConfigDialog, setShowResetConfigDialog] = useState(false);
  const [isResettingConfig, setIsResettingConfig] = useState(false);

  const handleTabChange = (tab: NavItem) => {
    if (!bankId) return;
    router.push(bankRoute(bankId, `?view=${tab}`));
  };

  const handleDataSubTabChange = (newSubTab: DataSubTab) => {
    if (!bankId) return;
    router.push(bankRoute(bankId, `?view=data&subTab=${newSubTab}`));
  };

  const handleBankConfigTabChange = (newTab: BankConfigTab) => {
    if (!bankId) return;
    router.push(bankRoute(bankId, `?view=profile&bankConfigTab=${newTab}`));
  };

  const handleDeleteBank = async () => {
    if (!bankId) return;

    setIsDeleting(true);
    try {
      await client.deleteBank(bankId);
      setShowDeleteDialog(false);
      setCurrentBank(null);
      await loadBanks();
      router.push("/");
    } catch (error) {
      // Error toast is shown automatically by the API client interceptor
    } finally {
      setIsDeleting(false);
    }
  };

  const handleClearObservations = async () => {
    if (!bankId) return;

    setIsClearingObservations(true);
    try {
      const result = await client.clearObservations(bankId);
      setShowClearObservationsDialog(false);
      toast.success("成功", {
        description: result.message || "观察已成功清除",
      });
    } catch (error) {
      // Error toast is shown automatically by the API client interceptor
    } finally {
      setIsClearingObservations(false);
    }
  };

  const handleResetConfig = async () => {
    if (!bankId) return;
    setIsResettingConfig(true);
    try {
      await client.resetBankConfig(bankId);
      setShowResetConfigDialog(false);
    } catch {
      // Error toast shown by API client interceptor
    } finally {
      setIsResettingConfig(false);
    }
  };

  const handleTriggerConsolidation = async () => {
    if (!bankId) return;

    setIsConsolidating(true);
    try {
      await client.triggerConsolidation(bankId);
    } catch (error) {
      // Error toast is shown automatically by the API client interceptor
    } finally {
      setIsConsolidating(false);
    }
  };

  const handleRecoverConsolidation = async () => {
    if (!bankId) return;

    setIsRecoveringConsolidation(true);
    try {
      const result = await client.recoverConsolidation(bankId);
      toast.success(
        `已恢复 ${result.retried_count} 条失败的记忆以重新整合`
      );
    } catch (error) {
      // Error toast is shown automatically by the API client interceptor
    } finally {
      setIsRecoveringConsolidation(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <BankSelector />

      <div className="flex flex-1 overflow-hidden">
        <Sidebar currentTab={view} onTabChange={handleTabChange} />

        <main className="flex-1 overflow-y-auto">
          <div className="p-6">
            {/* Bank Configuration Tab */}
            {view === "profile" && (
              <div>
                <div className="flex justify-between items-start mb-6">
                  <div>
                    <h1 className="text-3xl font-bold mb-2 text-foreground">记忆库配置</h1>
                    <p className="text-muted-foreground">
                      管理记忆库设置、配置文件和操作。
                    </p>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="outline" size="sm">
                        操作
                        <MoreVertical className="w-4 h-4 ml-2" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-48">
                      <DropdownMenuItem
                        onClick={async () => {
                          if (!bankId) return;
                          try {
                            const manifest = await client.exportBankTemplate(bankId);
                            const json = JSON.stringify(manifest, null, 2);
                            await navigator.clipboard.writeText(json);
                            toast.success("模板已复制到剪贴板");
                          } catch {
                            toast.error("导出模板失败");
                          }
                        }}
                      >
                        <Download className="w-4 h-4 mr-2" />
                        导出模板
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={handleTriggerConsolidation}
                        disabled={isConsolidating || !observationsEnabled}
                        title={
                          !observationsEnabled ? "观察功能未启用" : undefined
                        }
                      >
                        {isConsolidating ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <Brain className="w-4 h-4 mr-2" />
                        )}
                        {isConsolidating ? "整合中..." : "运行整合"}
                        {!observationsEnabled && (
                          <span className="ml-auto text-xs text-muted-foreground">关闭</span>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={handleRecoverConsolidation}
                        disabled={isRecoveringConsolidation || !observationsEnabled}
                        title={
                          !observationsEnabled ? "观察功能未启用" : undefined
                        }
                      >
                        {isRecoveringConsolidation ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <RotateCcw className="w-4 h-4 mr-2" />
                        )}
                        {isRecoveringConsolidation ? "恢复中..." : "恢复整合"}
                        {!observationsEnabled && (
                          <span className="ml-auto text-xs text-muted-foreground">关闭</span>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuItem
                        onClick={() => setShowClearObservationsDialog(true)}
                        disabled={!observationsEnabled}
                        className="text-amber-600 dark:text-amber-400 focus:text-amber-700 dark:focus:text-amber-300"
                        title={
                          !observationsEnabled ? "观察功能未启用" : undefined
                        }
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        清除观察
                        {!observationsEnabled && (
                          <span className="ml-auto text-xs text-muted-foreground">关闭</span>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setShowResetConfigDialog(true)}
                        disabled={!bankConfigEnabled}
                        className="text-amber-600 dark:text-amber-400 focus:text-amber-700 dark:focus:text-amber-300"
                        title={!bankConfigEnabled ? "记忆库配置 API 已禁用" : undefined}
                      >
                        <RotateCcw className="w-4 h-4 mr-2" />
                        重置配置
                        {!bankConfigEnabled && (
                          <span className="ml-auto text-xs text-muted-foreground">关闭</span>
                        )}
                      </DropdownMenuItem>
                      <DropdownMenuSeparator />
                      <DropdownMenuItem
                        onClick={() => setShowDeleteDialog(true)}
                        className="text-red-600 dark:text-red-400 focus:text-red-700 dark:focus:text-red-300"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        删除记忆库
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>

                {/* Sub-tabs */}
                <div className="mb-6 border-b border-border">
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleBankConfigTabChange("general")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        bankConfigTab === "general"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      概览
                      {bankConfigTab === "general" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                    {bankConfigEnabled && (
                      <button
                        onClick={() => handleBankConfigTabChange("configuration")}
                        className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                          bankConfigTab === "configuration"
                            ? "text-primary"
                            : "text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        配置
                        {bankConfigTab === "configuration" && (
                          <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => handleBankConfigTabChange("webhooks")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        bankConfigTab === "webhooks"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      Webhook
                      {bankConfigTab === "webhooks" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                    <button
                      onClick={() => handleBankConfigTabChange("audit-logs")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        bankConfigTab === "audit-logs"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      审计日志
                      {bankConfigTab === "audit-logs" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                  </div>
                </div>

                {/* Tab content */}
                <div>
                  {bankConfigTab === "general" && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-4">
                        此记忆库的概览统计和后台操作。
                      </p>
                      <div className="space-y-6">
                        <BankStatsView />
                        <BankOperationsView />
                        <BankProfileView hideReflectFields />
                      </div>
                    </div>
                  )}
                  {bankConfigTab === "configuration" && bankConfigEnabled && (
                    <div className="space-y-6">
                      <BankConfigView />
                    </div>
                  )}
                  {bankConfigTab === "webhooks" && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-4">
                        管理 Webhook 端点以接收此记忆库的事件通知。
                      </p>
                      <WebhooksView />
                    </div>
                  )}
                  {bankConfigTab === "audit-logs" && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-4">
                        查看此记忆库上执行的所有操作的审计记录。
                      </p>
                      <AuditLogsView />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Recall Tab */}
            {view === "recall" && (
              <div>
                <h1 className="text-3xl font-bold mb-2 text-foreground">召回</h1>
                <p className="text-muted-foreground mb-6">
                  通过详细的追踪信息和检索方法分析记忆召回。
                </p>
                <SearchDebugView />
              </div>
            )}

            {/* Reflect Tab */}
            {view === "reflect" && (
              <div>
                <h1 className="text-3xl font-bold mb-2 text-foreground">反思</h1>
                <p className="text-muted-foreground mb-6">
                  运行一个代理循环，自主收集证据并从记忆库性格视角推理，生成上下文相关的响应。
                </p>
                <ThinkView />
              </div>
            )}

            {/* Data/Memories Tab */}
            {view === "data" && (
              <div>
                <h1 className="text-3xl font-bold mb-2 text-foreground">记忆</h1>
                <p className="text-muted-foreground mb-6">
                  查看和探索此记忆库中存储的不同类型的记忆。
                </p>

                <div className="mb-6 border-b border-border">
                  <div className="flex gap-1">
                    <button
                      onClick={() => handleDataSubTabChange("world")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        subTab === "world"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      世界常识
                      {subTab === "world" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDataSubTabChange("experience")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        subTab === "experience"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      经历记忆
                      {subTab === "experience" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDataSubTabChange("observations")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        subTab === "observations"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      观察
                      {!observationsEnabled && (
                        <span className="ml-2 text-xs px-1.5 py-0.5 rounded bg-muted text-muted-foreground">
                          关闭
                        </span>
                      )}
                      {subTab === "observations" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                    <button
                      onClick={() => handleDataSubTabChange("mental-models")}
                      className={`px-6 py-3 font-semibold text-sm transition-all relative ${
                        subTab === "mental-models"
                          ? "text-primary"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      思维模型
                      {subTab === "mental-models" && (
                        <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-primary" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  {subTab === "world" && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-4">
                        从外部来源接收的关于世界的客观事实。
                      </p>
                      <DataView key="world" factType="world" />
                    </div>
                  )}
                  {subTab === "experience" && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-4">
                        记忆库自身的行动、交互和第一人称经验。
                      </p>
                      <DataView key="experience" factType="experience" />
                    </div>
                  )}
                  {subTab === "observations" &&
                    (observationsEnabled ? (
                      <div>
                        <p className="text-sm text-muted-foreground mb-4">
                          从事实中合成的整合知识 — 从累积证据中涌现的模式、偏好和学习成果。
                        </p>
                        <DataView key="observations" factType="observation" />
                      </div>
                    ) : (
                      <div className="flex flex-col items-center justify-center py-16 text-center">
                        <div className="text-muted-foreground mb-2">
                          <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="48"
                            height="48"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          >
                            <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2Z" />
                            <path d="M12 8v4" />
                            <path d="M12 16h.01" />
                          </svg>
                        </div>
                        <h3 className="text-lg font-semibold text-foreground mb-1">
                          观察功能未启用
                        </h3>
                        <p className="text-sm text-muted-foreground max-w-md">
                          此服务器上的观察整合功能已禁用。如需启用，请设置{" "}
                          <code className="px-1 py-0.5 bg-muted rounded text-xs">
                            HINDSIGHT_API_ENABLE_OBSERVATIONS=true
                          </code>{" "}
                          。
                        </p>
                      </div>
                    ))}
                  {subTab === "mental-models" && (
                    <div>
                      <p className="text-sm text-muted-foreground mb-4">
                        用户从查询中生成的摘要 — 可在记忆演进时刷新的可复用知识快照。
                      </p>
                      <MentalModelsView key="mental-models" />
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Documents Tab */}
            {view === "documents" && (
              <div>
                <h1 className="text-3xl font-bold mb-2 text-foreground">文档</h1>
                <p className="text-muted-foreground mb-6">
                  管理文档并保留新记忆。
                </p>
                <DocumentsView />
              </div>
            )}

            {/* Entities Tab */}
            {view === "entities" && (
              <div>
                <h1 className="text-3xl font-bold mb-2 text-foreground">实体</h1>
                <p className="text-muted-foreground mb-6">
                  探索记忆中提及的实体（人物、组织、地点）。
                </p>
                <EntitiesView />
              </div>
            )}
          </div>
        </main>
      </div>

      {/* Delete Bank Confirmation Dialog */}
      <AlertDialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>删除记忆库</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>
                  确定要删除记忆库{" "}
                  <span className="font-semibold text-foreground">{bankId}</span> 吗？
                </p>
                <p className="text-red-600 dark:text-red-400 font-medium">
                  此操作不可撤销。所有记忆、实体、文档和记忆库配置将被永久删除。
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isDeleting}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteBank}
              disabled={isDeleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {isDeleting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  删除中...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  删除记忆库
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Reset Configuration Confirmation Dialog */}
      <AlertDialog open={showResetConfigDialog} onOpenChange={setShowResetConfigDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>重置配置</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>
                  确定要重置{" "}
                  <span className="font-semibold text-foreground">{bankId}</span>{" "}
                  的所有配置覆盖吗？
                </p>
                <p className="text-amber-600 dark:text-amber-400 font-medium">
                  所有记忆库级别的设置（保留、观察、反思）将恢复为服务器默认值。这不影响记忆、实体或记忆库配置。
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isResettingConfig}>取消</AlertDialogCancel>
            <AlertDialogAction onClick={handleResetConfig} disabled={isResettingConfig}>
              {isResettingConfig ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  重置中...
                </>
              ) : (
                <>
                  <RotateCcw className="w-4 h-4 mr-2" />
                  重置配置
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Clear Observations Confirmation Dialog */}
      <AlertDialog open={showClearObservationsDialog} onOpenChange={setShowClearObservationsDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>清除观察</AlertDialogTitle>
            <AlertDialogDescription asChild>
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>
                  确定要清除{" "}
                  <span className="font-semibold text-foreground">{bankId}</span>{" "}
                  的所有观察吗？
                </p>
                <p className="text-amber-600 dark:text-amber-400 font-medium">
                  这将删除所有整合知识。观察将在下次整合运行时重新生成。
                </p>
              </div>
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={isClearingObservations}>取消</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleClearObservations}
              disabled={isClearingObservations}
              className="bg-amber-500 text-white hover:bg-amber-600"
            >
              {isClearingObservations ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  清除中...
                </>
              ) : (
                <>
                  <Trash2 className="w-4 h-4 mr-2" />
                  清除观察
                </>
              )}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
