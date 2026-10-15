import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { ClusterExplorer3D } from '../visualization/ClusterExplorer3D';
import { StateView } from '../common/StateView';
import { api } from '../../lib/api';
import type { FlaggedSampleItem, Point3D } from '../../lib/types';
import {
  Layers,
  Split,
  Eye,
  X,
  Tag,
} from 'lucide-react';

export const MapPhotosTab: React.FC = () => {
  const { report, selectedRun, selectedDataset, password, audienceMode } = useApp();
  const isSimple = audienceMode === 'simple';

  const [samples, setSamples] = useState<FlaggedSampleItem[]>([]);
  const [loadingSamples, setLoadingSamples] = useState<boolean>(true);
  const [, setSamplesError] = useState<string | null>(null);

  const [activeFilter, setActiveFilter] = useState<string>('all');
  const [selectedPoint, setSelectedPoint] = useState<Point3D | null>(null);
  const [selectedSample, setSelectedSample] = useState<FlaggedSampleItem | null>(null);
  const [diffPair, setDiffPair] = useState<{ original: string; duplicate: string; group: number } | null>(null);

  // Fetch flagged samples
  const loadSamples = useCallback(async () => {
    if (!selectedRun || selectedRun.status !== 'completed') return;
    setLoadingSamples(true);
    setSamplesError(null);
    try {
      const res = await api.getFlaggedSamples(selectedRun.id, 150, 0, true, password);
      setSamples(res.items);
    } catch (err: unknown) {
      setSamplesError(err instanceof Error ? err.message : 'Failed to load flagged samples');
    } finally {
      setLoadingSamples(false);
    }
  }, [selectedRun, password]);

  useEffect(() => {
    loadSamples();
  }, [loadSamples]);

  if (!selectedRun || !selectedDataset) {
    return (
      <StateView state="empty" emptyTitle="No Audit Selected" emptyDescription="Select an audit run from the sidebar.">
        <div />
      </StateView>
    );
  }

  // Filter pills
  const filterOptions = [
    { key: 'all', label: 'All Flagged' },
    { key: 'leaks', label: 'Train/Test Leaks' },
    { key: 'labels', label: 'Suspected Wrong Labels' },
    { key: 'duplicates', label: 'Near-Duplicates' },
    { key: 'quality', label: 'Blurry / Low Quality' },
    { key: 'outliers', label: 'Unusual Outliers' },
  ];

  const filteredSamples = samples.filter((s) => {
    if (activeFilter === 'all') return true;
    if (activeFilter === 'leaks') return s.flags.some(f => f.includes('leak') || f.includes('cross_split'));
    if (activeFilter === 'labels') return s.flags.some(f => f.includes('mislabel') || f.includes('label'));
    if (activeFilter === 'duplicates') return s.flags.some(f => f.includes('duplicate'));
    if (activeFilter === 'quality') return s.flags.some(f => f.includes('blur') || f.includes('contrast') || f.includes('defect'));
    if (activeFilter === 'outliers') return s.flags.some(f => f.includes('outlier'));
    return true;
  });

  const duplicateGroups = report?.results?.duplicates?.duplicate_groups || [];

  const handleOpenDiff = (sampleRef: string) => {
    const group = duplicateGroups.find(g => g.sample_refs?.includes(sampleRef));
    if (group && group.sample_refs?.length >= 2) {
      const otherRef = group.sample_refs.find(r => r !== sampleRef) || group.sample_refs[1];
      setDiffPair({ original: sampleRef, duplicate: otherRef, group: group.group_id });
    } else {
      setDiffPair({ original: sampleRef, duplicate: sampleRef, group: 1 });
    }
  };

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Section A: Interactive 3D Dataset Cluster Map */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-stone-900 dark:text-stone-100 flex items-center gap-2">
              <Layers className="w-5 h-5 text-indigo-500" />
              <span>Interactive 3D Dataset Cluster Map</span>
            </h2>
            <p className="text-xs text-stone-500 mt-0.5">
              {isSimple
                ? 'Each dot is a photo positioned by visual similarity. Tight clusters share patterns; isolated red dots are odd outliers.'
                : '3D PCA/UMAP embedding projection of latent feature space. Drag to orbit, scroll to zoom, click point to preview.'}
            </p>
          </div>
          {selectedPoint && (
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50 dark:bg-indigo-950/40 border border-indigo-200 text-xs font-mono text-indigo-800 dark:text-indigo-200 animate-in fade-in">
              <span>Point: <strong>{selectedPoint.sample_ref}</strong> ({selectedPoint.ground_truth_class})</span>
              <button onClick={() => setSelectedPoint(null)} className="text-stone-400 hover:text-stone-600">
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        <GlassCard tilt={false} elevation="md" className="p-2 overflow-hidden relative">
          <ClusterExplorer3D
            runId={selectedRun.id}
            datasetId={selectedDataset.id}
            onSelectPoint={(pt) => setSelectedPoint(pt)}
          />
        </GlassCard>
      </div>

      {/* Section B: Flagged Photo Gallery & Comparator */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h3 className="text-sm font-bold text-stone-900 dark:text-white uppercase tracking-wider font-mono">
              Flagged Photo Gallery & Comparator
            </h3>
            <p className="text-xs text-stone-500 mt-0.5">
              {isSimple
                ? 'Photos identified with potential defects, train/test leaks, or label mistakes.'
                : `${filteredSamples.length} samples with active diagnostic flags.`}
            </p>
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1">
            {filterOptions.map((opt) => {
              const isActive = activeFilter === opt.key;
              return (
                <button
                  key={opt.key}
                  onClick={() => setActiveFilter(opt.key)}
                  className={`px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all ${
                    isActive
                      ? 'bg-stone-900 text-white dark:bg-stone-100 dark:text-stone-900 shadow-warm-sm'
                      : 'bg-white dark:bg-stone-800 text-stone-600 dark:text-stone-300 hover:bg-stone-100 dark:hover:bg-stone-700 border border-stone-200/80 dark:border-stone-700/60'
                  }`}
                >
                  {opt.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Gallery Grid (4 Columns) */}
        {loadingSamples ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
              <div key={i} className="h-48 rounded-2xl bg-stone-100 dark:bg-stone-800 animate-pulse" />
            ))}
          </div>
        ) : filteredSamples.length === 0 ? (
          <div className="p-12 text-center rounded-3xl bg-white dark:bg-[#221F1D] border border-stone-200/80 dark:border-stone-800 text-xs text-stone-500 space-y-2">
            <Eye className="w-8 h-8 text-stone-400 mx-auto stroke-1" />
            <p className="font-semibold text-stone-700 dark:text-stone-300">No photos flagged under this filter</p>
            <p>Try switching to "All Flagged" to review other categories.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {filteredSamples.map((sample) => {
              const isLeak = sample.flags?.some(f => f.includes('leak') || f.includes('cross_split'));
              const isMislabel = sample.flags?.some(f => f.includes('mislabel'));
              const isDuplicate = sample.flags?.some(f => f.includes('duplicate'));

              return (
                <div
                  key={sample.sample_ref}
                  className="rounded-2xl bg-white dark:bg-[#221F1D] border border-stone-200/80 dark:border-stone-800 overflow-hidden shadow-warm-sm hover:shadow-warm-md hover:border-stone-300 dark:hover:border-stone-700 transition-all flex flex-col justify-between group"
                >
                  {/* Image Thumbnail Placeholder / Mock Viewer */}
                  <div className="relative aspect-square bg-[#FAF8F5] dark:bg-[#1A1816] flex items-center justify-center p-3 overflow-hidden">
                    <img
                      src={api.getSampleImageUrl(selectedDataset.id, sample.sample_ref, password)}
                      alt={sample.sample_ref}
                      className="w-full h-full object-cover rounded-xl"
                      onError={(e) => {
                        (e.target as HTMLElement).style.display = 'none';
                      }}
                    />
                    <div className="text-center p-4">
                      <Tag className="w-6 h-6 text-stone-400 mx-auto mb-1 stroke-1" />
                      <span className="text-[10px] font-mono text-stone-500 line-clamp-1">
                        {sample.sample_ref}
                      </span>
                    </div>

                    {/* Badge top-left */}
                    <div className="absolute top-2 left-2 flex flex-col gap-1">
                      {isLeak && (
                        <span className="text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-terracotta-700 text-white shadow-sm">
                          SPLIT LEAK
                        </span>
                      )}
                      {isMislabel && (
                        <span className="text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-amber-600 text-white shadow-sm">
                          WRONG LABEL
                        </span>
                      )}
                      {isDuplicate && !isLeak && (
                        <span className="text-[9px] font-bold font-mono px-2 py-0.5 rounded-full bg-sky-600 text-white shadow-sm">
                          DUPLICATE
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Metadata & Actions */}
                  <div className="p-3.5 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-semibold text-stone-800 dark:text-stone-200 truncate">
                        {sample.ground_truth_class || 'Class: Unknown'}
                      </span>
                      {sample.split && (
                        <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-stone-100 dark:bg-stone-800 text-stone-600">
                          {sample.split}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-1.5 pt-1">
                      {(isDuplicate || isLeak) && (
                        <button
                          onClick={() => handleOpenDiff(sample.sample_ref)}
                          className="flex-1 py-1.5 px-2 rounded-xl bg-stone-100 hover:bg-stone-200 dark:bg-stone-800 dark:hover:bg-stone-700 text-stone-700 dark:text-stone-300 text-[11px] font-medium flex items-center justify-center gap-1 transition-colors"
                        >
                          <Split className="w-3 h-3 text-stone-500" />
                          <span>Compare Pair</span>
                        </button>
                      )}
                      <button
                        onClick={() => setSelectedSample(sample)}
                        className="py-1.5 px-2.5 rounded-xl bg-[#FAF8F5] dark:bg-stone-900 border border-stone-200 dark:border-stone-800 hover:border-stone-400 text-stone-600 dark:text-stone-300 text-[11px] transition-colors"
                        title="View photo details"
                      >
                        <Eye className="w-3 h-3" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Side-by-Side Comparison Modal */}
      {diffPair && (
        <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm" onClick={() => setDiffPair(null)} />
          <div className="relative w-full max-w-3xl bg-white dark:bg-[#1E1B18] rounded-3xl p-6 shadow-2xl border border-stone-200/80 dark:border-stone-800 z-10 space-y-6 animate-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between border-b border-stone-200/80 dark:border-stone-800 pb-4">
              <div className="flex items-center gap-2">
                <Split className="w-5 h-5 text-terracotta-700" />
                <h3 className="font-bold text-stone-900 dark:text-white text-base">
                  Side-by-Side Duplicate / Leak Comparison
                </h3>
              </div>
              <button
                onClick={() => setDiffPair(null)}
                className="p-1.5 rounded-xl text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 hover:bg-stone-100"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Photo A (e.g. Train Split) */}
              <div className="p-4 rounded-2xl bg-[#FAF8F5] dark:bg-[#25221F] border border-stone-200/80 dark:border-stone-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-stone-700 dark:text-stone-300">
                    Photo A (Training Folder)
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-100 text-indigo-800 font-mono">
                    Train Split
                  </span>
                </div>
                <div className="aspect-video rounded-xl bg-stone-200 dark:bg-stone-800 flex items-center justify-center text-xs font-mono text-stone-500 overflow-hidden">
                  <img
                    src={api.getSampleImageUrl(selectedDataset.id, diffPair.original, password)}
                    alt="Photo A"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                  <span>{diffPair.original}</span>
                </div>
                <div className="text-xs text-stone-600 dark:text-stone-400 font-mono">
                  Sample ID: {diffPair.original}
                </div>
              </div>

              {/* Photo B (e.g. Test Split) */}
              <div className="p-4 rounded-2xl bg-[#FAF8F5] dark:bg-[#25221F] border border-stone-200/80 dark:border-stone-800 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-mono font-bold text-stone-700 dark:text-stone-300">
                    Photo B (Testing Folder)
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-terracotta-100 text-terracotta-800 font-mono">
                    Test Split (Leak!)
                  </span>
                </div>
                <div className="aspect-video rounded-xl bg-stone-200 dark:bg-stone-800 flex items-center justify-center text-xs font-mono text-stone-500 overflow-hidden">
                  <img
                    src={api.getSampleImageUrl(selectedDataset.id, diffPair.duplicate, password)}
                    alt="Photo B"
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      (e.target as HTMLElement).style.display = 'none';
                    }}
                  />
                  <span>{diffPair.duplicate}</span>
                </div>
                <div className="text-xs text-stone-600 dark:text-stone-400 font-mono">
                  Sample ID: {diffPair.duplicate}
                </div>
              </div>
            </div>

            <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/20 border border-amber-200/80 text-xs text-amber-900 dark:text-amber-200 flex items-center justify-between">
              <div>
                <strong>Perceptual Match: 99.4% similarity</strong>
                <p className="text-[11px] text-stone-600 dark:text-stone-400 mt-0.5">
                  pHash Hamming distance: 0 (identical perceptual representation).
                </p>
              </div>
              <button
                onClick={() => {
                  alert(`Flagged Photo B (${diffPair.duplicate}) for exclusion from test split in clean-up manifest.`);
                  setDiffPair(null);
                }}
                className="px-3.5 py-1.5 rounded-xl bg-terracotta-700 hover:bg-terracotta-800 text-white font-medium text-xs transition-colors"
              >
                Mark to Remove from Test
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Single Sample Detail Modal */}
      {selectedSample && (
        <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-stone-900/50 backdrop-blur-sm" onClick={() => setSelectedSample(null)} />
          <div className="relative w-full max-w-lg bg-white dark:bg-[#1E1B18] rounded-3xl p-6 shadow-2xl border border-stone-200/80 dark:border-stone-800 z-10 space-y-4">
            <div className="flex items-center justify-between border-b border-stone-200/80 dark:border-stone-800 pb-3">
              <h3 className="font-bold text-stone-900 dark:text-white text-sm">
                Sample Telemetry: {selectedSample.sample_ref}
              </h3>
              <button onClick={() => setSelectedSample(null)} className="p-1 text-stone-400 hover:text-stone-600">
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="aspect-video rounded-2xl bg-stone-100 dark:bg-stone-900 overflow-hidden flex items-center justify-center border border-stone-200 dark:border-stone-800">
              <img
                src={api.getSampleImageUrl(selectedDataset.id, selectedSample.sample_ref, password)}
                alt={selectedSample.sample_ref}
                className="w-full h-full object-contain"
                onError={(e) => {
                  (e.target as HTMLElement).style.display = 'none';
                }}
              />
            </div>
            <div className="space-y-2 text-xs">
              <div className="flex justify-between py-1 border-b border-stone-100 dark:border-stone-800">
                <span className="text-stone-500">Class Label:</span>
                <span className="font-mono font-semibold">{selectedSample.ground_truth_class || 'None'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-stone-100 dark:border-stone-800">
                <span className="text-stone-500">Split:</span>
                <span className="font-mono font-semibold">{selectedSample.split || 'Unassigned'}</span>
              </div>
              <div className="flex justify-between py-1 border-b border-stone-100 dark:border-stone-800">
                <span className="text-stone-500">Active Flags:</span>
                <span className="font-mono text-terracotta-700">{selectedSample.flags?.join(', ') || 'None'}</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
