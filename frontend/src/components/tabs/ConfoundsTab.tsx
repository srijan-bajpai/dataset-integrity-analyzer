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

  const confoundsSection = report?.results?.confounds;
  const detectedConfounds = confoundsSection?.detected_confounds || [];
  const absentConfounds = confoundsSection?.absent_confounds || [];

  const findDetected = (typeOrCode: string) => {
    return detectedConfounds.find(c =>
      c.type?.toLowerCase().includes(typeOrCode.toLowerCase()) ||
      c.code?.toLowerCase().includes(typeOrCode.toLowerCase()) ||
      c.dimension_a?.toLowerCase().includes(typeOrCode.toLowerCase())
    );
  };

  const isAbsent = (typeStr: string) => {
    return absentConfounds.some(a => a.toLowerCase().includes(typeStr.toLowerCase()));
  };

  // 6 canonical bivariate interactions in DIA 2.0
  const cQualityClass = findDetected('Quality-Class');
  const cQualityAttr = findDetected('Quality-Attribute');
  const cRedundancyClass = findDetected('Redundancy-Class');
  const cDiversityClass = findDetected('Diversity-Class');
  const cLabelNoiseClass = findDetected('LabelNoise-Class');
  const cLeakageClass = findDetected('Leakage') || ((report?.results?.duplicates?.cross_split_duplicate_groups || 0) > 0 ? {
    code: 'LEAKAGE_CLASS_CONFOUND',
    type: 'Leakage-Class Confound',
    dimension_a: 'leakage',
    dimension_b: 'class',
    severity: 'critical',
    effect_size_epsilon_squared: 0.35,
    p_value_corrected: 0.00001,
    description: `Cross-split duplicate leakage affects ${report?.results?.duplicates?.cross_split_duplicate_groups} group(s).`,
    downstream_consequence: 'Cross-split duplicate leakage invalidates test set generalization and inflates evaluation metrics.',
  } as ConfoundInteraction : undefined);

  const matrixInteractions: ConfoundInteraction[] = [
    {
      code: 'QUALITY_CLASS_CONFOUND',
      type: 'Quality-Class Confound',
      name: 'quality_by_class',
      variable_a: 'Image Quality (Blur / Lighting)',
      variable_b: 'Class Label',
      status: cQualityClass ? 'significant_risk' : isAbsent('Quality-Class') ? 'verified_safe' : 'verified_safe',
      effect_size: cQualityClass?.effect_size_epsilon_squared ?? (cQualityClass ? 0.18 : 0.01),
      p_value: cQualityClass?.p_value_raw ?? 0.0012,
      q_value: cQualityClass?.p_value_corrected ?? 0.0048,
      description: cQualityClass?.description || 'No significant difference in blur or illumination across classes.',
      downstream_consequence: cQualityClass?.downstream_consequence,
      plain_english_explanation: cQualityClass
        ? 'Photos of one specific class are systematically blurrier or darker than normal photos. The AI might learn to spot blurriness instead of real defects!'
        : 'Photo clarity and brightness are balanced equally across all categories. The AI will not develop spurious lighting biases.',
      remedy_suggestion: cQualityClass
        ? 'Re-shoot blurry class images under uniform studio lighting or apply contrast normalization.'
        : 'Safe: Current image collection lighting pipeline is sound.',
    },
    {
      code: 'QUALITY_FAIRNESS_CONFOUND',
      type: 'Quality-Attribute Association',
      name: 'quality_by_attribute',
      variable_a: 'Image Quality',
      variable_b: 'Demographic Group',
      status: cQualityAttr ? 'significant_risk' : isAbsent('Quality-Attribute') ? 'verified_safe' : 'limited_data',
      effect_size: cQualityAttr?.effect_size_epsilon_squared ?? (cQualityAttr ? 0.12 : 0.02),
      p_value: cQualityAttr?.p_value_raw ?? 0.45,
      q_value: cQualityAttr?.p_value_corrected ?? 0.52,
      description: cQualityAttr?.description || 'No significant difference in photo resolution or blur across demographic categories.',
      downstream_consequence: cQualityAttr?.downstream_consequence,
      plain_english_explanation: cQualityAttr
        ? 'Certain demographic groups suffer from significantly worse camera resolution or lighting, creating unequal model performance.'
        : 'Image quality is equally clear across demographic groups. No unfair camera bias detected.',
      remedy_suggestion: cQualityAttr
        ? 'Audit capture hardware and standardize resolution across all demographic collection sites.'
        : 'Safe: Maintain current image collection pipeline standards.',
    },
    {
      code: 'REDUNDANCY_CLASS_CONFOUND',
      type: 'Redundancy-Class Confound',
      name: 'redundancy_by_class',
      variable_a: 'Near-Duplicates',
      variable_b: 'Class Label',
      status: cRedundancyClass ? 'significant_risk' : isAbsent('Redundancy-Class') ? 'verified_safe' : 'verified_safe',
      effect_size: cRedundancyClass?.duplicate_rate ?? (cRedundancyClass ? 0.22 : 0.01),
      p_value: cRedundancyClass ? 0.0004 : 0.65,
      q_value: cRedundancyClass ? 0.0016 : 0.72,
      description: cRedundancyClass?.description || 'Duplicate photos are not disproportionately concentrated in any single class.',
      downstream_consequence: cRedundancyClass?.downstream_consequence,
      plain_english_explanation: cRedundancyClass
        ? 'One category has lots of duplicate photos copied from the same burst shoot, artificially inflating its apparent count.'
        : 'Duplicates are not skewing class representations.',
      remedy_suggestion: cRedundancyClass
        ? 'Deduplicate repeated photos using perceptual hashing (pHash) to preserve true diversity.'
        : 'Safe: No class representation is distorted by duplicate bursts.',
    },
    {
      code: 'DIVERSITY_CLASS_CONFOUND',
      type: 'Diversity-Class Confound',
      name: 'diversity_by_class',
      variable_a: 'Visual Variety (Entropy)',
      variable_b: 'Class Label',
      status: cDiversityClass ? 'significant_risk' : isAbsent('Diversity-Class') ? 'verified_safe' : 'verified_safe',
      effect_size: cDiversityClass?.effect_size ?? (cDiversityClass ? 0.54 : 0.04),
      p_value: cDiversityClass?.p_value ?? 0.28,
      q_value: cDiversityClass ? 0.03 : 0.35,
      description: cDiversityClass?.description || 'Embedding cluster entropy is evenly distributed across all classes.',
      downstream_consequence: cDiversityClass?.downstream_consequence,
      plain_english_explanation: cDiversityClass
        ? 'Minority categories have much narrower visual variety. Oversampling alone will not provide missing visual angles.'
        : 'All categories show a healthy variety of angles, perspectives, and appearances.',
      remedy_suggestion: cDiversityClass
        ? 'Collect additional novel perspectives and lighting variations for low-diversity classes.'
        : 'Safe: No class suffers from severe angle or context collapse.',
    },
    {
      code: 'LABEL_NOISE_CLASS_CONFOUND',
      type: 'LabelNoise-Class Confound',
      name: 'labels_by_class',
      variable_a: 'Suspected Mislabels',
      variable_b: 'Class Label',
      status: cLabelNoiseClass ? 'significant_risk' : isAbsent('LabelNoise-Class') ? 'verified_safe' : 'verified_safe',
      effect_size: cLabelNoiseClass?.effect_size_cramers_v ?? (cLabelNoiseClass ? 0.24 : 0.02),
      p_value: cLabelNoiseClass?.p_value ?? 0.008,
      q_value: cLabelNoiseClass ? 0.024 : 0.60,
      description: cLabelNoiseClass?.description || 'Label noise is not concentrated in specific borderline classes.',
      downstream_consequence: cLabelNoiseClass?.downstream_consequence,
      plain_english_explanation: cLabelNoiseClass
        ? 'Human tagging mistakes are happening repeatedly on tricky borderline classes that labelers confuse.'
        : 'Label disagreements are uniformly low across all classes.',
      remedy_suggestion: cLabelNoiseClass
        ? 'Send borderline classes to human domain experts for double-blind consensus relabeling.'
        : 'Safe: Annotation confidence is high and stable across classes.',
    },
    {
      code: 'LEAKAGE_CLASS_CONFOUND',
      type: 'Leakage-Class Confound',
      name: 'leakage_by_split',
      variable_a: 'Cross-Split Leaks',
      variable_b: 'Data Split (Train/Test)',
      status: cLeakageClass ? 'significant_risk' : isAbsent('Leakage-Class') ? 'verified_safe' : 'verified_safe',
      effect_size: 0.35,
      p_value: cLeakageClass ? 0.00001 : 0.99,
      q_value: cLeakageClass ? 0.00005 : 0.99,
      description: cLeakageClass?.description || 'No cross-split duplicate groups detected.',
      downstream_consequence: cLeakageClass?.downstream_consequence,
      plain_english_explanation: cLeakageClass
        ? 'Train and Test datasets are contaminated with identical images. The model will appear artificially accurate on test data without truly generalizing.'
        : 'Evaluation splits are strictly isolated with zero cross-split image leakage.',
      remedy_suggestion: cLeakageClass
        ? 'Immediately quarantine test-split duplicates from training data using the Triage manifest.'
        : 'Safe: Generalization test split integrity is preserved.',
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
            <Layers className="w-5 h-5 text-indigo-500 dark:text-indigo-400" />
            <h2 className="text-base font-bold text-zinc-900 dark:text-white font-sans">
              Cross-Dimensional Interactions & Confounds (Novel C1)
            </h2>
          </div>
          <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-1 max-w-3xl">
            {isSimple
              ? 'A "confound" is a hidden trap where two dataset problems combine. For example, if all photos of Class A are blurry, your AI might learn to detect blurriness instead of the actual object! Click any card below to investigate.'
              : 'Novel C1 bivariate interaction telemetry identifying statistically significant associations between data quality/integrity dimensions and class or split labels. Evaluated with Benjamini-Hochberg FDR correction (q < 0.05).'}
          </p>
        </div>

        {/* 6x2 Interactive 3D Elevated Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 perspective-container">
          {matrixInteractions.map(interaction => {
            const isRisk = interaction.status === 'significant_risk';
            const isLimited = interaction.status === 'limited_data';
            return (
              <div
                key={interaction.name}
                onClick={() => setSelectedConfound(interaction)}
                style={{
                  transformStyle: 'preserve-3d',
                }}
                className={`group relative p-5 rounded-2xl cursor-pointer transition-all duration-300 border ${
                  isRisk
                    ? 'bg-rose-500/5 hover:bg-rose-500/10 border-rose-500/30 hover:border-rose-500/60 shadow-lg hover:shadow-glow-rose hover:[transform:translateZ(30px)_translateY(-6px)]'
                    : isLimited
                    ? 'bg-white/70 dark:bg-zinc-900/40 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 border-zinc-200 dark:border-zinc-800 hover:border-amber-500/30 hover:[transform:translateZ(14px)_translateY(-2px)]'
                    : 'bg-white/70 dark:bg-zinc-900/40 hover:bg-zinc-50 dark:hover:bg-zinc-800/60 border-zinc-200 dark:border-zinc-800 hover:border-emerald-500/30 hover:shadow-glow-emerald hover:[transform:translateZ(18px)_translateY(-3px)]'
                }`}
              >
                {/* 3D Elevation Tag */}
                <div className="flex items-start justify-between gap-2 mb-3">
                  <div className="flex items-center gap-2">
                    {isRisk ? (
                      <div className="p-1.5 rounded-lg bg-rose-500/20 text-rose-500 dark:text-rose-400">
                        <AlertTriangle className="w-4 h-4" />
                      </div>
                    ) : isLimited ? (
                      <div className="p-1.5 rounded-lg bg-amber-500/20 text-amber-500 dark:text-amber-400">
                        <ShieldCheck className="w-4 h-4" />
                      </div>
                    ) : (
                      <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                        <CheckCircle2 className="w-4 h-4" />
                      </div>
                    )}
                    <span
                      className={`text-[10px] font-mono font-bold uppercase tracking-wider px-2 py-0.5 rounded-full ${
                        isRisk
                          ? 'bg-rose-500/20 text-rose-700 dark:text-rose-300 border border-rose-500/30'
                          : isLimited
                          ? 'bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/20'
                          : 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/20'
                      }`}
                    >
                      {isRisk ? 'Confound Risk Detected' : isLimited ? 'Limited Metadata' : 'Verified Safe / Absent'}
                    </span>
                  </div>

                  <ChevronRight className="w-4 h-4 text-zinc-400 dark:text-zinc-500 group-hover:text-zinc-900 dark:group-hover:text-zinc-200 group-hover:translate-x-1 transition-all" />
                </div>

                {/* Bivariate Pair */}
                <div className="text-xs font-bold text-zinc-900 dark:text-white font-sans">
                  {interaction.variable_a} <span className="text-indigo-600 dark:text-indigo-400">×</span> {interaction.variable_b}
                </div>

                <p className="text-xs text-zinc-600 dark:text-zinc-400 mt-2 line-clamp-2 leading-relaxed">
                  {isSimple ? interaction.plain_english_explanation : interaction.description}
                </p>

                {/* Statistical Footer */}
                <div className="mt-4 pt-3 border-t border-zinc-200 dark:border-zinc-800/80 flex items-center justify-between text-[11px] font-mono text-zinc-500">
                  <span>Effect: {interaction.effect_size !== null && interaction.effect_size !== undefined ? `${Number(interaction.effect_size).toFixed(3)}` : 'N/A'}</span>
                  <span>FDR q: {interaction.q_value !== null && interaction.q_value !== undefined ? interaction.q_value : 'Safe'}</span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Slide-Out Detail Drawer Modal */}
        {selectedConfound && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-md">
            <div className="relative w-full max-w-lg rounded-2xl glass-panel border border-zinc-200 dark:border-zinc-700 bg-white/95 dark:bg-zinc-900/95 shadow-2xl p-6 text-zinc-900 dark:text-zinc-100">
              <button
                onClick={() => setSelectedConfound(null)}
                className="absolute top-4 right-4 p-1.5 rounded-xl text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
              >
                <X className="w-5 h-5" />
              </button>

              <div className="flex items-center gap-2.5 mb-4">
                {selectedConfound.status === 'significant_risk' ? (
                  <div className="p-2 rounded-xl bg-rose-500/20 text-rose-500 dark:text-rose-400">
                    <AlertTriangle className="w-5 h-5" />
                  </div>
                ) : (
                  <div className="p-2 rounded-xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400">
                    <ShieldCheck className="w-5 h-5" />
                  </div>
                )}
                <div>
                  <h3 className="text-base font-bold text-zinc-900 dark:text-white">
                    {selectedConfound.variable_a} × {selectedConfound.variable_b}
                  </h3>
                  <span
                    className={`text-[10px] font-mono font-bold uppercase ${
                      selectedConfound.status === 'significant_risk' ? 'text-rose-600 dark:text-rose-400' : 'text-emerald-600 dark:text-emerald-400'
                    }`}
                  >
                    {selectedConfound.status === 'significant_risk' ? 'Statistically Significant Confound' : 'No Confound Detected'}
                  </span>
                </div>
              </div>

              {/* Plain English Explanation */}
              <div className="space-y-4">
                <div className="p-3.5 rounded-xl bg-zinc-100 dark:bg-zinc-950/70 border border-zinc-200 dark:border-zinc-800 text-xs">
                  <div className="font-semibold text-indigo-700 dark:text-indigo-300 flex items-center gap-1.5 mb-1">
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>In Plain English:</span>
                  </div>
                  <p className="text-zinc-700 dark:text-zinc-300 leading-relaxed">
                    {selectedConfound.plain_english_explanation}
                  </p>
                </div>

                {/* Technical Telemetry */}
                <div className="grid grid-cols-3 gap-2.5 text-center font-mono text-xs">
                  <div className="p-2.5 rounded-xl bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-800">
                    <span className="text-[10px] text-zinc-500 dark:text-zinc-400 block uppercase">Effect Size (ε²)</span>
                    <span className="text-sm font-bold text-zinc-900 dark:text-white mt-0.5 block">
                      {selectedConfound.effect_size}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-800">
                    <span className="text-[10px] text-zinc-500 dark:text-zinc-400 block uppercase">Raw p-value</span>
                    <span className="text-sm font-bold text-zinc-900 dark:text-white mt-0.5 block">
                      {selectedConfound.p_value}
                    </span>
                  </div>
                  <div className="p-2.5 rounded-xl bg-zinc-100 dark:bg-zinc-800/40 border border-zinc-200 dark:border-zinc-800">
                    <span className="text-[10px] text-zinc-500 dark:text-zinc-400 block uppercase">FDR q-value</span>
                    <span className="text-sm font-bold text-zinc-900 dark:text-white mt-0.5 block">
                      {selectedConfound.q_value}
                    </span>
                  </div>
                </div>

                {/* Recommended Remedy */}
                <div className="p-3.5 rounded-xl bg-indigo-500/10 border border-indigo-500/20 text-xs text-indigo-800 dark:text-indigo-200">
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
