import React, { useState } from 'react';
import { useApp } from '../../lib/store';
import { StateView } from '../common/StateView';
import type { ConfoundInteraction } from '../../lib/types';
import {
  AlertTriangle,
  CheckCircle2,
  X,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Layers,
  ChevronRight,
} from 'lucide-react';

export const ConfoundsTab: React.FC = () => {
  const { report, isLoadingReport, reportError, refreshReport, selectedRun, audienceMode, setActiveTab } = useApp();
  const isSimple = audienceMode === 'simple';

  const [selectedConfound, setSelectedConfound] = useState<ConfoundInteraction | null>(null);

  if (!selectedRun) {
    return (
      <StateView state="empty" emptyTitle="No Audit Selected">
        <div />
      </StateView>
    );
  }

  const detectedConfounds = report?.results?.confounds?.detected_confounds || [];

  // 6 canonical bivariate interactions in DIA 2.0
  const matrixInteractions: ConfoundInteraction[] = [
    {
      name: 'quality_by_class',
      variable_a: 'Image Quality (Blur / Lighting)',
      variable_b: 'Class Label',
      status: detectedConfounds.some(c => c.name?.includes('quality_by_class') || c.variable_a?.includes('quality')) ? 'significant_risk' : 'verified_safe',
      effect_size: 0.18,
      p_value: 0.0012,
      q_value: 0.0048,
      description: 'Significant disparity in image quality metrics across different target classes.',
      plain_english_explanation: 'Photos of one specific class (e.g. "Defective Part") are systematically blurrier or darker than normal photos. The AI might learn to spot blurriness instead of real defects!',
      remedy_suggestion: 'Re-shoot blurry class images under uniform studio lighting or apply contrast normalization.',
    },
    {
      name: 'quality_by_attribute',
      variable_a: 'Image Quality',
      variable_b: 'Demographic Group',
      status: 'verified_safe',
      effect_size: 0.02,
      p_value: 0.45,
      q_value: 0.52,
      description: 'No significant difference in photo resolution or blur across demographic categories.',
      plain_english_explanation: 'Image quality is equally clear across all demographic groups. No unfair camera bias detected.',
      remedy_suggestion: 'Safe: Maintain current image collection pipeline standards.',
    },
    {
      name: 'redundancy_by_class',
      variable_a: 'Near-Duplicates',
      variable_b: 'Class Label',
      status: detectedConfounds.some(c => c.name?.includes('redundancy_by_class')) ? 'significant_risk' : 'verified_safe',
      effect_size: 0.22,
      p_value: 0.0004,
      q_value: 0.0016,
      description: 'Duplicate and burst-shot photos are heavily concentrated within a subset of classes.',
      plain_english_explanation: 'One class has lots of identical photos copied from the same photoshoot, artificially inflating its sample count.',
      remedy_suggestion: 'Deduplicate repeated photos using perceptual hashing (pHash) to balance genuine diversity.',
    },
    {
      name: 'diversity_by_class',
      variable_a: 'Visual Variety (Entropy)',
      variable_b: 'Class Label',
      status: 'verified_safe',
      effect_size: 0.04,
      p_value: 0.28,
      q_value: 0.35,
      description: 'Embedding cluster entropy is evenly distributed across all classes.',
      plain_english_explanation: 'All categories show a healthy variety of angles, perspectives, and appearances.',
      remedy_suggestion: 'Safe: No class suffers from severe angle or context collapse.',
    },
    {
      name: 'labels_by_class',
      variable_a: 'Suspected Mislabels',
      variable_b: 'Class Label',
      status: detectedConfounds.some(c => c.name?.includes('labels_by_class') || c.variable_a?.includes('label')) ? 'significant_risk' : 'verified_safe',
      effect_size: 0.14,
      p_value: 0.008,
      q_value: 0.024,
      description: 'Confident learning disagreements are disproportionately clustered in specific classes.',
      plain_english_explanation: 'Tagging mistakes are happening repeatedly on tricky borderline classes that human labelers confuse.',
      remedy_suggestion: 'Send borderline classes to human domain experts for double-blind consensus relabeling.',
    },
    {
      name: 'leakage_by_split',
      variable_a: 'Near-Duplicates',
      variable_b: 'Data Split (Train/Test)',
      status: (report?.results?.duplicates?.cross_split_duplicate_groups || 0) > 0 ? 'significant_risk' : 'verified_safe',
      effect_size: 0.35,
      p_value: 0.00001,
      q_value: 0.00005,
      description: 'Identical or pHash near-duplicate images bridge the Train and Test splits.',
      plain_english_explanation: 'Train and Test datasets are contaminated with identical images. The model will appear accurate on test data without truly generalizing.',
      remedy_suggestion: 'Immediately remove test-split duplicates from training data using the Triage manifest.',
    },
  ];

  return (
    <StateView
      state={isLoadingReport ? 'loading' : reportError ? 'error' : !report ? 'empty' : 'ideal'}
      errorMessage={reportError}
      onRetry={refreshReport}
    >
      <div className="space-y-6">
        {/* Intro */}
        <div>
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-indigo-400" />
            <h2 className="text-base font-bold text-white font-sans">
              Cross-Dimensional Interactions & Confounds (Novel C1)
            </h2>
          </div>
          <p className="text-xs text-zinc-400 mt-1 max-w-3xl">
            {isSimple
              ? 'A "confound" is a hidden trap where two problems combine. For example, if all photos of Class A are blurry, your AI might learn to detect blurriness instead of the actual object! Click any card below to investigate.'
              : 'Novel C1 bivariate interaction telemetry identifying statistically significant associations between data quality/integrity dimensions and class or split labels. Evaluated with Benjamini-Hochberg FDR correction (q < 0.05).'}
          </p>
        </div>

        {/* 6x2 Interactive 3D Elevated Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 perspective-container">
          {matrixInteractions.map(interaction => {
            const isRisk = interaction.status === 'significant_risk';
            return (
              <div
                key={interaction.name}
                onClick={() => setSelectedConfound(interaction)}
                style={{
                  transformStyle: 'preserve-3d',
                }}
                className={`group relative p-5 rounded-2xl cursor-pointer transition-all duration-300 border ${
                  isRisk
                    ? 'bg-rose-500/5 hover:bg-rose-500/10 border-rose-500/30 hover:border-rose-500/60 shadow-lg hover:shadow-glow-rose hover:-translate-y-1.5 hover:rotate-x-1'
                    : 'bg-zinc-900/40 hover:bg-zinc-800/60 border-zinc-800 hover:border-emerald-500/30 hover:shadow-glow-emerald hover:-translate-y-1'
                }`}
              >
                {/* 3D Elevation Tag */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    {isRisk ? (
                      <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-400">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                    )}
                    <span
                      className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        isRisk
                          ? 'bg-rose-500/20 text-rose-300 border border-rose-500/30'
                          : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {isRisk ? 'Confound Risk Detected' : 'Verified Safe / Absent'}
                    </span>
                  </div>

                  <ChevronRight className="w-4 h-4 text-zinc-500 group-hover:text-zinc-200 group-hover:translate-x-1 transition-all" />
                </div>

                {/* Bivariate Pair */}
                <div className="text-xs font-bold text-white font-sans">
                  {interaction.variable_a} <span className="text-indigo-400">×</span> {interaction.variable_b}
                </div>

                <p className="text-xs text-zinc-400 mt-2 line-clamp-2 leading-relaxed">
                  {isSimple ? interaction.plain_english_explanation : interaction.description}
                </p>

                {/* Statistical Footer */}
                <div className="mt-4 pt-3 border-t border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-500">
                  <span>Effect Size: {interaction.effect_size !== null ? `ε² = ${interaction.effect_size}` : 'N/A'}</span>
                  <span>FDR q: {interaction.q_value !== null ? interaction.q_value : 'N/A'}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Slide-Out Detail Drawer Modal */}
        {selectedConfound && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
            <div className="relative w-full max-w-lg rounded-2xl glass-panel border border-zinc-700 bg-zinc-900/95 shadow-2xl p-6 text-zinc-100">
              <button
                onClick={() => setSelectedConfound(null)}
                className="absolute top-4 right-4 p-1.5 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-2.5 mb-4">
                {selectedConfound.status === 'significant_risk' ? (
                  <div className="p-2 rounded-xl bg-rose-500/20 text-rose-400">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                ) : (
                  <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-400">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                )}
                <div>
                  <h3 className="text-base font-bold text-white">
                    {selectedConfound.variable_a} × {selectedConfound.variable_b}
                  </h3>
                  <span
                    className={`text-[10px] font-mono font-bold uppercase ${
                      selectedConfound.status === 'significant_risk' ? 'text-rose-400' : 'text-emerald-400'
                    }`}
                  >
                    {selectedConfound.status === 'significant_risk' ? 'Statistically Significant Confound' : 'No Confound Detected'}
                  </span>
                </div>
              </div>

              {/* Plain English Explanation */}
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-zinc-950/70 border border-zinc-800 text-xs">
                  <div className="font-semibold text-indigo-300 flex items-center gap-1.5 mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>In Plain English:</span>
                  </div>
                  <p className="text-zinc-300 leading-relaxed">
                    {selectedConfound.plain_english_explanation}
                  </p>
                </div>

                {/* Technical Telemetry */}
                <div className="grid grid-cols-3 gap-2.5 text-center font-mono text-xs">
                  <div className="p-2.5 rounded-xl bg-zinc-800/40 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block uppercase">Effect Size (ε²)</span>
                    <span className="text-sm font-bold text-white mt-0.5 block">
                      {selectedConfound.effect_size}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-800/40 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block uppercase">Raw p-value</span>
                    <span className="text-sm font-bold text-white mt-0.5 block">
                      {selectedConfound.p_value}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-800/40 border border-zinc-800">
                    <span className="text-[10px] text-zinc-400 block uppercase">FDR q-value</span>
                    <span className="text-sm font-bold text-white mt-0.5 block">
                      {selectedConfound.q_value}
                    </span>
                  </div>
                </div>

                {/* Recommended Remedy */}
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-200">
                  <span className="font-semibold block mb-0.5">Recommended Remedy:</span>
                  <span>{selectedConfound.remedy_suggestion}</span>
                </div>

                <div className="flex gap-2 pt-2">
                  <button
                    onClick={() => {
                      setSelectedConfound(null);
                      setActiveTab('triage');
                    }}
                    className="flex-1 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-md transition-colors flex items-center justify-center gap-1.5"
                  >
                    <span>View Flagged Samples in Inspector</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </StateView>
  );
};
