'use client';

import * as React from 'react';
import { Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Check, ChevronsUpDown } from 'lucide-react';
import { cn } from '@/lib/utils';

function BankSelectorInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { currentBank, setCurrentBank, banks } = useBank();
  const [open, setOpen] = React.useState(false);

  const sortedBanks = React.useMemo(() => {
    return [...banks].sort((a, b) => a.localeCompare(b));
  }, [banks]);

  return (
    <div className="bg-card text-card-foreground px-5 py-3 border-b-4 border-primary">
      <div className="flex items-center gap-2.5 text-sm">
        <span className="font-medium">Memory Bank:</span>
        <Popover open={open} onOpenChange={setOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              role="combobox"
              aria-expanded={open}
              className="w-[300px] justify-between font-bold border-2 border-primary hover:bg-accent"
            >
              {currentBank || "Select a memory bank..."}
              <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-[300px] p-0">
            <Command>
              <CommandInput placeholder="Search memory banks..." />
              <CommandList>
                <CommandEmpty>No memory bank found.</CommandEmpty>
                <CommandGroup>
                  {sortedBanks.map((bank) => (
                    <CommandItem
                      key={bank}
                      value={bank}
                      onSelect={(value) => {
                        setCurrentBank(value);
                        setOpen(false);
                        // Preserve current view and subTab when switching banks
                        const view = searchParams.get('view') || 'data';
                        const subTab = searchParams.get('subTab');
                        const queryString = subTab ? `?view=${view}&subTab=${subTab}` : `?view=${view}`;
                        router.push(`/banks/${value}${queryString}`);
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-4 w-4",
                          currentBank === bank ? "opacity-100" : "opacity-0"
                        )}
                      />
                      {bank}
                    </CommandItem>
                  ))}
                </CommandGroup>
              </CommandList>
            </Command>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
}

export function BankSelector() {
  return (
    <Suspense fallback={
      <div className="bg-card text-card-foreground px-5 py-3 border-b-4 border-primary">
        <div className="flex items-center gap-2.5 text-sm">
          <span className="font-medium">Memory Bank:</span>
          <Button
            variant="outline"
            className="w-[300px] justify-between font-bold border-2 border-primary"
            disabled
          >
            Loading...
            <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
          </Button>
        </div>
      </div>
    }>
      <BankSelectorInner />
    </Suspense>
  );
}
