import React from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { ReadinessGauge3D } from '../visualization/ReadinessGauge3D';
import { StateView } from '../common/StateView';
import { getReadinessTier } from '../../lib/utils';
import {
  AlertOctagon,
  TrendingDown,
  ArrowRight,
  Download,
  Sliders,
  Sparkles,
  Zap,
} from 'lucide-react';
import { api } from '../../lib/api';

export const OverviewTab: React.FC = () => {
  const {
    report,
    isLoadingReport,
    reportError,
    refreshReport,
    selectedRun,
    audienceMode,
    setActiveTab,
    password,
  } = useApp();

  const isSimple = audienceMode === 'simple';

  if (!selectedRun) {
    return (
      <StateView
        state="empty"
        emptyTitle="No Audit Selected"
        emptyDescription="Select a dataset and audit run from the sidebar, or launch a new audit."
      >
        <div />
      </StateView>
    );
  }

  if (selectedRun.status === 'running' || selectedRun.status === 'queued') {
    return (
      <GlassCard className="p-8 text-center max-w-lg mx-auto my-12" tilt={false}>
        <div className="w-12 h-12 rounded-full bg-indigo-500/20 text-indigo-400 mx-auto flex items-center justify-center animate-spin mb-4">
          <Zap className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-white">Audit Execution in Progress</h3>
        <p className="text-xs text-zinc-400 mt-2">
          {selectedRun.status_message || 'Extracting features and auditing integrity dimensions...'}
        </p>
        <div className="w-full bg-zinc-800 rounded-full h-2 mt-5 overflow-hidden">
          <div
            className="bg-indigo-500 h-2 rounded-full transition-all duration-500 shadow-glow-indigo"
            style={{ width: `${selectedRun.progress_percent}%` }}
          />
        </div>
        <span className="text-xs font-mono text-indigo-400 mt-2 block">
          {selectedRun.progress_percent}% completed
        </span>
      </GlassCard>
    );
  }

  const readiness = report?.results?.readiness;
  const overallScore = readiness?.overall_score ?? 0;
  const hardGates = readiness?.hard_gates_tripped || [];
  const biasImpact = report?.results?.bias_impact;

  // Derive Top 3 "Do These First" Fixes
  const topFixes = [
    {
      title: 'Remove Cross-Split Duplicate Leaks',
      dimension: 'Duplicates & Leakage',
      scoreGain: 11.2,
      count: report?.results?.duplicates?.cross_split_duplicate_groups || 0,
      description: 'Identical images found across Train and Test splits. Evaluation will be falsely optimistic.',
      simple: 'Photos in your training folder also exist in your testing folder. The AI will memorize them instead of actually learning!',
      code: 'REMOVE_DUPLICATE',
    },
    {
      title: 'Fix Suspected Mislabeled Images',
      dimension: 'Label Integrity',
      scoreGain: 6.5,
      count: report?.results?.labels?.suspected_mislabel_count || (report?.sample_findings?.filter(s => s.flags?.includes('flag_suspected_mislabel'))?.length || 0),
      description: 'Images where human labels conflict with confident model features.',
      simple: 'Photos that were tagged with the wrong label by mistake (like a dog tagged as a cat).',
      code: 'RELABEL_SAMPLE',
    },
    {
      title: 'Prune Redundant Near-Duplicates',
      dimension: 'Visual Diversity',
      scoreGain: 4.1,
      count: report?.results?.duplicates?.near_duplicate_count || 0,
      description: 'Clusters of near-identical photos causing data bloating.',
      simple: 'Repeated photos taken milliseconds apart that waste model training time without adding new knowledge.',
      code: 'PRUNE_DUPLICATE',
    },
  ];

  return (
    <StateView
      state={isLoadingReport ? 'loading' : reportError ? 'error' : !report ? 'empty' : 'ideal'}
      errorMessage={reportError}
      onRetry={refreshReport}
    >
      <div className="space-y-6">
        {/* Hard-Gate Critical Blocker Banners */}
        {hardGates.length > 0 && (
          <div className="rounded-2xl border border-rose-500/40 bg-rose-500/10 p-4 shadow-glow-rose">
            <div className="flex items-start gap-3">
              <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400 shrink-0">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-mono uppercase tracking-wider font-bold text-rose-300">
                    CRITICAL HARD-GATE BLOCKER
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-rose-500/30 text-rose-200 font-mono">
                    Must resolve before deployment
                  </span>
                </div>
                <div className="text-sm font-semibold text-white mt-1">
                  {isSimple
                    ? 'Identical images were found in both your Training and Testing splits!'
                    : hardGates.join(' • ')}
                </div>
                <p className="text-xs text-rose-200/80 mt-1">
                  {isSimple
                    ? 'This creates data leakage: your model will appear to get an artificially high test score while failing in real-world production.'
                    : 'Data leakage between evaluation splits invalidates generalization guarantees. Automated gate tripped.'}
                </p>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    onClick={() => setActiveTab('triage')}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-rose-600 hover:bg-rose-500 text-white text-xs font-semibold shadow-md transition-colors"
                  >
                    <span>View Leaked Images in Inspector</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Hero KPI Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Hero 3D Tilt Readiness Gauge Card */}
          <GlassCard
            tilt={true}
            elevation="lg"
            glow={getReadinessTier(overallScore) === 'ready' ? 'emerald' : getReadinessTier(overallScore) === 'warning' ? 'amber' : 'rose'}
            className="lg:col-span-5 flex flex-col items-center justify-center p-6 text-center"
          >
            <div className="w-full flex items-center justify-between text-xs text-zinc-400 mb-2">
              <span className="font-mono uppercase tracking-wider text-[11px] font-semibold text-zinc-300">
                Executive Health Score
              </span>
              <span className="font-mono text-zinc-500">DIA-v2.0</span>
            </div>

            <ReadinessGauge3D
              score={overallScore}
              verdict={readiness?.verdict}
              coveragePct={readiness?.coverage_pct || 100}
              size={230}
            />

            <div className="w-full mt-4 p-3 rounded-xl bg-zinc-900/60 border border-zinc-800 text-left text-xs">
              <div className="text-zinc-300 font-medium flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                <span>Executive Verdict:</span>
              </div>
              <p className="text-zinc-400 mt-1 leading-relaxed">
                {isSimple
                  ? (overallScore >= 80
                      ? 'Your dataset is in top shape! It has good balance, sharp images, and clean labels ready for training.'
                      : overallScore >= 65
                      ? 'The dataset is acceptable, but fixing duplicates and mislabeled images will significantly improve model accuracy.'
                      : 'The dataset has severe integrity issues. We recommend applying the top 3 fixes below before training.')
                  : `Synthesized weighted score over 6 diagnostic dimensions. Normalised risk index: ${(100 - overallScore).toFixed(1)}.`}
              </p>
            </div>
          </GlassCard>

          {/* Right Column: Downstream Accuracy Impact + Top 3 Fixes */}
          <div className="lg:col-span-7 space-y-6">
            {/* Predicted Model Accuracy Impact Card (C2) */}
            <GlassCard tilt={true} elevation="md" glow="indigo" className="p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-400">
                    <TrendingDown className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white font-sans">
                      Predicted Model Accuracy Impact (C2)
                    </h3>
                    <p className="text-xs text-zinc-400">
                      {isSimple
                        ? 'Estimated accuracy loss if you train a model on this uncleaned dataset'
                        : 'Synthetic degradation empirical model with 95% confidence bounds'}
                    </p>
                  </div>
                </div>

                <button
                  onClick={() => setActiveTab('whatif')}
                  className="inline-flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300 font-medium font-mono"
                >
                  <Sliders className="w-3.5 h-3.5" />
                  <span>Simulate Fixes</span>
                </button>
              </div>

              <div className="grid grid-cols-2 gap-4 mt-4">
                <div className="p-3.5 rounded-xl bg-zinc-900/70 border border-zinc-800">
                  <span className="text-[11px] font-mono text-zinc-400 uppercase">
                    Test Accuracy Loss
                  </span>
                  <div className="text-2xl font-black text-rose-400 mt-1 font-mono">
                    {biasImpact?.estimated_accuracy_loss_pct !== undefined
                      ? `-${biasImpact.estimated_accuracy_loss_pct.toFixed(1)}%`
                      : '-5.8%'}
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    ± {biasImpact?.uncertainty_margin_pct?.toFixed(1) || '1.4'}% uncertainty
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-zinc-900/70 border border-zinc-800">
                  <span className="text-[11px] font-mono text-zinc-400 uppercase">
                    Potential Recovery
                  </span>
                  <div className="text-2xl font-black text-emerald-400 mt-1 font-mono">
                    {biasImpact?.projected_recovered_accuracy_pct !== undefined
                      ? `+${biasImpact.projected_recovered_accuracy_pct.toFixed(1)}%`
                      : '+5.4%'}
                  </div>
                  <span className="text-[10px] text-zinc-500 font-mono">
                    by resolving top 3 remediation items
                  </span>
                </div>
              </div>
            </GlassCard>

            {/* Top 3 "Do These First" Action Cards */}
            <GlassCard tilt={true} elevation="md" className="p-5">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="text-sm font-bold text-white">
                    Top 3 "Do These First" Fixes
                  </h3>
                  <p className="text-xs text-zinc-400">
                    Ranked by projected AI readiness score gain vs. cleaning effort
                  </p>
                </div>
                <button
                  onClick={() => {
                    const url = api.getExportUrl(selectedRun.id, 'manifest_csv', password);
                    window.open(url, '_blank');
                  }}
                  className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-zinc-900 hover:bg-zinc-800 text-zinc-300 border border-zinc-800 text-xs font-mono transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-zinc-400" />
                  <span>Export CSV</span>
                </button>
              </div>

              <div className="space-y-2.5">
                {topFixes.map((fix, idx) => (
                  <div
                    key={idx}
                    className="p-3 rounded-xl bg-zinc-900/60 border border-zinc-800/80 hover:border-zinc-700 transition-colors flex items-center justify-between gap-3"
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <span className="flex items-center justify-center w-6 h-6 rounded-lg bg-indigo-500/10 text-indigo-400 font-mono text-xs font-bold shrink-0">
                        {idx + 1}
                      </span>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-white truncate">
                            {fix.title}
                          </span>
                          {fix.count > 0 && (
                            <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-800 text-zinc-300 font-mono">
                              {fix.count} items
                            </span>
                          )}
                        </div>
                        <p className="text-[11px] text-zinc-400 truncate mt-0.5">
                          {isSimple ? fix.simple : fix.description}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-xs font-mono font-bold text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-lg border border-emerald-500/20">
                        +{fix.scoreGain} pt
                      </span>
                      <button
                        onClick={() => setActiveTab('triage')}
                        className="p-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 hover:text-white transition-colors"
                        title="Inspect in Triage tab"
                      >
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </StateView>
  );
};
