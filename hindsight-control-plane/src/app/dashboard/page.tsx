'use client';

import { useState } from 'react';
import { BankSelector } from '@/components/bank-selector';
import { Sidebar } from '@/components/sidebar';
import { DataView } from '@/components/data-view';
import { DocumentsView } from '@/components/documents-view';
import { EntitiesView } from '@/components/entities-view';
import { ThinkView } from '@/components/think-view';
import { SearchDebugView } from '@/components/search-debug-view';
import { StatsView } from '@/components/stats-view';
import { useBank } from '@/lib/bank-context';

type NavItem = 'recall' | 'reflect' | 'data' | 'documents' | 'entities' | 'bank';
type DataSubTab = 'world' | 'bank' | 'opinion';

export default function DashboardPage() {
  const [currentTab, setCurrentTab] = useState<NavItem>('data');
  const [dataSubTab, setDataSubTab] = useState<DataSubTab>('world');
  const { currentBank } = useBank();

  const DataSubTabButton = ({ tab, label }: { tab: DataSubTab; label: string }) => (
    <button
      onClick={() => setDataSubTab(tab)}
      className={`px-4 py-2 font-semibold text-sm rounded transition-all border-2 ${
        dataSubTab === tab
          ? 'bg-primary text-primary-foreground border-primary'
          : 'bg-background text-foreground border-border hover:bg-accent'
      }`}
    >
      {label}
    </button>
  );

  const NoAgentMessage = () => (
    <div className="flex items-center justify-center h-[calc(100vh-80px)] bg-muted/20">
      <div className="text-center p-10 bg-card rounded-lg border-2 border-border shadow-lg max-w-md">
        <h3 className="text-2xl font-bold mb-3 text-card-foreground">Welcome to Hindsight</h3>
        <p className="text-muted-foreground mb-4">
          Select a memory bank from the dropdown above to get started.
        </p>
        <div className="text-6xl mb-4">🧠</div>
        <p className="text-sm text-muted-foreground">
          The sidebar will appear once you select a memory bank.
        </p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <BankSelector />

      {!currentBank ? (
        <NoAgentMessage />
      ) : (
        <div className="flex flex-1 overflow-hidden">
          <Sidebar currentTab={currentTab} onTabChange={setCurrentTab} />

          <main className="flex-1 overflow-y-auto">
            <div className="p-6">
              {/* Recall Tab */}
              {currentTab === 'recall' && (
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-foreground">Recall Analyzer</h1>
                  <p className="text-muted-foreground mb-6">
                    Analyze memory recall with detailed trace information and retrieval methods.
                  </p>
                  <SearchDebugView />
                </div>
              )}

              {/* Reflect Tab */}
              {currentTab === 'reflect' && (
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-foreground">Reflect</h1>
                  <p className="text-muted-foreground mb-6">
                    Ask questions and get AI-powered answers based on stored memories.
                  </p>
                  <ThinkView />
                </div>
              )}

              {/* Data/Memories Tab */}
              {currentTab === 'data' && (
                <div>
                  <div className="mb-6">
                    <h1 className="text-3xl font-bold mb-2 text-foreground">Memories</h1>
                    <p className="text-muted-foreground mb-4">
                      View and explore different types of memories stored in this memory bank.
                    </p>

                    <div className="flex gap-2">
                      <DataSubTabButton tab="world" label="World Facts" />
                      <DataSubTabButton tab="bank" label="Bank Facts" />
                      <DataSubTabButton tab="opinion" label="Opinions" />
                    </div>
                  </div>

                  <div>
                    {dataSubTab === 'world' && <DataView factType="world" />}
                    {dataSubTab === 'bank' && <DataView factType="bank" />}
                    {dataSubTab === 'opinion' && <DataView factType="opinion" />}
                  </div>
                </div>
              )}

              {/* Documents Tab */}
              {currentTab === 'documents' && (
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-foreground">Documents</h1>
                  <p className="text-muted-foreground mb-6">
                    Manage documents and retain new memories.
                  </p>
                  <DocumentsView />
                </div>
              )}

              {/* Entities Tab */}
              {currentTab === 'entities' && (
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-foreground">Entities</h1>
                  <p className="text-muted-foreground mb-6">
                    Explore entities (people, organizations, places) mentioned in memories.
                  </p>
                  <EntitiesView />
                </div>
              )}

              {/* Memory Bank Tab (Stats & Operations) */}
              {currentTab === 'bank' && (
                <div>
                  <h1 className="text-3xl font-bold mb-2 text-foreground">Memory Bank</h1>
                  <p className="text-muted-foreground mb-6">
                    View statistics and operations for this memory bank.
                  </p>
                  <StatsView />
                </div>
              )}
            </div>
          </main>
        </div>
      )}
    </div>
  );
}
