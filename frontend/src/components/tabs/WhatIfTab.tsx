import React, { useState, useEffect } from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { StateView } from '../common/StateView';
import { ReadinessGauge3D } from '../visualization/ReadinessGauge3D';
import { api } from '../../lib/api';
import type { WhatIfResponse } from '../../lib/types';
import {
  Sliders,
  TrendingUp,
  RotateCcw,
  Zap,
  ArrowRight,
} from 'lucide-react';

export const WhatIfTab: React.FC = () => {
  const { report, selectedRun, password, audienceMode } = useApp();
  const isSimple = audienceMode === 'simple';

  const baselineScore = report?.results?.readiness?.overall_score || 64;

  // Initial metric values from report
  const initialMetrics = {
    defect_rate_pct: report?.results?.quality?.defect_rate_pct ?? 8.0,
    cross_split_duplicate_groups: report?.results?.duplicates?.cross_split_duplicate_groups ?? 2,
    redundancy_ratio: report?.results?.duplicates?.redundancy_ratio ?? 0.12,
    label_noise_rate_pct: report?.results?.labels?.label_noise_rate_pct ?? 4.5,
    imbalance_ratio: report?.results?.distribution?.imbalance_ratio ?? 2.8,
    cluster_entropy: report?.results?.diversity?.cluster_entropy ?? 0.72,
  };

  const [sliderValues, setSliderValues] = useState<Record<string, number>>(initialMetrics);
  const [whatIfResult, setWhatIfResult] = useState<WhatIfResponse | null>(null);

  // Sync when report loads
  useEffect(() => {
    if (report) {
      setSliderValues({
        defect_rate_pct: report?.results?.quality?.defect_rate_pct ?? 8.0,
        cross_split_duplicate_groups: report?.results?.duplicates?.cross_split_duplicate_groups ?? 2,
        redundancy_ratio: report?.results?.duplicates?.redundancy_ratio ?? 0.12,
        label_noise_rate_pct: report?.results?.labels?.label_noise_rate_pct ?? 4.5,
        imbalance_ratio: report?.results?.distribution?.imbalance_ratio ?? 2.8,
        cluster_entropy: report?.results?.diversity?.cluster_entropy ?? 0.72,
      });
    }
  }, [report]);

  // Debounced API call to /what-if
  useEffect(() => {
    if (!selectedRun || selectedRun.status !== 'completed') return;

    const timer = setTimeout(async () => {
      try {
        const res = await api.getWhatIf(selectedRun.id, sliderValues, password);
        setWhatIfResult(res);
      } catch (err: unknown) {
        console.warn('What-If simulation error:', err);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [sliderValues, selectedRun, password]);

  const handleSliderChange = (key: string, value: number) => {
    setSliderValues(prev => ({ ...prev, [key]: value }));
  };

  // 1-Click Fix Presets
  const applyPreset = (preset: 'zero_leakage' | 'fix_quality' | 'clean_labels' | 'perfect' | 'reset') => {
    switch (preset) {
      case 'zero_leakage':
        setSliderValues(prev => ({ ...prev, cross_split_duplicate_groups: 0 }));
        break;
      case 'fix_quality':
        setSliderValues(prev => ({ ...prev, defect_rate_pct: 0 }));
        break;
      case 'clean_labels':
        setSliderValues(prev => ({ ...prev, label_noise_rate_pct: 0 }));
        break;
      case 'perfect':
        setSliderValues({
          defect_rate_pct: 0,
          cross_split_duplicate_groups: 0,
          redundancy_ratio: 0.02,
          label_noise_rate_pct: 0,
          imbalance_ratio: 1.0,
          cluster_entropy: 0.95,
        });
        break;
      case 'reset':
        setSliderValues(initialMetrics);
        break;
    }
  };

  if (!selectedRun) {
    return (
      <StateView state="empty" emptyTitle="No Audit Selected">
        <div />
      </StateView>
    );
  }

  const projectedScore = whatIfResult?.what_if_score ?? baselineScore;
  const scoreDelta = whatIfResult?.score_delta ?? (projectedScore - baselineScore);
  const projectedAccuracyGain = Math.max(0, Math.round(scoreDelta * 0.28 * 10) / 10);

  return (
    <div className="space-y-6">
      {/* Intro */}
      <div>
        <div className="flex items-center gap-2">
          <Sliders className="w-5 h-5 text-indigo-400" />
          <h2 className="text-base font-bold text-white font-sans">
            What-If Scenario Sandbox & Accuracy Predictor
          </h2>
        </div>
        <p className="text-xs text-zinc-400 mt-1 max-w-3xl">
          {isSimple
            ? 'Test how much your AI dataset will improve before doing any actual work! Move sliders or click a 1-click fix button to see the projected score increase in real time.'
            : 'Interactive hyperspace rescoring bounded by DIA mathematical readiness weights without modifying underlying sample files.'}
        </p>
      </div>

      {/* 1-Click Preset Action Pills */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        <span className="text-xs font-mono text-zinc-400 mr-1 flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-400" /> 1-Click Fixes:
        </span>
        <button
          onClick={() => applyPreset('zero_leakage')}
          className="px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 text-xs font-medium transition-all hover:scale-[1.02]"
        >
          Remove Cross-Split Leaks
        </button>
        <button
          onClick={() => applyPreset('fix_quality')}
          className="px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 text-xs font-medium transition-all hover:scale-[1.02]"
        >
          Fix Blurry & Dark Photos
        </button>
        <button
          onClick={() => applyPreset('clean_labels')}
          className="px-3 py-1.5 rounded-xl bg-zinc-900 hover:bg-zinc-800 text-zinc-200 border border-zinc-700/80 text-xs font-medium transition-all hover:scale-[1.02]"
        >
          Relabel Noise to 0%
        </button>
        <button
          onClick={() => applyPreset('perfect')}
          className="px-3 py-1.5 rounded-xl bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/40 text-xs font-medium transition-all hover:scale-[1.02]"
        >
          Simulate Pristine Dataset
        </button>
        <button
          onClick={() => applyPreset('reset')}
          className="p-1.5 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800 transition-colors ml-auto"
          title="Reset sliders to baseline"
        >
          <RotateCcw className="w-4 h-4" />
        </button>
      </div>

      {/* Split-Screen Simulator: Left Sliders, Right Live Score Gauge */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Sliders */}
        <div className="lg:col-span-7 space-y-4">
          <GlassCard tilt={false} elevation="sm" className="p-5 space-y-5">
            <h3 className="text-xs font-mono uppercase tracking-wider text-zinc-300 font-bold border-b border-zinc-800 pb-2">
              Hypothetical Metric Adjustments
            </h3>

            {/* Cross-Split Duplicate Groups */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-200 font-semibold">Cross-Split Duplicate Leaks</span>
                <span className={`font-bold ${sliderValues.cross_split_duplicate_groups === 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {sliderValues.cross_split_duplicate_groups} leaked groups
                </span>
              </div>
              <input
                type="range"
                min="0"
                max="10"
                step="1"
                value={sliderValues.cross_split_duplicate_groups}
                onChange={e => handleSliderChange('cross_split_duplicate_groups', Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <span className="text-[11px] text-zinc-500 block">
                {isSimple ? 'Identical images sharing train and test sets' : 'Trips zero-tolerance hard gate if > 0'}
              </span>
            </div>

            {/* Defect Rate % */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-200 font-semibold">Image Defect Rate</span>
                <span className="text-indigo-400 font-bold">{sliderValues.defect_rate_pct.toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="50"
                step="0.5"
                value={sliderValues.defect_rate_pct}
                onChange={e => handleSliderChange('defect_rate_pct', Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <span className="text-[11px] text-zinc-500 block">
                {isSimple ? 'Percentage of images with blur, dark exposure, or low resolution' : 'Weighted Laplacian variance & luminance clipping defects'}
              </span>
            </div>

            {/* Label Noise Rate % */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-200 font-semibold">Label Noise Rate</span>
                <span className="text-indigo-400 font-bold">{sliderValues.label_noise_rate_pct.toFixed(1)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="30"
                step="0.5"
                value={sliderValues.label_noise_rate_pct}
                onChange={e => handleSliderChange('label_noise_rate_pct', Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <span className="text-[11px] text-zinc-500 block">
                {isSimple ? 'Estimated mislabeled images' : 'Confident learning estimated class transition noise'}
              </span>
            </div>

            {/* Redundancy Ratio */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-200 font-semibold">Duplicate Redundancy Ratio</span>
                <span className="text-indigo-400 font-bold">{(sliderValues.redundancy_ratio * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0"
                max="0.5"
                step="0.01"
                value={sliderValues.redundancy_ratio}
                onChange={e => handleSliderChange('redundancy_ratio', Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <span className="text-[11px] text-zinc-500 block">
                {isSimple ? 'Percentage of near-duplicate repeat photos' : 'Perceptual hashing redundancy'}
              </span>
            </div>

            {/* Imbalance Ratio */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-mono">
                <span className="text-zinc-200 font-semibold">Class Imbalance Ratio</span>
                <span className="text-indigo-400 font-bold">{sliderValues.imbalance_ratio.toFixed(1)}x</span>
              </div>
              <input
                type="range"
                min="1.0"
                max="10.0"
                step="0.1"
                value={sliderValues.imbalance_ratio}
                onChange={e => handleSliderChange('imbalance_ratio', Number(e.target.value))}
                className="w-full accent-indigo-500 cursor-pointer"
              />
              <span className="text-[11px] text-zinc-500 block">
                {isSimple ? 'Ratio of biggest category size to smallest category' : 'Max to min class representation disparity'}
              </span>
            </div>
          </GlassCard>
        </div>

        {/* Right Column: Live Projected Gauge & Score Delta */}
        <div className="lg:col-span-5 space-y-4">
          <GlassCard tilt={true} elevation="md" glow={scoreDelta > 0 ? 'emerald' : 'indigo'} className="p-6 text-center">
            <span className="text-[10px] font-mono uppercase tracking-wider text-zinc-400">
              Live Projected Score Simulation
            </span>

            <ReadinessGauge3D
              score={projectedScore}
              verdict={whatIfResult?.readiness?.verdict}
              size={220}
            />

            {/* Score Delta Banner */}
            <div className="mt-4 p-4 rounded-xl bg-zinc-900/80 border border-zinc-800">
              <div className="flex items-center justify-around font-mono">
                <div>
                  <span className="text-[10px] text-zinc-500 uppercase block">Baseline</span>
                  <span className="text-xl font-bold text-zinc-400">{Math.round(baselineScore)}</span>
                </div>
                <ArrowRight className="w-5 h-5 text-indigo-400" />
                <div>
                  <span className="text-[10px] text-zinc-500 uppercase block">Projected</span>
                  <span className="text-xl font-bold text-white">{Math.round(projectedScore)}</span>
                </div>
                <div>
                  <span className="text-[10px] text-zinc-500 uppercase block">Delta</span>
                  <span className={`text-xl font-black ${scoreDelta >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                    {scoreDelta >= 0 ? `+${scoreDelta.toFixed(1)}` : scoreDelta.toFixed(1)}
                  </span>
                </div>
              </div>

              {/* Accuracy Recovery Estimate */}
              {projectedAccuracyGain > 0 && (
                <div className="mt-3 pt-3 border-t border-zinc-800 text-xs text-emerald-300 flex items-center justify-center gap-1.5 font-sans">
                  <TrendingUp className="w-4 h-4 text-emerald-400 shrink-0" />
                  <span>
                    Estimated test accuracy recovery: <strong>+{projectedAccuracyGain}%</strong>
                  </span>
                </div>
              )}
            </div>

            <p className="text-[11px] text-zinc-500 mt-3 italic">
              * Hypothetical rescore calculates weighted dimension impact instantly without modifying raw files.
            </p>
          </GlassCard>
        </div>
      </div>
    </div>
  );
};
