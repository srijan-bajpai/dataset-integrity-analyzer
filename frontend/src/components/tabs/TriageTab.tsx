import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { StateView } from '../common/StateView';
import { api } from '../../lib/api';
import type { FlaggedSampleItem } from '../../lib/types';
import {
  FileSearch,
  Download,
  FileCode,
  FileSpreadsheet,
  FileText,
  Copy,
  Tag,
  Sparkles,
  Split,
  Eye,
  X,
} from 'lucide-react';

export const TriageTab: React.FC = () => {
  const { report, selectedRun, selectedDataset, password, audienceMode } = useApp();
  const isSimple = audienceMode === 'simple';

  const [samples, setSamples] = useState<FlaggedSampleItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<string>('all');
  const [selectedSample, setSelectedSample] = useState<FlaggedSampleItem | null>(null);
  const [diffPair, setDiffPair] = useState<{ original: string; duplicate: string; group: number } | null>(null);

  const loadSamples = useCallback(async () => {
    if (!selectedRun || selectedRun.status !== 'completed') return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.getFlaggedSamples(selectedRun.id, 150, 0, true, password);
      setSamples(res.items);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to load flagged samples');
    } finally {
      setLoading(false);
    }
  }, [selectedRun, password]);

  useEffect(() => {
    loadSamples();
  }, [loadSamples]);

  if (!selectedRun) {
    return (
      <StateView state="empty" emptyTitle="No Audit Selected">
        <div />
      </StateView>
    );
  }

  // Filter samples based on selected tag
  const filteredSamples = samples.filter(s => {
    if (filter === 'all') return true;
    if (filter === 'leakage') return s.flags.some(f => f.includes('duplicate') || f.includes('leakage'));
    if (filter === 'labels') return s.flags.some(f => f.includes('mislabel') || f.includes('label'));
    if (filter === 'quality') return s.flags.some(f => f.includes('blurred') || f.includes('contrast') || f.includes('exposed') || f.includes('defect'));
    if (filter === 'outliers') return s.flags.some(f => f.includes('outlier'));
    return true;
  });

  const duplicateGroups = report?.results?.duplicates?.duplicate_groups || [];

  return (
    <div className="space-y-6">
      {/* Top Banner & Export Hub */}
      <GlassCard tilt={false} elevation="sm" className="p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <FileSearch className="w-5 h-5 text-indigo-400" />
              <h2 className="text-base font-bold text-white font-sans">
                Sample Triage & 1-Click Export Center
              </h2>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              {isSimple
                ? 'Review photos flagged by DIA, compare duplicate pairs side-by-side, and download compliance reports.'
                : 'Per-sample diagnostic telemetry, out-of-fold label disagreements, pHash Hamming clusters, and machine-actionable export manifests.'}
            </p>
          </div>

          {/* 1-Click Export Buttons */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              onClick={() => {
                const url = api.getExportUrl(selectedRun.id, 'html', password);
                window.open(url, '_blank');
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-medium shadow-md transition-colors"
              title="Download standalone zero-dependency HTML audit report"
            >
              <FileCode className="w-3.5 h-3.5" />
              <span>HTML Report</span>
            </button>

            <button
              onClick={() => {
                const url = api.getExportUrl(selectedRun.id, 'datasheet_md', password);
                window.open(url, '_blank');
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 text-xs font-medium transition-colors"
              title="Download Gebru et al. Datasheet in Markdown"
            >
              <FileText className="w-3.5 h-3.5 text-zinc-400" />
              <span>Datasheet (MD)</span>
            </button>

            <button
              onClick={() => {
                const url = api.getExportUrl(selectedRun.id, 'manifest_csv', password);
                window.open(url, '_blank');
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 text-xs font-medium transition-colors"
              title="Download Remediation Action Manifest CSV"
            >
              <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
              <span>Remediation CSV</span>
            </button>

            <button
              onClick={() => {
                const url = api.getExportUrl(selectedRun.id, 'samples_csv', password);
                window.open(url, '_blank');
              }}
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 text-xs font-medium transition-colors"
              title="Download raw per-sample metric values CSV"
            >
              <Download className="w-3.5 h-3.5 text-zinc-400" />
              <span>All Samples CSV</span>
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Filter Navigation Pills */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-1.5 bg-zinc-900/60 p-1 rounded-xl border border-zinc-800/80 text-xs">
          <button
            onClick={() => setFilter('all')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors ${
              filter === 'all' ? 'bg-indigo-600 text-white' : 'text-zinc-400 hover:text-zinc-200'
            }`}
          >
            All Flagged ({samples.length})
          </button>
          <button
            onClick={() => setFilter('leakage')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              filter === 'leakage' ? 'bg-rose-500/20 text-rose-300 font-semibold' : 'text-zinc-400 hover:text-rose-400'
            }`}
          >
            <Split className="w-3.5 h-3.5" />
            <span>Cross-Split Leaks</span>
          </button>
          <button
            onClick={() => setFilter('labels')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              filter === 'labels' ? 'bg-amber-500/20 text-amber-300 font-semibold' : 'text-zinc-400 hover:text-amber-400'
            }`}
          >
            <Tag className="w-3.5 h-3.5" />
            <span>Suspected Bad Labels</span>
          </button>
          <button
            onClick={() => setFilter('quality')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              filter === 'quality' ? 'bg-sky-500/20 text-sky-300 font-semibold' : 'text-zinc-400 hover:text-sky-400'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>Blur / Quality Defects</span>
          </button>
          <button
            onClick={() => setFilter('outliers')}
            className={`px-3 py-1.5 rounded-lg font-medium transition-colors flex items-center gap-1.5 ${
              filter === 'outliers' ? 'bg-purple-500/20 text-purple-300 font-semibold' : 'text-zinc-400 hover:text-purple-400'
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            <span>Visual Outliers</span>
          </button>
        </div>

        {/* Duplicate Groups Quick Comparator Pill */}
        {duplicateGroups.length > 0 && (
          <button
            onClick={() => {
              const g = duplicateGroups[0];
              if (g && g.sample_refs.length >= 2) {
                setDiffPair({ original: g.sample_refs[0], duplicate: g.sample_refs[1], group: g.group_id });
              }
            }}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/30 text-xs font-mono transition-colors"
          >
            <Copy className="w-3.5 h-3.5" />
            <span>Compare Duplicate Pair (#{duplicateGroups[0]?.group_id || 1})</span>
          </button>
        )}
      </div>

      {/* Visual Image Grid of Problem Samples */}
      <StateView
        state={loading ? 'loading' : error ? 'error' : filteredSamples.length === 0 ? 'empty' : 'ideal'}
        errorMessage={error}
        onRetry={loadSamples}
        emptyTitle="No Flagged Samples Found"
        emptyDescription="This dataset category does not have any flagged issues under the selected filter."
      >
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3.5">
          {filteredSamples.map(sample => {
            const isMislabel = sample.flags.some(f => f.includes('mislabel'));
            const isDuplicate = sample.flags.some(f => f.includes('duplicate'));
            const isBlur = sample.flags.some(f => f.includes('blurred'));
            const isOutlier = sample.flags.some(f => f.includes('outlier'));

            return (
              <div
                key={sample.sample_ref}
                onClick={() => setSelectedSample(sample)}
                className="group relative rounded-xl overflow-hidden glass-card border border-zinc-800 hover:border-zinc-600 cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-lg flex flex-col"
              >
                {/* Thumbnail */}
                <div className="relative aspect-square w-full bg-zinc-900 overflow-hidden">
                  {selectedDataset ? (
                    <img
                      src={api.getSampleImageUrl(selectedDataset.id, sample.sample_ref, password)}
                      alt={sample.sample_ref}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      loading="lazy"
                      onError={e => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                  ) : null}

                  {/* Flag Badges Overlay */}
                  <div className="absolute top-1.5 left-1.5 flex flex-wrap gap-1">
                    {isMislabel && (
                      <span className="px-1.5 py-0.5 rounded bg-rose-600/90 text-white text-[9px] font-bold font-mono">
                        BAD LABEL
                      </span>
                    )}
                    {isDuplicate && (
                      <span className="px-1.5 py-0.5 rounded bg-amber-600/90 text-white text-[9px] font-bold font-mono">
                        DUPE
                      </span>
                    )}
                    {isBlur && (
                      <span className="px-1.5 py-0.5 rounded bg-sky-600/90 text-white text-[9px] font-bold font-mono">
                        BLUR
                      </span>
                    )}
                    {isOutlier && (
                      <span className="px-1.5 py-0.5 rounded bg-purple-600/90 text-white text-[9px] font-bold font-mono">
                        OUTLIER
                      </span>
                    )}
                  </div>
                </div>

                {/* Footer Info */}
                <div className="p-2 text-left bg-zinc-950/80 border-t border-zinc-800/80">
                  <div className="text-[11px] font-mono text-zinc-200 truncate font-semibold">
                    {sample.sample_ref}
                  </div>
                  <div className="flex items-center justify-between text-[10px] text-zinc-400 mt-0.5">
                    <span className="truncate">{sample.ground_truth_class || 'unlabelled'}</span>
                    <span className="font-mono text-zinc-500 uppercase">{sample.split}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </StateView>

      {/* Side-by-Side Duplicate / Leakage Comparator Modal */}
      {diffPair && selectedDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="relative w-full max-w-2xl rounded-2xl glass-panel border border-zinc-700 bg-zinc-900 shadow-2xl p-6 text-zinc-100">
            <button
              onClick={() => setDiffPair(null)}
              className="absolute top-4 right-4 p-1.5 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-4">
              <Copy className="w-5 h-5 text-amber-400" />
              <div>
                <h3 className="text-sm font-bold text-white">
                  Side-by-Side Duplicate & Leakage Comparator (Group #{diffPair.group})
                </h3>
                <span className="text-xs text-zinc-400 font-mono">
                  Perceptual Hash Similarity (pHash distance &lt;= 6)
                </span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              {/* Image A */}
              <div className="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800 text-center">
                <span className="text-xs font-mono font-bold text-zinc-300 block mb-2 truncate">
                  Image A: {diffPair.original}
                </span>
                <img
                  src={api.getSampleImageUrl(selectedDataset.id, diffPair.original, password)}
                  alt="Original"
                  className="w-full h-48 object-contain rounded-lg bg-black/40 border border-zinc-800"
                />
              </div>

              {/* Image B */}
              <div className="p-3 rounded-xl bg-zinc-950/70 border border-zinc-800 text-center">
                <span className="text-xs font-mono font-bold text-zinc-300 block mb-2 truncate">
                  Image B: {diffPair.duplicate}
                </span>
                <img
                  src={api.getSampleImageUrl(selectedDataset.id, diffPair.duplicate, password)}
                  alt="Duplicate"
                  className="w-full h-48 object-contain rounded-lg bg-black/40 border border-zinc-800"
                />
              </div>
            </div>

            <div className="mt-4 p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 text-xs text-amber-300">
              <strong>Recommendation:</strong> Prune Image B from the training set or isolate it from the validation/test splits to eliminate evaluation leakage.
            </div>
          </div>
        </div>
      )}

      {/* Flagged Sample Detail Drawer Modal */}
      {selectedSample && selectedDataset && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
          <div className="relative w-full max-w-lg rounded-2xl glass-panel border border-zinc-700 bg-zinc-900 shadow-2xl p-6 text-zinc-100">
            <button
              onClick={() => setSelectedSample(null)}
              className="absolute top-4 right-4 p-1.5 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex gap-4">
              <img
                src={api.getSampleImageUrl(selectedDataset.id, selectedSample.sample_ref, password)}
                alt={selectedSample.sample_ref}
                className="w-28 h-28 object-cover rounded-xl bg-zinc-950 border border-zinc-700 shrink-0"
              />
              <div className="min-w-0">
                <h3 className="text-sm font-bold text-white font-mono truncate">
                  {selectedSample.sample_ref}
                </h3>
                <div className="text-xs text-zinc-400 mt-1">
                  Class: <strong className="text-zinc-200">{selectedSample.ground_truth_class}</strong>
                </div>
                <div className="text-xs text-zinc-400">
                  Split: <strong className="text-zinc-200 uppercase">{selectedSample.split}</strong>
                </div>

                <div className="flex flex-wrap gap-1 mt-2">
                  {selectedSample.flags.map(f => (
                    <span
                      key={f}
                      className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 font-mono text-[10px] border border-zinc-700"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="mt-4 pt-3 border-t border-zinc-800">
              <span className="text-xs font-mono font-semibold uppercase text-zinc-400 block mb-2">
                Sample Telemetry
              </span>
              <div className="max-h-40 overflow-y-auto space-y-1 font-mono text-xs">
                {Object.entries(selectedSample.metrics).map(([k, v]) => (
                  <div key={k} className="flex justify-between py-1 px-2 rounded bg-zinc-950/60 text-zinc-400">
                    <span>{k}</span>
                    <span className="text-zinc-200">{String(v)}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
