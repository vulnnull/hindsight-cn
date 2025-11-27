'use client';

import { useBank } from '@/lib/bank-context';

export function BankSelector() {
  const { currentBank, setCurrentBank, banks, loadBanks } = useBank();

  return (
    <div className="bg-card text-card-foreground px-5 py-3 border-b-4 border-primary">
      <div className="flex items-center gap-2.5 text-sm">
        <span className="font-medium">Memory Bank:</span>
        <select
          value={currentBank || ''}
          onChange={(e) => setCurrentBank(e.target.value || null)}
          className="px-3 py-1.5 border-2 border-primary rounded bg-background text-foreground text-sm font-bold cursor-pointer transition-all hover:bg-accent focus:outline-none focus:ring-2 focus:ring-ring"
        >
          <option value="">Select a memory bank...</option>
          {banks.map((bank) => (
            <option key={bank} value={bank}>
              {bank}
            </option>
          ))}
        </select>
        <button
          onClick={loadBanks}
          className="ml-2 px-2 py-1 text-xs bg-primary text-primary-foreground hover:opacity-90 rounded transition-colors"
          title="Refresh memory banks"
        >
          🔄
        </button>
      </div>
    </div>
  );
}
