'use client';

import { useState, useEffect } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';

interface Entity {
  id: string;
  canonical_name: string;
  mention_count: number;
  first_seen?: string;
  last_seen?: string;
  metadata?: Record<string, any>;
}

interface EntityDetail extends Entity {
  observations: Array<{
    text: string;
    mentioned_at?: string;
  }>;
}

export function EntitiesView() {
  const { currentBank } = useBank();
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedEntity, setSelectedEntity] = useState<EntityDetail | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  const loadEntities = async () => {
    if (!currentBank) return;

    setLoading(true);
    try {
      const result: any = await client.listEntities({
        bank_id: currentBank,
        limit: 100,
      });
      setEntities(result.items || []);
    } catch (error) {
      console.error('Error loading entities:', error);
      alert('Error loading entities: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const loadEntityDetail = async (entityId: string) => {
    if (!currentBank) return;

    setLoadingDetail(true);
    try {
      const result: any = await client.getEntity(entityId, currentBank);
      setSelectedEntity(result);
    } catch (error) {
      console.error('Error loading entity detail:', error);
      alert('Error loading entity detail: ' + (error as Error).message);
    } finally {
      setLoadingDetail(false);
    }
  };

  const regenerateObservations = async () => {
    if (!currentBank || !selectedEntity) return;

    setRegenerating(true);
    try {
      await client.regenerateEntityObservations(selectedEntity.id, currentBank);
      // Reload entity detail to show new observations
      await loadEntityDetail(selectedEntity.id);
    } catch (error) {
      console.error('Error regenerating observations:', error);
      alert('Error regenerating observations: ' + (error as Error).message);
    } finally {
      setRegenerating(false);
    }
  };

  useEffect(() => {
    if (currentBank) {
      loadEntities();
      setSelectedEntity(null);
    }
  }, [currentBank]);

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString();
  };

  return (
    <div className="flex gap-4">
      {/* Entity List */}
      <div className="flex-1">
        {loading ? (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-4xl mb-2">⏳</div>
              <div className="text-sm text-muted-foreground">Loading entities...</div>
            </div>
          </div>
        ) : entities.length > 0 ? (
          <>
            <div className="mb-4 text-sm text-muted-foreground">
              {entities.length} entities
            </div>
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Mentions</TableHead>
                  <TableHead>First Seen</TableHead>
                  <TableHead>Last Seen</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {entities.map((entity) => (
                  <TableRow
                    key={entity.id}
                    onClick={() => loadEntityDetail(entity.id)}
                    className={`cursor-pointer ${
                      selectedEntity?.id === entity.id ? 'bg-accent' : ''
                    }`}
                  >
                    <TableCell className="text-xs text-muted-foreground font-mono" title={entity.id}>{entity.id.slice(0, 8)}...</TableCell>
                    <TableCell className="font-medium">{entity.canonical_name}</TableCell>
                    <TableCell>{entity.mention_count}</TableCell>
                    <TableCell>{formatDate(entity.first_seen)}</TableCell>
                    <TableCell>{formatDate(entity.last_seen)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
          </>
        ) : (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-4xl mb-2">👥</div>
              <div className="text-sm text-muted-foreground">No entities found</div>
              <div className="text-xs text-muted-foreground mt-1">Entities are extracted from facts when memories are added.</div>
            </div>
          </div>
        )}
      </div>

      {/* Entity Detail Panel */}
      {selectedEntity && (
        <div className="w-96 bg-card border-2 border-primary rounded-lg p-4">
          <div className="flex justify-between items-start mb-4">
            <h3 className="text-lg font-bold text-card-foreground">{selectedEntity.canonical_name}</h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setSelectedEntity(null)}
            >
              X
            </Button>
          </div>

          <div className="text-sm text-muted-foreground mb-4">
            <div className="font-mono text-xs mb-1" title={selectedEntity.id}>ID: {selectedEntity.id}</div>
            <div>Mentions: {selectedEntity.mention_count}</div>
            <div>First seen: {formatDate(selectedEntity.first_seen)}</div>
            <div>Last seen: {formatDate(selectedEntity.last_seen)}</div>
          </div>

          <div className="mb-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-bold text-card-foreground">Observations</h4>
              <Button
                onClick={regenerateObservations}
                disabled={regenerating}
                variant="secondary"
                size="sm"
              >
                {regenerating ? 'Regenerating...' : 'Regenerate'}
              </Button>
            </div>

            {loadingDetail ? (
              <div className="text-muted-foreground text-sm">Loading observations...</div>
            ) : selectedEntity.observations && selectedEntity.observations.length > 0 ? (
              <ul className="space-y-2">
                {selectedEntity.observations.map((obs, idx) => (
                  <li key={idx} className="p-2 bg-muted rounded text-sm">
                    <div>{obs.text}</div>
                    {obs.mentioned_at && (
                      <div className="text-xs text-muted-foreground mt-1">
                        {formatDate(obs.mentioned_at)}
                      </div>
                    )}
                  </li>
                ))}
              </ul>
            ) : (
              <div className="text-muted-foreground text-sm">
                No observations yet. Click &quot;Regenerate&quot; to generate observations from facts.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
