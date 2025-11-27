'use client';

import { useBank } from '@/lib/bank-context';
import { Search, Sparkles, Database, FileText, Users, Brain } from 'lucide-react';
import { cn } from '@/lib/utils';

type NavItem = 'recall' | 'reflect' | 'data' | 'documents' | 'entities' | 'bank';

interface SidebarProps {
  currentTab: NavItem;
  onTabChange: (tab: NavItem) => void;
}

export function Sidebar({ currentTab, onTabChange }: SidebarProps) {
  const { currentBank } = useBank();

  if (!currentBank) {
    return null;
  }

  const navItems = [
    { id: 'recall' as NavItem, label: 'Recall', icon: Search },
    { id: 'reflect' as NavItem, label: 'Reflect', icon: Sparkles },
    { id: 'data' as NavItem, label: 'Memories', icon: Database },
    { id: 'documents' as NavItem, label: 'Documents', icon: FileText },
    { id: 'entities' as NavItem, label: 'Entities', icon: Users },
    { id: 'bank' as NavItem, label: 'Memory Bank', icon: Brain },
  ];

  return (
    <aside className="w-64 bg-card border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h2 className="text-lg font-semibold text-card-foreground">Navigation</h2>
      </div>

      <nav className="flex-1 p-3">
        <ul className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;

            return (
              <li key={item.id}>
                <button
                  onClick={() => onTabChange(item.id)}
                  className={cn(
                    'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all',
                    isActive
                      ? 'bg-primary text-primary-foreground shadow-sm'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <Icon className="w-5 h-5" />
                  <span>{item.label}</span>
                </button>
              </li>
            );
          })}
        </ul>
      </nav>
    </aside>
  );
}
