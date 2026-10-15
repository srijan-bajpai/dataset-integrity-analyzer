import React from 'react';
import {
  Sparkles,
  Cpu,
  Sun,
  Moon,
  Lock,
  Unlock,
  Activity,
  Layers,
} from 'lucide-react';
import { useApp } from '../../lib/store';
import { ReadinessBadge } from '../common/ReadinessBadge';

export const Header: React.FC = () => {
  const {
    theme,
    toggleTheme,
    audienceMode,
    setAudienceMode,
    isUnlocked,
    setIsUnlockModalOpen,
    selectedDataset,
    selectedRun,
    report,
  } = useApp();

  const isSimple = audienceMode === 'simple';
  const overallScore = report?.results?.readiness?.overall_score;

  return (
    <header className="sticky top-0 z-40 w-full border-b border-stone-200/80 dark:border-stone-800 bg-[#FAF8F5]/90 dark:bg-[#181614]/90 backdrop-blur-md">
      <div className="flex items-center justify-between h-16 px-4 md:px-6">
        {/* Brand & Context */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-2xl bg-gradient-to-br from-amber-500 to-terracotta-600 text-white shadow-warm-sm">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-base font-sans text-stone-900 dark:text-white">
                DIA <span className="text-amber-700 dark:text-amber-400 font-mono text-sm">2.0</span>
              </span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-amber-50 dark:bg-amber-950/40 text-amber-900 dark:text-amber-200 font-mono border border-amber-200/80 dark:border-amber-800">
                WARM STUDIO
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-stone-500 dark:text-stone-400">
              <span className="font-medium text-stone-700 dark:text-stone-300 truncate max-w-[150px] sm:max-w-[200px]">
                {selectedDataset ? selectedDataset.name : 'No dataset selected'}
              </span>
              {selectedRun && (
                <>
                  <span className="text-stone-400">/</span>
                  <span className="font-mono text-stone-500">
                    Run #{selectedRun.id.slice(0, 6)}
                  </span>
                </>
              )}
            </div>
          </div>
        </div>

        {/* Center: Live Readiness Quick Pill (if completed) */}
        {selectedRun?.status === 'completed' && overallScore !== undefined && (
          <div className="hidden lg:flex items-center gap-2">
            <ReadinessBadge score={overallScore} size="sm" />
          </div>
        )}

        {/* Center: Live Running Status (if in progress) */}
        {selectedRun && (selectedRun.status === 'running' || selectedRun.status === 'queued') && (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-mono animate-pulse">
            <Activity className="w-3.5 h-3.5 animate-spin" />
            <span>
              {selectedRun.status === 'queued' ? 'Audit Queued...' : `Auditing: ${selectedRun.progress_percent}%`}
            </span>
          </div>
        )}

        {/* Right Controls */}
        <div className="flex items-center gap-2.5">
          {/* Layman vs Technical Jargon Toggle */}
          <div className="flex items-center rounded-2xl bg-stone-100 dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 p-0.5 text-xs">
            <button
              onClick={() => setAudienceMode('simple')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-medium transition-all ${
                isSimple
                  ? 'bg-white dark:bg-stone-800 text-stone-900 dark:text-white shadow-warm-sm'
                  : 'text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200'
              }`}
              title="Layman View: Plain-English explanations without statistics jargon"
            >
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              <span className="hidden sm:inline">Layman View</span>
              <span className="sm:hidden">Simple</span>
            </button>
            <button
              onClick={() => setAudienceMode('engineer')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl font-medium transition-all ${
                !isSimple
                  ? 'bg-white dark:bg-stone-800 text-stone-900 dark:text-white font-mono shadow-warm-sm'
                  : 'text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 font-mono'
              }`}
              title="Technical View: Statistical formulas, FDR q-values, and raw tests"
            >
              <Cpu className="w-3.5 h-3.5 text-indigo-500" />
              <span className="hidden sm:inline">Technical (Jargon)</span>
              <span className="sm:hidden">Stats</span>
            </button>
          </div>

          {/* Password Unlock Status Button */}
          <button
            onClick={() => setIsUnlockModalOpen(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-2xl border text-xs transition-colors ${
              isUnlocked
                ? 'bg-sage-50 border-sage-200 text-sage-800 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800'
                : 'bg-stone-100 dark:bg-stone-900 border-stone-200 dark:border-stone-800 text-stone-600 dark:text-stone-400 hover:text-stone-900'
            }`}
            title={isUnlocked ? 'Studio unlocked (write access enabled)' : 'Click to unlock full admin write access'}
          >
            {isUnlocked ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
            <span className="hidden md:inline font-mono">
              {isUnlocked ? 'Unlocked' : 'Read-Only'}
            </span>
          </button>

          {/* Theme Toggle (Daylight / Night) */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-2xl bg-stone-100 dark:bg-stone-900 border border-stone-200/80 dark:border-stone-800 text-stone-600 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-100 transition-colors"
            title={`Switch to ${theme === 'dark' ? 'Daylight (Warm Paper)' : 'Dark (Warm Obsidian)'} mode`}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
