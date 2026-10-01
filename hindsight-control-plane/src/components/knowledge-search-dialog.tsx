"use client";

import { useState } from "react";
import { useTranslations } from "next-intl";
import { client, type KnowledgeTagFilter } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Spinner } from "@/components/ui/spinner";
import { JsonViewer } from "@/components/ui/json-viewer";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Search } from "lucide-react";
import { KnowledgeSearchResult } from "./knowledge-search-result";
import { KnowledgeTagFilterPanel } from "./knowledge-tag-filter";

function countPages(nodes: TreeResponse["roots"]): number {
  return nodes.reduce(
    (n, node) => n + (node.kind === "page" ? 1 : 0) + countPages(node.children ?? []),
    0
  );
}

type SearchResponse = Awaited<ReturnType<typeof client.searchKnowledgePages>>;
type TreeResponse = Awaited<ReturnType<typeof client.getKnowledgeTree>>;
type Endpoint = "search" | "tree";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  bankId: string;
  /** Seed query, taken from the sidebar's search box when the dialog opens. */
  initialQuery: string;
  /** The sidebar's tag filter. Edited here in place, so the sidebar follows. */
  tagFilter: KnowledgeTagFilter;
  onTagFilterChange: (filter: KnowledgeTagFilter) => void;
  /** Folder path per node id, from the loaded tree — search returns neither. */
  pathById: Map<string, string>;
  onOpenPage: (pageId: string) => void;
}

/**
 * The knowledge search the sidebar runs, with its knobs exposed and the server's
 * answer shown raw beside the rendered hits. It edits the sidebar's own tag
 * filter and can run it against either endpoint the sidebar calls: search (with
 * a query) or the tree (without one).
 */
export function KnowledgeSearchDialog({
  open,
  onOpenChange,
  bankId,
  initialQuery,
  tagFilter,
  onTagFilterChange,
  pathById,
  onOpenPage,
}: Props) {
  const t = useTranslations("knowledgeBase");
  const [query, setQuery] = useState(initialQuery);
  const [limit, setLimit] = useState(20);
  const [endpoint, setEndpoint] = useState<Endpoint>("search");
  const [response, setResponse] = useState<SearchResponse | null>(null);
  const [treeResponse, setTreeResponse] = useState<TreeResponse | null>(null);
  const [tookMs, setTookMs] = useState<number | null>(null);
  const [searching, setSearching] = useState(false);

  const run = async () => {
    const q = query.trim();
    if (endpoint === "search" && !q) return;
    setSearching(true);
    const started = performance.now();
    try {
      if (endpoint === "tree") {
        setResponse(null);
        setTreeResponse(await client.getKnowledgeTree(bankId, tagFilter));
      } else {
        setTreeResponse(null);
        setResponse(await client.searchKnowledgePages(bankId, q, limit, tagFilter));
      }
      setTookMs(Math.round(performance.now() - started));
    } catch {
      // toast handled by interceptor
      setResponse(null);
      setTreeResponse(null);
    } finally {
      setSearching(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {/* Fixed height, flex column: the panel is the same size empty as it is
          full, so running a search doesn't jump the dialog under the cursor. */}
      <DialogContent className="sm:max-w-3xl flex flex-col h-[70vh] overflow-hidden">
        <DialogHeader>
          <DialogTitle>{t("advancedSearchTitle")}</DialogTitle>
          <DialogDescription>{t("advancedSearchDescription")}</DialogDescription>
        </DialogHeader>

        <Tabs
          value={endpoint}
          onValueChange={(v) => setEndpoint(v as Endpoint)}
          className="shrink-0"
        >
          <TabsList>
            <TabsTrigger value="search">{t("endpointSearch")}</TabsTrigger>
            <TabsTrigger value="tree">{t("endpointTree")}</TabsTrigger>
          </TabsList>
        </Tabs>

        <div className="space-y-1 shrink-0">
          <Label>{t("tagFilterTitle")}</Label>
          <KnowledgeTagFilterPanel bankId={bankId} value={tagFilter} onChange={onTagFilterChange} />
        </div>

        <div className="flex items-end justify-end gap-2 shrink-0">
          <div className="flex-1 space-y-1" hidden={endpoint !== "search"}>
            <Label htmlFor="kb-adv-query">{t("advancedQuery")}</Label>
            <Input
              id="kb-adv-query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && run()}
              placeholder={t("searchPlaceholder")}
            />
          </div>
          <div className="w-24 space-y-1" hidden={endpoint !== "search"}>
            <Label htmlFor="kb-adv-limit">{t("advancedLimit")}</Label>
            <Input
              id="kb-adv-limit"
              type="number"
              min={1}
              max={50}
              value={limit}
              onChange={(e) => setLimit(Math.max(1, Math.min(50, Number(e.target.value) || 1)))}
            />
          </div>
          <Button onClick={run} disabled={searching || (endpoint === "search" && !query.trim())}>
            {searching ? <Spinner size="sm" /> : <Search className="w-4 h-4" />}
            {t("advancedRun")}
          </Button>
        </div>

        {treeResponse ? (
          <div className="flex-1 min-h-0 flex flex-col gap-2">
            <span className="text-xs text-muted-foreground shrink-0">
              {t("advancedMeta", { total: countPages(treeResponse.roots), ms: tookMs ?? 0 })}
            </span>
            <JsonViewer value={treeResponse} className="bg-muted flex-1 overflow-y-auto text-xs" />
          </div>
        ) : !response ? (
          <div className="flex-1 flex items-center justify-center text-sm text-muted-foreground">
            {t("advancedIdle")}
          </div>
        ) : (
          <Tabs defaultValue="results" className="flex-1 flex flex-col min-h-0">
            <div className="flex items-center justify-between gap-2 shrink-0">
              <TabsList>
                <TabsTrigger value="results">{t("advancedResults")}</TabsTrigger>
                <TabsTrigger value="json">{t("advancedJson")}</TabsTrigger>
              </TabsList>
              <span className="text-xs text-muted-foreground">
                {t("advancedMeta", { total: response.total, ms: tookMs ?? 0 })}
              </span>
            </div>

            <TabsContent value="results" className="flex-1 min-h-0 overflow-y-auto">
              {response.results.length === 0 ? (
                <p className="py-8 text-sm text-muted-foreground text-center">{t("searchEmpty")}</p>
              ) : (
                <ul className="divide-y divide-border">
                  {response.results.map((r, i) => (
                    <li key={r.id}>
                      <KnowledgeSearchResult
                        hit={r}
                        rank={i + 1}
                        path={pathById.get(r.id) ?? bankId}
                        onClick={() => {
                          onOpenPage(r.id);
                          onOpenChange(false);
                        }}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </TabsContent>

            <TabsContent value="json" className="flex-1 min-h-0">
              <JsonViewer value={response} className="bg-muted h-full overflow-y-auto text-xs" />
            </TabsContent>
          </Tabs>
        )}
      </DialogContent>
    </Dialog>
  );
}
