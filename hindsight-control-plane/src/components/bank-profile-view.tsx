'use client';

import { useState, useEffect } from 'react';
import { client } from '@/lib/api';
import { useBank } from '@/lib/bank-context';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RefreshCw, Save, User, Brain, FileText, Clock } from 'lucide-react';

interface PersonalityTraits {
  openness: number;
  conscientiousness: number;
  extraversion: number;
  agreeableness: number;
  neuroticism: number;
  bias_strength: number;
}

interface BankProfile {
  bank_id: string;
  name: string;
  personality: PersonalityTraits;
  background: string;
}

interface BankStats {
  bank_id: string;
  total_nodes: number;
  total_links: number;
  total_documents: number;
  nodes_by_fact_type: {
    world?: number;
    bank?: number;
    opinion?: number;
  };
  links_by_link_type: {
    temporal?: number;
    semantic?: number;
    entity?: number;
  };
  pending_operations: number;
  failed_operations: number;
}

const TRAIT_LABELS: Record<keyof PersonalityTraits, { label: string; description: string; lowLabel: string; highLabel: string }> = {
  openness: {
    label: 'Openness',
    description: 'Openness to experience - curiosity, creativity, and willingness to try new things',
    lowLabel: 'Practical',
    highLabel: 'Creative'
  },
  conscientiousness: {
    label: 'Conscientiousness',
    description: 'Organization, dependability, and self-discipline',
    lowLabel: 'Flexible',
    highLabel: 'Organized'
  },
  extraversion: {
    label: 'Extraversion',
    description: 'Sociability, assertiveness, and positive emotions',
    lowLabel: 'Reserved',
    highLabel: 'Outgoing'
  },
  agreeableness: {
    label: 'Agreeableness',
    description: 'Cooperation, trust, and altruism',
    lowLabel: 'Skeptical',
    highLabel: 'Trusting'
  },
  neuroticism: {
    label: 'Neuroticism',
    description: 'Emotional instability and tendency toward negative emotions',
    lowLabel: 'Calm',
    highLabel: 'Sensitive'
  },
  bias_strength: {
    label: 'Personality Influence',
    description: 'How strongly personality traits influence opinions and responses',
    lowLabel: 'Neutral',
    highLabel: 'Strong'
  }
};

function PersonalitySlider({
  trait,
  value,
  onChange,
  disabled
}: {
  trait: keyof PersonalityTraits;
  value: number;
  onChange: (value: number) => void;
  disabled?: boolean;
}) {
  const info = TRAIT_LABELS[trait];
  const percentage = Math.round(value * 100);

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-center">
        <label className="text-sm font-medium text-foreground">{info.label}</label>
        <span className="text-sm text-muted-foreground">{percentage}%</span>
      </div>
      <div className="relative">
        <input
          type="range"
          min="0"
          max="100"
          value={percentage}
          onChange={(e) => onChange(parseInt(e.target.value) / 100)}
          disabled={disabled}
          className="w-full h-2 bg-muted rounded-lg appearance-none cursor-pointer accent-primary disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <div className="flex justify-between text-xs text-muted-foreground mt-1">
          <span>{info.lowLabel}</span>
          <span>{info.highLabel}</span>
        </div>
      </div>
      <p className="text-xs text-muted-foreground">{info.description}</p>
    </div>
  );
}

