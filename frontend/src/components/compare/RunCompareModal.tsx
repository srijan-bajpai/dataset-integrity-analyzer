import React, { useState, useEffect } from 'react';
import { useApp } from '../../lib/store';
import { api } from '../../lib/api';
import type { RunComparison } from '../../lib/types';
import {
  GitCompare,
  X,
  TrendingUp,
  RotateCw,
} from 'lucide-react';

export const RunCompareModal: React.FC = () => {
  const { isCompareOpen, setIsCompareOpen, runs, password, audienceMode } = useApp();
  const isSimple = audienceMode === 'simple';

  const completedRuns = runs.filter(r => r.status === 'completed');

  const [runAId, setRunAId] = useState<string>('');
  const [runBId, setRunBId] = useState<string>('');
  const [comparison, setComparison] = useState<RunComparison | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Auto-select initial pair if available
  useEffect(() => {
    if (completedRuns.length >= 2) {
      setRunAId(completedRuns[1].id);
      setRunBId(completedRuns[0].id);
    } else if (completedRuns.length === 1) {
      setRunAId(completedRuns[0].id);
      setRunBId(completedRuns[0].id);
    }
  }, [completedRuns.length]);

  const runComparison = async () => {
    if (!runAId || !runBId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await api.compareRuns(runAId, runBId, password);
      setComparison(res);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Comparison failed');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isCompareOpen && runAId && runBId && runAId !== runBId) {
      runComparison();
    }
  }, [runAId, runBId, isCompareOpen]);

  if (!isCompareOpen) return null;

  const delta = comparison?.readiness_score_delta_b_minus_a;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-3xl rounded-2xl glass-panel border border-zinc-700 bg-zinc-900 shadow-2xl p-6 text-zinc-100 max-h-[90vh] overflow-y-auto">
        <button
          onClick={() => setIsCompareOpen(false)}
          className="absolute top-4 right-4 p-1.5 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 mb-5">
          <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
            <GitCompare className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-white">
              Diff Two Audits (Before vs. After Scorecard)
            </h3>
            <p className="text-xs text-zinc-400">
              {isSimple
                ? 'Compare two audit runs to prove how much your dataset improved after cleaning.'
                : 'Differential integrity telemetry evaluating dataset drift, score deltas, and sample redistributions.'}
            </p>
          </div>
        </div>

        {/* Pair Selector Controls */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-zinc-950/70 border border-zinc-800 mb-6">
          <div>
            <label className="block text-xs font-mono font-medium text-zinc-400 mb-1">
              Run A (Baseline / Before)
            </label>
            <select
              value={runAId}
              onChange={e => setRunAId(e.target.value)}
              className="w-full py-2 px-3 rounded-xl bg-zinc-900 border border-zinc-700 text-xs font-mono text-zinc-200 focus:outline-none focus:border-indigo-500"
            >
              {completedRuns.map(r => (
                <option key={r.id} value={r.id}>
                  #{r.id.slice(0, 8)} ({r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Run'})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-mono font-medium text-zinc-400 mb-1">
              Run B (Current / After Fixes)
            </label>
            <select
              value={runBId}
              onChange={e => setRunBId(e.target.value)}
              className="w-full py-2 px-3 rounded-xl bg-zinc-900 border border-zinc-700 text-xs font-mono text-zinc-200 focus:outline-none focus:border-indigo-500"
            >
              {completedRuns.map(r => (
                <option key={r.id} value={r.id}>
                  #{r.id.slice(0, 8)} ({r.created_at ? new Date(r.created_at).toLocaleDateString() : 'Run'})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Results */}
        {loading ? (
          <div className="py-12 text-center text-xs text-zinc-400 flex flex-col items-center gap-2">
            <RotateCw className="w-6 h-6 animate-spin text-indigo-400" />
            <span>Calculating differential telemetry...</span>
          </div>
        ) : error ? (
          <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
            {error}
          </div>
        ) : comparison ? (
          <div className="space-y-5">
            {/* Score Delta Hero Banner */}
            <div className="p-5 rounded-2xl bg-gradient-to-br from-zinc-950 to-zinc-900 border border-zinc-800 text-center">
              <span className="text-[11px] font-mono text-zinc-400 uppercase tracking-wider block mb-1">
                AI Readiness Score Improvement
              </span>
              <div className="flex items-center justify-center gap-3">
                <span
                  className={`text-4xl font-black font-sans ${
                    delta !== null && delta !== undefined && delta >= 0 ? 'text-emerald-400' : 'text-rose-400'
                  }`}
                >
                  {delta !== null && delta !== undefined
                    ? `${delta >= 0 ? '+' : ''}${delta.toFixed(1)} pts`
                    : 'No delta'}
                </span>
                {delta !== null && delta !== undefined && delta > 0 && (
                  <TrendingUp className="w-8 h-8 text-emerald-400" />
                )}
              </div>
              <p className="text-xs text-zinc-400 mt-2 max-w-md mx-auto">
                {isSimple
                  ? (delta && delta > 0
                      ? `Great job! Your fixes boosted overall dataset health by +${delta.toFixed(1)} points.`
                      : 'The scores between both runs are identical or shifted.')
                  : comparison.interpretation}
              </p>
            </div>

            {/* Same Fingerprint Badge */}
            <div className="flex items-center justify-between text-xs font-mono p-3 rounded-xl bg-zinc-900/60 border border-zinc-800">
              <span className="text-zinc-400">Dataset SHA-256 Fingerprint:</span>
              <span
                className={`px-2 py-0.5 rounded font-semibold ${
                  comparison.same_dataset_fingerprint
                    ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                    : 'bg-amber-500/10 text-amber-300 border border-amber-500/20'
                }`}
              >
                {comparison.same_dataset_fingerprint ? 'Identical Dataset Files' : 'Updated / Cleaned Files'}
              </span>
            </div>

            {/* Class Deltas Breakdown */}
            {Object.keys(comparison.class_count_deltas_b_minus_a).length > 0 && (
              <div>
                <h4 className="text-xs font-mono font-semibold uppercase text-zinc-400 mb-2">
                  Sample Count Changes by Class (B - A)
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs font-mono">
                  {Object.entries(comparison.class_count_deltas_b_minus_a).map(([cls, diff]) => (
                    <div
                      key={cls}
                      className="p-2.5 rounded-xl bg-zinc-950/60 border border-zinc-800 flex justify-between"
                    >
                      <span className="text-zinc-300 truncate">{cls}:</span>
                      <span className={`font-bold ${diff > 0 ? 'text-emerald-400' : diff < 0 ? 'text-amber-400' : 'text-zinc-500'}`}>
                        {diff > 0 ? `+${diff}` : diff}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="py-8 text-center text-xs text-zinc-500">
            Select two different completed runs above to view before-and-after differences.
          </div>
        )}
      </div>
    </div>
  );
};
