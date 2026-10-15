import React from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { ClusterExplorer3D } from '../visualization/ClusterExplorer3D';
import { StateView } from '../common/StateView';
import { getReadinessColor, getReadinessTier, ELI5_TRANSLATIONS } from '../../lib/utils';
import {
  Scale,
  Users,
  Sparkles,
  Copy,
  Eye,
  Tag,
  CheckCircle2,
  BarChart2,
} from 'lucide-react';

export const DimensionsTab: React.FC = () => {
  const { report, isLoadingReport, reportError, refreshReport, selectedRun, selectedDataset, audienceMode } = useApp();
  const isSimple = audienceMode === 'simple';

  if (!selectedRun) {
    return (
      <StateView state="empty" emptyTitle="No Audit Selected">
        <div />
      </StateView>
    );
  }

  const results = report?.results;
  const dimensionScores = results?.readiness?.dimension_scores || {};

  const dimensions = [
    {
      key: 'distribution',
      title: 'Class Balance',
      icon: <Scale className="w-5 h-5 text-indigo-400" />,
      score: dimensionScores.distribution?.score ?? 80,
      weight: dimensionScores.distribution?.weight ?? 0.2,
      rawMetric: results?.distribution?.imbalance_ratio !== undefined ? `Imbalance Ratio: ${results.distribution.imbalance_ratio.toFixed(2)}x` : 'Balanced',
      eli5Key: 'distribution',
    },
    {
      key: 'fairness',
      title: 'Fairness & Representation',
      icon: <Users className="w-5 h-5 text-sky-400" />,
      score: dimensionScores.fairness?.score ?? 75,
      weight: dimensionScores.fairness?.weight ?? 0.15,
      rawMetric: results?.fairness?.worst_absolute_target_gap !== undefined ? `Worst Gap: ${(results.fairness.worst_absolute_target_gap * 100).toFixed(1)}%` : 'No Metadata Specified',
      eli5Key: 'fairness',
    },
    {
      key: 'quality',
      title: 'Image Quality & Defects',
      icon: <Sparkles className="w-5 h-5 text-emerald-400" />,
      score: dimensionScores.quality?.score ?? 85,
      weight: dimensionScores.quality?.weight ?? 0.2,
      rawMetric: results?.quality?.defect_rate_pct !== undefined ? `Defect Rate: ${results.quality.defect_rate_pct.toFixed(1)}%` : '0% Defects',
      eli5Key: 'quality',
    },
    {
      key: 'duplicates',
      title: 'Duplicates & Leakage',
      icon: <Copy className="w-5 h-5 text-amber-400" />,
      score: dimensionScores.duplicates?.score ?? 60,
      weight: dimensionScores.duplicates?.weight ?? 0.2,
      rawMetric: `${results?.duplicates?.cross_split_duplicate_groups || 0} cross-split leaks • ${results?.duplicates?.near_duplicate_count || 0} duplicates`,
      eli5Key: 'duplicates',
    },
    {
      key: 'diversity',
      title: 'Visual Diversity',
      icon: <Eye className="w-5 h-5 text-purple-400" />,
      score: dimensionScores.diversity?.score ?? 78,
      weight: dimensionScores.diversity?.weight ?? 0.15,
      rawMetric: results?.diversity?.cluster_entropy !== undefined ? `Entropy: ${results.diversity.cluster_entropy.toFixed(2)} (k=${results.diversity.selected_k || 3})` : 'Normal',
      eli5Key: 'diversity',
    },
    {
      key: 'labels',
      title: 'Label Integrity',
      icon: <Tag className="w-5 h-5 text-rose-400" />,
      score: dimensionScores.labels?.score ?? 70,
      weight: dimensionScores.labels?.weight ?? 0.1,
      rawMetric: results?.labels?.label_noise_rate_pct !== undefined ? `Label Noise: ${results.labels.label_noise_rate_pct.toFixed(1)}%` : '0% Noise',
      eli5Key: 'labels',
    },
  ];

  const classCounts = results?.distribution?.class_counts || {};
  const noiseMatrix = results?.labels?.noise_matrix || {};

  return (
    <StateView
      state={isLoadingReport ? 'loading' : reportError ? 'error' : !report ? 'empty' : 'ideal'}
      errorMessage={reportError}
      onRetry={refreshReport}
    >
      <div className="space-y-6">
        {/* Header & Subtitle */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-bold text-zinc-900 dark:text-white font-sans">
              6 Diagnostic Integrity Dimensions
            </h2>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              {isSimple
                ? 'Each health score grades one specific part of your dataset, from photo clarity to fairness.'
                : 'Orthogonal diagnostic metrics normalized to 0–100 scale using bounded sigmoid scoring functions.'}
            </p>
          </div>
        </div>

        {/* 6 Dimension Cards Grid with 3D Tilt */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dimensions.map(dim => {
            const colors = getReadinessColor(dim.score);
            const tier = getReadinessTier(dim.score);
            const translation = ELI5_TRANSLATIONS[dim.eli5Key];

            return (
              <GlassCard
                key={dim.key}
                tilt={true}
                elevation="sm"
                glow={tier === 'ready' ? 'emerald' : tier === 'warning' ? 'amber' : 'rose'}
                className="p-4 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="p-2 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800">
                        {dim.icon}
                      </div>
                      <div>
                        <h4 className="text-xs font-bold text-zinc-900 dark:text-white font-sans">
                          {dim.title}
                        </h4>
                        <span className="text-[10px] text-zinc-500 font-mono">
                          Weight: {(dim.weight * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className={`text-xl font-black font-sans ${colors.text}`}>
                        {Math.round(dim.score)}
                      </span>
                      <span className="text-zinc-400 dark:text-zinc-500 text-xs font-mono">/100</span>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="w-full bg-zinc-200 dark:bg-zinc-800/80 rounded-full h-1.5 mt-3 overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500`}
                      style={{
                        width: `${dim.score}%`,
                        backgroundColor: colors.hex,
                      }}
                    />
                  </div>

                  {/* Plain English vs Stats description */}
                  <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-3 leading-relaxed">
                    {isSimple ? translation.simple : translation.technical}
                  </p>
                </div>

                <div className="mt-3 pt-2.5 border-t border-zinc-200 dark:border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-600 dark:text-zinc-400">
                  <span className="truncate">{dim.rawMetric}</span>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-semibold uppercase ${colors.bg} ${colors.text}`}>
                    {tier}
                  </span>
                </div>
              </GlassCard>
            );
          })}
        </div>

        {/* Interactive 3D Embedding & Outlier Cluster Explorer */}
        {selectedDataset && (
          <div className="pt-2">
            <ClusterExplorer3D runId={selectedRun.id} datasetId={selectedDataset.id} />
          </div>
        )}

        {/* Deep Dive Sub-Panels: Class Distribution & Label Confusion Matrix */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 pt-2">
          {/* Class Distribution Bar Card */}
          <GlassCard tilt={false} elevation="sm" className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <BarChart2 className="w-4 h-4 text-indigo-500 dark:text-indigo-400" />
                <h4 className="text-xs font-bold text-zinc-900 dark:text-white font-sans">
                  Class Distribution & Representation
                </h4>
              </div>
              <span className="text-xs font-mono text-zinc-500 dark:text-zinc-400">
                {Object.keys(classCounts).length} classes
              </span>
            </div>

            {Object.keys(classCounts).length === 0 ? (
              <div className="text-xs text-zinc-500 py-6 text-center">
                No class counts available
              </div>
            ) : (
              <div className="space-y-2 mt-2">
                {Object.entries(classCounts).map(([cls, count]) => {
                  const maxCount = Math.max(...Object.values(classCounts), 1);
                  const pct = Math.round((Number(count) / maxCount) * 100);
                  return (
                    <div key={cls} className="space-y-1">
                      <div className="flex justify-between text-xs font-mono">
                        <span className="text-zinc-800 dark:text-zinc-300 font-medium truncate">{cls}</span>
                        <span className="text-zinc-500 dark:text-zinc-400">{count} images</span>
                      </div>
                      <div className="w-full bg-zinc-200 dark:bg-zinc-800/80 rounded-full h-1.5 overflow-hidden">
                        <div
                          className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </GlassCard>

          {/* Confident Learning Label Noise Review */}
          <GlassCard tilt={false} elevation="sm" className="p-5">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <Tag className="w-4 h-4 text-rose-500 dark:text-rose-400" />
                <h4 className="text-xs font-bold text-zinc-900 dark:text-white font-sans">
                  Confident Learning Label Disagreements
                </h4>
              </div>
              <span className="text-xs font-mono text-rose-700 dark:text-rose-400 bg-rose-500/10 px-2 py-0.5 rounded border border-rose-500/20">
                {results?.labels?.label_noise_rate_pct !== undefined ? `${results.labels.label_noise_rate_pct}% estimated noise` : 'Clean'}
              </span>
            </div>

            <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-3">
              {isSimple
                ? 'Photos where our AI embedding model strongly suspects the human tag is incorrect.'
                : 'Out-of-fold predicted probability matrix thresholded via Northcutt et al. Confident Learning.'}
            </p>

            {Object.keys(noiseMatrix).length === 0 ? (
              <div className="p-6 text-center text-xs text-emerald-700 dark:text-emerald-400 rounded-xl bg-emerald-500/5 border border-emerald-500/20">
                <CheckCircle2 className="w-6 h-6 mx-auto mb-1 text-emerald-600 dark:text-emerald-400" />
                <span>Zero confident label noise detected! All labels match image visual features.</span>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs font-mono">
                  <thead>
                    <tr className="border-b border-zinc-200 dark:border-zinc-800 text-zinc-500 dark:text-zinc-400">
                      <th className="pb-2">Given Label</th>
                      <th className="pb-2">Likely True Label</th>
                      <th className="pb-2 text-right">Disagreements</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-zinc-200 dark:divide-zinc-800/60 text-zinc-800 dark:text-zinc-300">
                    {Object.entries(noiseMatrix).map(([fromLabel, toMap]) =>
                      Object.entries(toMap as Record<string, number>).map(([toLabel, count]) => (
                        <tr key={`${fromLabel}-${toLabel}`}>
                          <td className="py-2 text-rose-600 dark:text-rose-400">{fromLabel}</td>
                          <td className="py-2 text-emerald-600 dark:text-emerald-400">{toLabel}</td>
                          <td className="py-2 text-right font-bold">{count}</td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            )}
          </GlassCard>
        </div>
      </div>
    </StateView>
  );
};
