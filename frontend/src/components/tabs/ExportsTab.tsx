import React from 'react';
import { useApp } from '../../lib/store';
import { GlassCard } from '../common/GlassCard';
import { StateView } from '../common/StateView';
import { api } from '../../lib/api';
import {
  Download,
  FileCode,
  FileSpreadsheet,
  FileText,
  Scale,
  ArrowRight,
} from 'lucide-react';

export const ExportsTab: React.FC = () => {
  const { selectedRun, password, audienceMode, setIsCompareOpen } = useApp();
  const isSimple = audienceMode === 'simple';

  if (!selectedRun) {
    return (
      <StateView state="empty" emptyTitle="No Audit Selected">
        <div />
      </StateView>
    );
  }

  const exportCards: Array<{
    title: string;
    ext: string;
    icon: React.ReactNode;
    description: string;
    formatKey: 'manifest_csv' | 'html' | 'datasheet_md' | 'manifest_json';
    badge: string;
    badgeColor: string;
  }> = [
    {
      title: 'Actionable Clean-Up Fix List',
      ext: 'CSV / JSON',
      icon: <FileSpreadsheet className="w-6 h-6 text-emerald-600" />,
      description: isSimple
        ? 'A spreadsheet listing every duplicate photo to delete and every wrong label to correct, ready for your team.'
        : 'Machine-actionable remediation manifest containing sample IDs, defect taxonomy, and automated deduplication actions.',
      formatKey: 'manifest_csv',
      badge: 'Immediate Fixes',
      badgeColor: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    },
    {
      title: 'Standalone Executive Audit Report',
      ext: 'HTML',
      icon: <FileCode className="w-6 h-6 text-sky-600" />,
      description: isSimple
        ? 'A clean, beautiful visual report that opens in any browser. Perfect to email stakeholders or managers.'
        : 'Zero-dependency standalone HTML document embedding interactive WebGL diagnostics and integrity health scoring.',
      formatKey: 'html',
      badge: 'Stakeholder Ready',
      badgeColor: 'bg-sky-50 text-sky-800 border-sky-200',
    },
    {
      title: 'Dataset Datasheet & Model Card',
      ext: 'Markdown / JSON',
      icon: <FileText className="w-6 h-6 text-amber-600" />,
      description: isSimple
        ? 'Standard documentation describing how the data was collected, its quality, and its intended use for compliance.'
        : 'Standardized Gebru et al. Datasheet for Datasets for ISO/IEC AI compliance, audit logs, and GitHub repositories.',
      formatKey: 'datasheet_md',
      badge: 'Compliance & Governance',
      badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
    },
    {
      title: 'Full Lossless Diagnostic Metrics',
      ext: 'JSON',
      icon: <FileCode className="w-6 h-6 text-purple-600" />,
      description: isSimple
        ? 'All numbers and raw test findings for researchers and machine learning engineers.'
        : 'Complete lossless telemetry dump with p-values, 5-fold cross-validation logits, and pHash Hamming clusters.',
      formatKey: 'manifest_json',
      badge: 'Lossless Raw Data',
      badgeColor: 'bg-purple-50 text-purple-800 border-purple-200',
    },
  ];

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      {/* Top Header */}
      <div>
        <h2 className="text-base font-bold text-stone-900 dark:text-stone-100 flex items-center gap-2">
          <Download className="w-5 h-5 text-amber-600" />
          <span>1-Click Exports & Compliance Reports</span>
        </h2>
        <p className="text-xs text-stone-500 mt-0.5">
          {isSimple
            ? 'Download ready-to-use clean-up lists, executive summaries, or compare multiple audit runs.'
            : 'Export standardized audit artifacts and reproducible research records.'}
        </p>
      </div>

      {/* 4 Large Export Cards (2x2 Grid) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {exportCards.map((card, idx) => (
          <GlassCard
            key={idx}
            tilt={true}
            elevation="sm"
            className="p-6 flex flex-col justify-between hover:border-stone-300 dark:hover:border-stone-700 transition-all"
          >
            <div>
              <div className="flex items-start justify-between gap-3">
                <div className="p-3 rounded-2xl bg-stone-100 dark:bg-stone-800">
                  {card.icon}
                </div>
                <span className={`text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${card.badgeColor}`}>
                  {card.badge}
                </span>
              </div>

              <h3 className="text-sm font-bold text-stone-900 dark:text-stone-100 mt-4">
                {card.title}
              </h3>
              <p className="text-xs text-stone-500 dark:text-stone-400 mt-1 leading-relaxed">
                {card.description}
              </p>
            </div>

            <div className="mt-6 pt-4 border-t border-stone-100 dark:border-stone-800 flex items-center justify-between">
              <span className="text-[11px] font-mono text-stone-400">
                Format: <strong>{card.ext}</strong>
              </span>
              <button
                onClick={() => {
                  const url = api.getExportUrl(selectedRun.id, card.formatKey, password);
                  window.open(url, '_blank');
                }}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-stone-900 hover:bg-stone-800 text-white dark:bg-stone-100 dark:text-stone-900 dark:hover:bg-white text-xs font-semibold shadow-warm-sm transition-all"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Download</span>
              </button>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Before vs After Run Comparison Card */}
      <div className="p-6 rounded-3xl bg-white dark:bg-[#221F1D] border border-stone-200/80 dark:border-stone-800 shadow-warm-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-2xl bg-indigo-50 dark:bg-indigo-950/40 text-indigo-600">
            <Scale className="w-6 h-6" />
          </div>
          <div>
            <h4 className="text-sm font-bold text-stone-900 dark:text-white">
              Before vs. After Run Comparator
            </h4>
            <p className="text-xs text-stone-500 mt-0.5">
              Compare this audit run against a previous run to verify that your clean-up actions improved health scores.
            </p>
          </div>
        </div>

        <button
          onClick={() => setIsCompareOpen(true)}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-warm-sm whitespace-nowrap transition-all"
        >
          <span>Compare Two Runs</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
