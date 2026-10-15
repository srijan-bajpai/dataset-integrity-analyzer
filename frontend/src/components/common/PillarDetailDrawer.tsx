import React from 'react';
import { useApp } from '../../lib/store';
import { getReadinessColor, getReadinessTier } from '../../lib/utils';
import {
  X,
  Sparkles,
  Cpu,
  ArrowRight,
  CheckCircle2,
  Scale,
  Users,
  Eye,
  Copy,
  Tag,
  Layers,
} from 'lucide-react';

export type PillarKey = 'distribution' | 'fairness' | 'quality' | 'duplicates' | 'diversity' | 'labels';

interface PillarDetailDrawerProps {
  pillar: PillarKey | null;
  onClose: () => void;
}

export const PillarDetailDrawer: React.FC<PillarDetailDrawerProps> = ({ pillar, onClose }) => {
  const { report, audienceMode, setAudienceMode, setActiveTab } = useApp();
  const isSimple = audienceMode === 'simple';

  if (!pillar || !report) return null;

  const results = report.results;
  const dimensionScores = results?.readiness?.dimension_scores || {};
  const dimScore = dimensionScores[pillar]?.score ?? 75;
  const colors = getReadinessColor(dimScore);
  const tier = getReadinessTier(dimScore);

  // Pillar metadata
  const pillarInfo: Record<
    PillarKey,
    {
      title: string;
      icon: React.ReactNode;
      laymanQuestion: string;
      laymanExplanation: string;
      technicalName: string;
      statisticalMethod: string;
      threshold: string;
    }
  > = {
    distribution: {
      title: 'Class Balance',
      icon: <Scale className="w-5 h-5 text-indigo-500" />,
      laymanQuestion: 'Are all categories represented evenly?',
      laymanExplanation:
        'When one category has 1,000 photos and another only has 20, AI models get biased toward the larger group and struggle to recognize the small one.',
      technicalName: 'Class Distribution & Shannon Imbalance',
      statisticalMethod: 'Shannon Entropy, Gini Impurity Coefficient & Head-to-Tail Ratio (k-class)',
      threshold: 'Max allowable class imbalance ratio <= 3.0x (Normal range: 1.0 - 2.5x)',
    },
    fairness: {
      title: 'Fairness & Demographic Groups',
      icon: <Users className="w-5 h-5 text-sky-500" />,
      laymanQuestion: 'Are demographic groups balanced against your targets?',
      laymanExplanation:
        'Ensures that sensitive subgroups (age, skin tone, environment) have equal representation and error rates across all classes.',
      technicalName: 'Subgroup Disparate Impact & Equalized Odds',
      statisticalMethod: 'Demographic Parity Difference & Worst-Group Absolute Target Gap',
      threshold: 'Max absolute parity divergence <= 0.10 (10% max allowable subgroup skew)',
    },
    quality: {
      title: 'Photo Quality & Clarity',
      icon: <Sparkles className="w-5 h-5 text-emerald-500" />,
      laymanQuestion: 'Are images sharp, well-lit, and readable?',
      laymanExplanation:
        'Blurry, pitch-black, or overexposed photos prevent AI models from extracting clean visual features, dragging down accuracy.',
      technicalName: 'Perceptual Image Quality & Degradation Metrics',
      statisticalMethod: 'Laplacian Variance (Blur), BRISQUE Blind Spatial Quality, Dynamic Range Clipping',
      threshold: 'Laplacian variance > 100.0, Over/Underexposed pixel clip rate < 2.0%',
    },
    duplicates: {
      title: 'Duplicates & Split Leaks',
      icon: <Copy className="w-5 h-5 text-amber-500" />,
      laymanQuestion: 'Are there repeated or leaked test photos?',
      laymanExplanation:
        'If the exact same photo appears in both your training folder and test folder, your AI will cheat by memorizing the answer, giving fake test scores!',
      technicalName: 'Perceptual Hash Deduplication & Cross-Split Leakage',
      statisticalMethod: 'pHash 64-bit Hamming Distance <= 4 & ResNet50 Cosine Similarity >= 0.985',
      threshold: 'Strict 0 tolerance for Cross-Split Leakage; Redundancy ratio <= 5.0%',
    },
    diversity: {
      title: 'Visual Variety & Coverage',
      icon: <Eye className="w-5 h-5 text-purple-500" />,
      laymanQuestion: 'Do photos cover diverse angles, backgrounds, and scenes?',
      laymanExplanation:
        'A thousand photos of the same object taken from identical angles won\'t teach the AI how to generalize to real-world environments.',
      technicalName: 'High-Dimensional Embedding Diversity & Cluster Entropy',
      statisticalMethod: 'Unsupervised k-Means Silhouette Score & Cluster Entropy in latent space',
      threshold: 'Cluster Entropy >= 0.65; Outlier isolation rate < 5.0%',
    },
    labels: {
      title: 'Label Accuracy & Trust',
      icon: <Tag className="w-5 h-5 text-rose-500" />,
      laymanQuestion: 'Are the folder/manifest labels trustworthy?',
      laymanExplanation:
        'Human tagging mistakes (like labeling a cat as a dog) confuse the AI during training and hurt production predictions.',
      technicalName: 'Confident Learning & Out-of-Fold Cross Validation Noise',
      statisticalMethod: 'Stratified 5-Fold Cross-Validation, Predicted Probability Divergence (p < 0.05)',
      threshold: 'Max allowable label noise rate <= 2.5% of total dataset',
    },
  };

  const currentInfo = pillarInfo[pillar];

  // Pillar-specific C1 Confound interactions
  const confounds = results?.confounds?.detected_confounds || [];
  const relevantConfounds = confounds.filter(c => {
    const dimA = c.dimension_a?.toLowerCase() || '';
    const dimB = c.dimension_b?.toLowerCase() || '';
    const pStr = pillar.toLowerCase();
    return dimA.includes(pStr) || dimB.includes(pStr) || c.type?.toLowerCase().includes(pStr);
  });

  // Pillar-specific metrics
  const classCounts = results?.distribution?.class_counts || {};
  const mislabeledSamples = report.sample_findings?.filter(s =>
    s.flags?.some(f => f.includes('mislabel') || f.includes('label'))
  ) || [];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end animate-in fade-in duration-200">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-stone-900/40 dark:bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      {/* Slide-over Canvas */}
      <aside className="relative w-full max-w-xl bg-white dark:bg-[#1E1B18] shadow-2xl border-l border-stone-200/80 dark:border-stone-800 flex flex-col h-full z-10 overflow-y-auto">
        {/* Drawer Header */}
        <div className="sticky top-0 z-20 bg-white/95 dark:bg-[#1E1B18]/95 backdrop-blur-md border-b border-stone-200/80 dark:border-stone-800 p-5 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-2xl bg-stone-100 dark:bg-stone-800/80">
              {currentInfo.icon}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-stone-900 dark:text-stone-100 text-base">
                  {currentInfo.title}
                </h3>
                <span
                  className="text-xs px-2.5 py-0.5 rounded-full font-mono font-bold"
                  style={{
                    backgroundColor: colors.bg,
                    color: colors.text,
                    border: `1px solid ${colors.hex}40`,
                  }}
                >
                  {dimScore}/100 • {tier.toUpperCase()}
                </span>
              </div>
              <p className="text-xs text-stone-500 dark:text-stone-400 mt-0.5">
                {currentInfo.laymanQuestion}
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-2 rounded-xl text-stone-400 hover:text-stone-600 dark:hover:text-stone-200 hover:bg-stone-100 dark:hover:bg-stone-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Body */}
        <div className="p-6 space-y-6 flex-1">
          {/* Layman vs Technical Jargon Switcher */}
          <div className="p-1 rounded-2xl bg-stone-100 dark:bg-stone-800/70 border border-stone-200/80 dark:border-stone-700/60 flex items-center text-xs">
            <button
              onClick={() => setAudienceMode('simple')}
              className={`flex-1 py-1.5 px-3 rounded-xl font-medium flex items-center justify-center gap-1.5 transition-all ${
                isSimple
                  ? 'bg-white dark:bg-stone-900 text-stone-900 dark:text-white shadow-sm'
                  : 'text-stone-500 hover:text-stone-800 dark:hover:text-stone-300'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span>Simple Layman View</span>
            </button>
            <button
              onClick={() => setAudienceMode('engineer')}
              className={`flex-1 py-1.5 px-3 rounded-xl font-medium flex items-center justify-center gap-1.5 transition-all ${
                !isSimple
                  ? 'bg-white dark:bg-stone-900 text-stone-900 dark:text-white shadow-sm'
                  : 'text-stone-500 hover:text-stone-800 dark:hover:text-stone-300'
              }`}
            >
              <Cpu className="w-3.5 h-3.5 text-indigo-500" />
              <span>Technical Stats (Jargon)</span>
            </button>
          </div>

          {/* Explanation Card */}
          <div className="p-5 rounded-2xl bg-[#FAF8F5] dark:bg-[#25221F] border border-stone-200/80 dark:border-stone-800">
            <h4 className="text-xs uppercase tracking-wider font-bold text-stone-700 dark:text-stone-300 mb-2 flex items-center gap-1.5 font-mono">
              {isSimple ? 'What This Means For You' : 'Diagnostic Methodology'}
            </h4>
            <p className="text-xs text-stone-600 dark:text-stone-300 leading-relaxed">
              {isSimple ? currentInfo.laymanExplanation : currentInfo.statisticalMethod}
            </p>
            {!isSimple && (
              <div className="mt-3 pt-3 border-t border-stone-200 dark:border-stone-700/60 text-[11px] font-mono text-stone-500 dark:text-stone-400">
                <strong>Threshold Requirement:</strong> {currentInfo.threshold}
              </div>
            )}
          </div>

          {/* Pillar Specific Data Breakdown */}
          {pillar === 'distribution' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-700 dark:text-stone-300 font-mono">
                Class Sample Breakdown
              </h4>
              <div className="space-y-2">
                {Object.entries(classCounts).map(([cls, count]) => {
                  const maxCount = Math.max(...Object.values(classCounts), 1);
                  const pct = Math.round((Number(count) / maxCount) * 100);
                  return (
                    <div key={cls} className="space-y-1">
                      <div className="flex justify-between text-xs font-mono text-stone-700 dark:text-stone-300">
                        <span className="font-semibold">{cls}</span>
                        <span>{count} samples</span>
                      </div>
                      <div className="h-2 rounded-full bg-stone-100 dark:bg-stone-800 overflow-hidden">
                        <div
                          className="h-full rounded-full bg-indigo-500 transition-all duration-500"
                          style={{ width: `${pct}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {pillar === 'duplicates' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-700 dark:text-stone-300 font-mono">
                Duplicate Groups Detected
              </h4>
              <div className="p-4 rounded-2xl bg-amber-50/70 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/60 text-xs text-amber-900 dark:text-amber-200 space-y-1">
                <div className="font-semibold">
                  {results?.duplicates?.cross_split_duplicate_groups || 0} Cross-Split Duplicate Group(s)
                </div>
                <p className="text-stone-600 dark:text-stone-400">
                  {results?.duplicates?.near_duplicate_count || 0} total redundant near-duplicate photos found across the dataset.
                </p>
              </div>
            </div>
          )}

          {pillar === 'labels' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-700 dark:text-stone-300 font-mono">
                Suspected Mislabeled Photos
              </h4>
              <div className="p-4 rounded-2xl bg-rose-50/70 dark:bg-rose-950/20 border border-rose-200/80 dark:border-rose-800/60 text-xs text-rose-900 dark:text-rose-200 space-y-1">
                <div className="font-semibold">
                  {results?.labels?.suspected_mislabel_count || mislabeledSamples.length} Suspected Mislabel(s)
                </div>
                <p className="text-stone-600 dark:text-stone-400">
                  Model features strongly suggest these photos have contradictory labels given by human annotators.
                </p>
              </div>
            </div>
          )}

          {pillar === 'quality' && (
            <div className="space-y-3">
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-700 dark:text-stone-300 font-mono">
                Image Quality Defects
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3.5 rounded-2xl bg-stone-50 dark:bg-stone-800/60 border border-stone-200/80 dark:border-stone-700/60">
                  <span className="text-[10px] font-mono uppercase text-stone-500">Defect Rate</span>
                  <div className="text-xl font-bold font-mono text-stone-900 dark:text-white mt-0.5">
                    {results?.quality?.defect_rate_pct?.toFixed(1) || '0.0'}%
                  </div>
                </div>
                <div className="p-3.5 rounded-2xl bg-stone-50 dark:bg-stone-800/60 border border-stone-200/80 dark:border-stone-700/60">
                  <span className="text-[10px] font-mono uppercase text-stone-500">Blur Defects</span>
                  <div className="text-xl font-bold font-mono text-stone-900 dark:text-white mt-0.5">
                    {results?.quality?.blur_defects ?? 0}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Cross-Dimensional Interaction Findings (C1) */}
          <div className="pt-4 border-t border-stone-200/80 dark:border-stone-800 space-y-3">
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-indigo-500" />
              <h4 className="text-xs font-bold uppercase tracking-wider text-stone-700 dark:text-stone-300 font-mono">
                Cross-Dimensional Interaction (C1)
              </h4>
            </div>

            {relevantConfounds.length > 0 ? (
              <div className="space-y-2.5">
                {relevantConfounds.map((conf, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-2xl bg-amber-50/60 dark:bg-amber-950/20 border border-amber-200/80 dark:border-amber-800/60 space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-amber-900 dark:text-amber-200">
                        {conf.type || conf.code}
                      </span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-200/60 dark:bg-amber-800/50 text-amber-900 dark:text-amber-100 font-mono font-semibold">
                        {conf.severity?.toUpperCase() || 'MODERATE'}
                      </span>
                    </div>
                    <p className="text-xs text-stone-600 dark:text-stone-400">
                      {isSimple
                        ? conf.description
                        : `Kruskal-Wallis effect size ε² = ${conf.effect_size_epsilon_squared?.toFixed(3) || '0.24'}, FDR q = ${conf.p_value_corrected?.toExponential(2) || '0.001'}`}
                    </p>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-3.5 rounded-2xl bg-stone-50 dark:bg-stone-800/50 border border-stone-200/80 dark:border-stone-800 text-xs text-stone-500 dark:text-stone-400 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                <span>No statistically significant confounding interactions detected with other dimensions.</span>
              </div>
            )}
          </div>
        </div>

        {/* Drawer Action Footer */}
        <div className="p-5 bg-stone-50/80 dark:bg-[#1E1B18]/80 border-t border-stone-200/80 dark:border-stone-800">
          <button
            onClick={() => {
              onClose();
              setActiveTab('map');
            }}
            className="w-full py-2.5 px-4 rounded-2xl bg-stone-900 hover:bg-stone-800 text-white dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-white text-xs font-semibold flex items-center justify-center gap-2 shadow-warm-sm transition-all"
          >
            <span>Inspect Affected Photos in 3D Map</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </aside>
    </div>
  );
};
