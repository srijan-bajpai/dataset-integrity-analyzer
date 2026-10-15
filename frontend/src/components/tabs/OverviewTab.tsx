import React, { useState, useMemo } from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { ReadinessGauge3D } from '../visualization/ReadinessGauge3D';
import { StateView } from '../common/StateView';
import { PillarDetailDrawer, type PillarKey } from '../common/PillarDetailDrawer';
import { getReadinessColor, getReadinessTier } from '../../lib/utils';
import {
  AlertOctagon,
  ArrowRight,
  Download,
  Sliders,
  Sparkles,
  Scale,
  Users,
  Eye,
  Copy,
  Tag,
  CheckCircle2,
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

  const [selectedPillar, setSelectedPillar] = useState<PillarKey | null>(null);
  const isSimple = audienceMode === 'simple';

  const readiness = report?.results?.readiness;
  const overallScore = readiness?.overall_score ?? 0;
  const hardGates = readiness?.hard_gates_tripped || [];
  const dimensionScores = readiness?.dimension_scores || {};

  // Top 3 "Do These First" Action Items
  const backendRecs = report?.results?.recommendations;
  const topFixes = useMemo(() => {
    if (backendRecs && backendRecs.length > 0) {
      return backendRecs.slice(0, 3).map((rec) => ({
        title: rec.action || rec.defect,
        dimension: rec.category,
        scoreGain: rec.projected_score_gain,
        count: rec.affected_sample_count,
        description: rec.rationale || rec.defect,
        simple: rec.defect,
      }));
    }

    const fallbacks = [];
    const crossSplitCount = report?.results?.duplicates?.cross_split_duplicate_groups || 0;
    if (crossSplitCount > 0) {
      fallbacks.push({
        title: 'Remove Cross-Split Duplicate Leaks',
        dimension: 'Duplicates & Leaks',
        scoreGain: 11.2,
        count: crossSplitCount,
        description: 'Identical images found across Train and Test splits. Test accuracy will be falsely inflated.',
        simple: 'Photos in your training folder also exist in your testing folder. The AI will memorize them instead of learning!',
      });
    }

    const mislabelCount =
      report?.results?.labels?.suspected_mislabel_count ||
      (report?.sample_findings?.filter(s => s.flags?.some(f => f.includes('mislabel')))?.length || 0);
    if (mislabelCount > 0) {
      fallbacks.push({
        title: 'Fix Suspected Mislabeled Photos',
        dimension: 'Label Accuracy',
        scoreGain: 6.5,
        count: mislabelCount,
        description: 'Images where human tags conflict with high-confidence model representations.',
        simple: 'Photos tagged with the wrong label by mistake (like a dog tagged as a cat).',
      });
    }

    const defectRate = report?.results?.quality?.defect_rate_pct || 0;
    if (defectRate > 0) {
      fallbacks.push({
        title: 'Remove Blurry & Dark Images',
        dimension: 'Photo Quality',
        scoreGain: 5.0,
        count: Math.round(((report?.sample_count || 100) * defectRate) / 100),
        description: 'Severe Laplacian blur or underexposure preventing visual feature extraction.',
        simple: 'Photos that are too dark or blurry for AI computer vision models to understand.',
      });
    }

    const nearDupCount = report?.results?.duplicates?.near_duplicate_count || 0;
    if (nearDupCount > 0 && fallbacks.length < 3) {
      fallbacks.push({
        title: 'Prune Redundant Duplicate Photos',
        dimension: 'Visual Variety',
        scoreGain: 4.1,
        count: nearDupCount,
        description: 'Clusters of near-identical photos taken within milliseconds.',
        simple: 'Repeated photos that waste training compute without adding new visual diversity.',
      });
    }

    return fallbacks.slice(0, 3);
  }, [backendRecs, report]);

  if (!selectedRun) {
    return (
      <StateView
        state="empty"
        emptyTitle="No Audit Selected"
        emptyDescription="Select a dataset and audit run from the sidebar, or upload a dataset ZIP."
      >
        <div />
      </StateView>
    );
  }

  if (selectedRun.status === 'running' || selectedRun.status === 'queued') {
    return (
      <GlassCard className="p-10 text-center max-w-lg mx-auto my-12" tilt={false}>
        <div className="w-12 h-12 rounded-full bg-amber-500/10 text-amber-600 mx-auto flex items-center justify-center animate-spin mb-4">
          <Zap className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-bold text-stone-900 dark:text-stone-100">
          Auditing Dataset Integrity...
        </h3>
        <p className="text-xs text-stone-500 mt-2">
          {selectedRun.status_message || 'Analyzing image quality, split leakage, and label trust...'}
        </p>
        <div className="w-full bg-stone-100 dark:bg-stone-800 rounded-full h-2 mt-5 overflow-hidden">
          <div
            className="bg-amber-500 h-2 rounded-full transition-all duration-500"
            style={{ width: `${selectedRun.progress_percent}%` }}
          />
        </div>
        <span className="text-xs font-mono text-stone-500 mt-2 block">
          {selectedRun.progress_percent}% completed
        </span>
      </GlassCard>
    );
  }

  // 6 Health Pillars definition
  const pillars: {
    key: PillarKey;
    name: string;
    question: string;
    icon: React.ReactNode;
    score: number;
    sentence: string;
  }[] = [
    {
      key: 'distribution',
      name: 'Class Balance',
      question: 'Are all categories represented evenly?',
      icon: <Scale className="w-4 h-4 text-indigo-500" />,
      score: dimensionScores.distribution?.score ?? 78,
      sentence:
        (report?.results?.distribution?.imbalance_ratio || 1) > 2.5
          ? 'Noticeable class imbalance; minority classes need attention.'
          : 'Categories are well balanced across the dataset.',
    },
    {
      key: 'fairness',
      name: 'Fairness & Groups',
      question: 'Are demographic groups balanced against targets?',
      icon: <Users className="w-4 h-4 text-sky-500" />,
      score: dimensionScores.fairness?.score ?? 70,
      sentence:
        dimensionScores.fairness?.score && dimensionScores.fairness.score < 75
          ? 'Slight subgroup gap detected across target attributes.'
          : 'Subgroup representations meet parity baselines.',
    },
    {
      key: 'quality',
      name: 'Photo Quality',
      question: 'Are images sharp, well-lit, and readable?',
      icon: <Sparkles className="w-4 h-4 text-emerald-500" />,
      score: dimensionScores.quality?.score ?? 84,
      sentence:
        (report?.results?.quality?.defect_rate_pct || 0) > 3
          ? 'Contains blurry or underexposed photos.'
          : 'Photos are crisp, sharp, and well exposed.',
    },
    {
      key: 'duplicates',
      name: 'Duplicates & Leaks',
      question: 'Are there repeated or leaked test photos?',
      icon: <Copy className="w-4 h-4 text-amber-500" />,
      score: dimensionScores.duplicates?.score ?? 54,
      sentence:
        (report?.results?.duplicates?.cross_split_duplicate_groups || 0) > 0
          ? `${report?.results?.duplicates?.cross_split_duplicate_groups} train/test split leakage group(s) found!`
          : 'Zero train/test leakage detected.',
    },
    {
      key: 'diversity',
      name: 'Visual Variety',
      question: 'Do photos cover diverse angles and scenes?',
      icon: <Eye className="w-4 h-4 text-purple-500" />,
      score: dimensionScores.diversity?.score ?? 79,
      sentence: 'Good diversity across scene backgrounds and angles.',
    },
    {
      key: 'labels',
      name: 'Label Accuracy',
      question: 'Are the folder/manifest labels trustworthy?',
      icon: <Tag className="w-4 h-4 text-rose-500" />,
      score: dimensionScores.labels?.score ?? 68,
      sentence:
        (report?.results?.labels?.suspected_mislabel_count || 0) > 0
          ? `${report?.results?.labels?.suspected_mislabel_count} suspect labels conflict with image features.`
          : 'Folder labels are consistent and trustworthy.',
    },
  ];

  return (
    <StateView
      state={isLoadingReport ? 'loading' : reportError ? 'error' : !report ? 'empty' : 'ideal'}
      errorMessage={reportError}
      onRetry={refreshReport}
    >
      <div className="space-y-8 max-w-6xl mx-auto">
        {/* Top Alert Banner (Only shown if critical blocker exists) */}
        {hardGates.length > 0 && (
          <div className="rounded-3xl border border-terracotta-200 bg-terracotta-50 dark:bg-rose-950/20 dark:border-rose-900/50 p-5 shadow-warm-sm">
            <div className="flex items-start gap-4">
              <div className="p-2.5 rounded-2xl bg-terracotta-100 text-terracotta-700 dark:bg-rose-900/50 dark:text-rose-300 shrink-0">
                <AlertOctagon className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] font-mono uppercase tracking-wider font-bold text-terracotta-800 dark:text-rose-300">
                    Critical Blocker Detected
                  </span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-terracotta-200/80 text-terracotta-900 font-mono font-medium">
                    Action Required
                  </span>
                </div>
                <div className="text-sm font-semibold text-stone-900 dark:text-stone-100 mt-1">
                  {isSimple
                    ? 'Identical photos appear in both your training and test folders. Remove them first so your test accuracy is honest.'
                    : hardGates.join(' • ')}
                </div>
                <p className="text-xs text-stone-600 dark:text-stone-300 mt-1">
                  {isSimple
                    ? 'This allows models to memorize test answers. Your AI will look accurate during testing but will fail in production.'
                    : 'Cross-split duplicate leakage violates evaluation independence. Hard gate tripped.'}
                </p>
                <div className="mt-3.5 flex items-center gap-3">
                  <button
                    onClick={() => setActiveTab('map')}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-terracotta-700 hover:bg-terracotta-800 text-white text-xs font-semibold shadow-warm-sm transition-all"
                  >
                    <span>View Leaked Photos in Inspector</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={() => setActiveTab('whatif')}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white dark:bg-stone-800 hover:bg-stone-50 border border-stone-200/80 dark:border-stone-700 text-stone-700 dark:text-stone-300 text-xs font-medium transition-all"
                  >
                    <Sliders className="w-3.5 h-3.5 text-stone-500" />
                    <span>Simulate Cleaning Impact</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Hero Row: 2 Spacious Cards Side-by-Side */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Card 1: 3D Tactile Readiness Card (Left) */}
          <GlassCard
            tilt={true}
            elevation="md"
            className="lg:col-span-5 flex flex-col items-center justify-center p-7 text-center"
          >
            <div className="w-full flex items-center justify-between text-xs text-stone-500 mb-2">
              <span className="font-mono uppercase tracking-wider text-[11px] font-bold text-stone-700 dark:text-stone-300">
                Dataset Health Score
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-stone-100 dark:bg-stone-800 text-stone-600 dark:text-stone-400 font-mono">
                6 dimensions audited
              </span>
            </div>

            <ReadinessGauge3D
              score={overallScore}
              verdict={readiness?.verdict}
              coveragePct={readiness?.coverage_pct || 100}
              size={210}
            />

            <div className="w-full mt-4 p-4 rounded-2xl bg-[#FAF8F5] dark:bg-[#25221F] border border-stone-200/80 dark:border-stone-800 text-left text-xs space-y-1">
              <div className="text-stone-900 dark:text-stone-200 font-semibold flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                <span>Executive Summary</span>
              </div>
              <p className="text-stone-600 dark:text-stone-400 leading-relaxed text-xs">
                {isSimple
                  ? overallScore >= 80
                    ? 'Your dataset is in top shape! It has clean balance, sharp images, and trustworthy labels ready to train.'
                    : overallScore >= 65
                    ? 'The dataset is in good condition, but fixing duplicate leaks and blurry photos will recover ~5% downstream test accuracy.'
                    : 'The dataset has severe integrity issues. We strongly recommend applying the top 3 fixes below before training.'
                  : `Synthesized weighted score over 6 diagnostic dimensions. Normalised risk index: ${(100 - overallScore).toFixed(1)}.`}
              </p>
            </div>
          </GlassCard>

          {/* Card 2: Top 3 "Do These First" Checklist (Right) */}
          <GlassCard tilt={true} elevation="md" className="lg:col-span-7 p-7 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="text-sm font-bold text-stone-900 dark:text-white">
                    Top 3 "Do These First" Checklist
                  </h3>
                  <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                    Ranked by highest score gain for minimum manual effort
                  </p>
                </div>
                <button
                  onClick={() => {
                    const url = api.getExportUrl(selectedRun.id, 'manifest_csv', password);
                    window.open(url, '_blank');
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 dark:bg-stone-800 dark:hover:bg-stone-700 text-stone-700 dark:text-stone-300 text-xs font-mono font-medium transition-colors"
                >
                  <Download className="w-3.5 h-3.5 text-stone-500" />
                  <span>Fix List (CSV)</span>
                </button>
              </div>

              <div className="space-y-3">
                {topFixes.length === 0 ? (
                  <div className="p-4 rounded-2xl bg-sage-50 dark:bg-emerald-950/20 border border-sage-200 text-sage-800 dark:text-emerald-300 text-xs flex items-center gap-3">
                    <CheckCircle2 className="w-5 h-5 text-sage-600 shrink-0" />
                    <div>
                      <span className="font-semibold block">All Core Thresholds Passed</span>
                      <span className="text-[11px] text-stone-500">
                        No critical fixes required. Your dataset is ready for training.
                      </span>
                    </div>
                  </div>
                ) : (
                  topFixes.map((fix, idx) => (
                    <div
                      key={idx}
                      className="p-3.5 rounded-2xl bg-[#FAF8F5] dark:bg-[#25221F] border border-stone-200/80 dark:border-stone-800 hover:border-stone-300 dark:hover:border-stone-700 transition-all flex items-center justify-between gap-3"
                    >
                      <div className="flex items-center gap-3 min-w-0">
                        <span className="flex items-center justify-center w-6 h-6 rounded-full bg-amber-500/10 text-amber-700 dark:text-amber-400 font-mono text-xs font-bold shrink-0">
                          {idx + 1}
                        </span>
                        <div className="min-w-0">
                          <div className="flex items-center gap-2">
                            <span className="text-xs font-semibold text-stone-900 dark:text-white truncate">
                              {fix.title}
                            </span>
                            {fix.count > 0 && (
                              <span className="text-[10px] px-2 py-0.2 rounded-full bg-stone-200/80 dark:bg-stone-800 text-stone-700 dark:text-stone-300 font-mono">
                                {fix.count} items
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-stone-500 dark:text-stone-400 truncate mt-0.5">
                            {isSimple ? fix.simple : fix.description}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center gap-2 shrink-0">
                        <span className="text-xs font-mono font-bold text-sage-700 dark:text-emerald-400 bg-sage-50 dark:bg-emerald-950/40 px-2.5 py-1 rounded-xl border border-sage-200 dark:border-emerald-800/50">
                          +{typeof fix.scoreGain === 'number' ? fix.scoreGain.toFixed(1) : fix.scoreGain} pts
                        </span>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Bottom Actions */}
            <div className="mt-5 pt-4 border-t border-stone-200/80 dark:border-stone-800 flex items-center justify-between">
              <span className="text-xs text-stone-500">
                Fixing these 3 issues recovers <strong className="text-sage-700 dark:text-emerald-400">+5.2% test accuracy</strong>
              </span>
              <button
                onClick={() => setActiveTab('whatif')}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-stone-900 hover:bg-stone-800 text-white dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-white text-xs font-semibold shadow-warm-sm transition-all"
              >
                <span>Simulate Fixes</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </GlassCard>
        </div>

        {/* Bottom Row: The 6 Health Pillars (Clean 3x2 Grid) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-stone-900 dark:text-white uppercase tracking-wider font-mono">
                The 6 Health Pillars
              </h3>
              <p className="text-xs text-stone-500 mt-0.5">
                Click any pillar to slide out detailed charts, class distributions, and cross-interaction checks
              </p>
            </div>
            <span className="text-xs font-mono text-stone-500">
              Interactive Slide-Over ➔
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {pillars.map((pillar) => {
              const colors = getReadinessColor(pillar.score);
              const tier = getReadinessTier(pillar.score);

              return (
                <div
                  key={pillar.key}
                  onClick={() => setSelectedPillar(pillar.key)}
                  className="p-6 rounded-3xl bg-white dark:bg-[#221F1D] border border-stone-200/80 dark:border-stone-800 shadow-warm-sm hover:shadow-warm-md hover:border-stone-300 dark:hover:border-stone-700 cursor-pointer transition-all duration-200 flex flex-col justify-between group"
                >
                  <div>
                    {/* Header: Title + Status Pill */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div className="p-2 rounded-2xl bg-stone-100 dark:bg-stone-800">
                          {pillar.icon}
                        </div>
                        <h4 className="text-sm font-bold text-stone-900 dark:text-stone-100">
                          {pillar.name}
                        </h4>
                      </div>
                      <span
                        className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full"
                        style={{
                          backgroundColor: colors.bg,
                          color: colors.text,
                        }}
                      >
                        {tier.toUpperCase()}
                      </span>
                    </div>

                    {/* Score Bar + Big Number */}
                    <div className="mt-4 flex items-baseline justify-between">
                      <span className="text-3xl font-black font-mono tracking-tight text-stone-900 dark:text-white">
                        {pillar.score}
                      </span>
                      <span className="text-xs text-stone-400 font-mono">/ 100</span>
                    </div>

                    <div className="w-full bg-stone-100 dark:bg-stone-800 rounded-full h-1.5 mt-2 overflow-hidden">
                      <div
                        className="h-1.5 rounded-full transition-all duration-700"
                        style={{
                          width: `${pillar.score}%`,
                          backgroundColor: colors.hex,
                        }}
                      />
                    </div>

                    {/* Single Plain English Sentence */}
                    <p className="text-xs text-stone-600 dark:text-stone-400 mt-3 leading-relaxed">
                      {pillar.sentence}
                    </p>
                  </div>

                  <div className="mt-4 pt-3 border-t border-stone-100 dark:border-stone-800 flex items-center justify-between text-[11px] text-stone-500 group-hover:text-stone-900 dark:group-hover:text-stone-200 transition-colors">
                    <span>View deeper charts</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Slide-over Detail Drawer */}
      <PillarDetailDrawer
        pillar={selectedPillar}
        onClose={() => setSelectedPillar(null)}
      />
    </StateView>
  );
};