export function BankProfileView() {
  const { currentBank } = useBank();
  const [profile, setProfile] = useState<BankProfile | null>(null);
  const [stats, setStats] = useState<BankStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [editMode, setEditMode] = useState(false);

  // Edit state
  const [editName, setEditName] = useState('');
  const [editBackground, setEditBackground] = useState('');
  const [editPersonality, setEditPersonality] = useState<PersonalityTraits>({
    openness: 0.5,
    conscientiousness: 0.5,
    extraversion: 0.5,
    agreeableness: 0.5,
    neuroticism: 0.5,
    bias_strength: 0.5
  });

  const loadData = async () => {
    if (!currentBank) return;

    setLoading(true);
    try {
      const [profileData, statsData] = await Promise.all([
        client.getBankProfile(currentBank),
        client.getBankStats(currentBank)
      ]);
      setProfile(profileData);
      setStats(statsData as BankStats);

      // Initialize edit state
      setEditName(profileData.name);
      setEditBackground(profileData.background);
      setEditPersonality(profileData.personality);
    } catch (error) {
      console.error('Error loading bank profile:', error);
      alert('Error loading bank profile: ' + (error as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    if (!currentBank) return;

    setSaving(true);
    try {
      await client.updateBankProfile(currentBank, {
        name: editName,
        background: editBackground,
        personality: editPersonality
      });
      await loadData();
      setEditMode(false);
    } catch (error) {
      console.error('Error saving bank profile:', error);
      alert('Error saving bank profile: ' + (error as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    if (profile) {
      setEditName(profile.name);
      setEditBackground(profile.background);
      setEditPersonality(profile.personality);
    }
    setEditMode(false);
  };

  useEffect(() => {
    if (currentBank) {
      loadData();
    }
  }, [currentBank]);

  if (!currentBank) {
    return (
      <Card>
        <CardContent className="p-10 text-center">
          <h3 className="text-xl font-semibold mb-2 text-card-foreground">No Bank Selected</h3>
          <p className="text-muted-foreground">Please select a memory bank from the dropdown above to view its profile.</p>
        </CardContent>
      </Card>
    );
  }

  if (loading && !profile) {
    return (
      <Card>
        <CardContent className="text-center py-10">
          <Clock className="w-12 h-12 mx-auto mb-3 text-muted-foreground animate-pulse" />
          <div className="text-lg text-muted-foreground">Loading profile...</div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with actions */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-foreground">{profile?.name || currentBank}</h2>
          <p className="text-sm text-muted-foreground">Bank ID: {currentBank}</p>
        </div>
        <div className="flex gap-2">
          {editMode ? (
            <>
              <Button
                onClick={handleCancel}
                variant="outline"
                disabled={saving}
              >
                Cancel
              </Button>
              <Button
                onClick={handleSave}
                disabled={saving}
              >
                {saving ? (
                  <>
                    <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </>
                )}
              </Button>
            </>
          ) : (
            <>
              <Button
                onClick={loadData}
                variant="outline"
                size="sm"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button
                onClick={() => setEditMode(true)}
                size="sm"
              >
                Edit Profile
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Stats Overview */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="w-5 h-5" />
              Memory Overview
            </CardTitle>
            <CardDescription>Summary of stored memories and connections</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Total Memories</div>
                <div className="text-2xl font-bold text-foreground">{stats.total_nodes}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Total Links</div>
                <div className="text-2xl font-bold text-foreground">{stats.total_links}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Documents</div>
                <div className="text-2xl font-bold text-foreground">{stats.total_documents}</div>
              </div>
              <div className="bg-muted/50 border border-border rounded-lg p-4 text-center">
                <div className="text-xs text-muted-foreground font-semibold uppercase tracking-wide mb-1">Pending Ops</div>
                <div className="text-2xl font-bold text-foreground">{stats.pending_operations}</div>
              </div>
            </div>

            {/* Memory Type Breakdown */}
            <div className="mt-4 grid grid-cols-3 gap-4">
              <div className="bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg p-3 text-center">
                <div className="text-xs text-blue-600 dark:text-blue-400 font-semibold uppercase tracking-wide mb-1">World Facts</div>
                <div className="text-xl font-bold text-blue-700 dark:text-blue-300">{stats.nodes_by_fact_type?.world || 0}</div>
              </div>
              <div className="bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-800 rounded-lg p-3 text-center">
                <div className="text-xs text-purple-600 dark:text-purple-400 font-semibold uppercase tracking-wide mb-1">Bank Facts</div>
                <div className="text-xl font-bold text-purple-700 dark:text-purple-300">{stats.nodes_by_fact_type?.bank || 0}</div>
              </div>
              <div className="bg-amber-50 dark:bg-amber-950/30 border border-amber-200 dark:border-amber-800 rounded-lg p-3 text-center">
                <div className="text-xs text-amber-600 dark:text-amber-400 font-semibold uppercase tracking-wide mb-1">Opinions</div>
                <div className="text-xl font-bold text-amber-700 dark:text-amber-300">{stats.nodes_by_fact_type?.opinion || 0}</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="w-5 h-5" />
              Basic Information
            </CardTitle>
            <CardDescription>Name and identity for this memory bank</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="text-sm font-medium text-foreground">Display Name</label>
              {editMode ? (
                <Input
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  placeholder="Enter a name for this bank"
                  className="mt-1"
                />
              ) : (
                <p className="mt-1 text-foreground">{profile?.name || 'Unnamed'}</p>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Background */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <FileText className="w-5 h-5" />
              Background
            </CardTitle>
            <CardDescription>Context and background information for this memory bank</CardDescription>
          </CardHeader>
          <CardContent>
            {editMode ? (
              <Textarea
                value={editBackground}
                onChange={(e) => setEditBackground(e.target.value)}
                placeholder="Enter background information..."
                rows={6}
                className="resize-none"
              />
            ) : (
              <p className="text-foreground whitespace-pre-wrap">
                {profile?.background || 'No background information provided.'}
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Personality Traits */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="w-5 h-5" />
            Personality Traits (Big Five)
          </CardTitle>
          <CardDescription>
            These traits influence how the memory bank interprets and responds to information.
            Based on the Big Five personality model.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {(Object.keys(TRAIT_LABELS) as Array<keyof PersonalityTraits>).map((trait) => (
              <PersonalitySlider
                key={trait}
                trait={trait}
                value={editMode ? editPersonality[trait] : (profile?.personality[trait] || 0.5)}
                onChange={(value) => setEditPersonality(prev => ({ ...prev, [trait]: value }))}
                disabled={!editMode}
              />
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
