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
    <header className="sticky top-0 z-40 w-full border-b border-zinc-200 dark:border-zinc-800/80 bg-white/80 dark:bg-zinc-950/80 backdrop-blur-xl">
      <div className="flex items-center justify-between h-16 px-4 md:px-6">
        {/* Brand & Context */}
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-lg shadow-indigo-500/25">
            <Layers className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-base font-sans text-zinc-900 dark:text-white">
                DIA <span className="text-indigo-600 dark:text-indigo-400 font-mono text-sm">2.0</span>
              </span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-zinc-100 dark:bg-zinc-800/90 text-zinc-600 dark:text-zinc-400 font-mono border border-zinc-200 dark:border-zinc-700/50">
                PRO STUDIO
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-zinc-500 dark:text-zinc-400">
              <span className="font-medium text-zinc-700 dark:text-zinc-300 truncate max-w-[150px] sm:max-w-[200px]">
                {selectedDataset ? selectedDataset.name : 'No dataset selected'}
              </span>
              {selectedRun && (
                <>
                  <span className="text-zinc-400 dark:text-zinc-600">/</span>
                  <span className="font-mono text-zinc-600 dark:text-zinc-400">
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
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/30 text-indigo-700 dark:text-indigo-300 text-xs font-mono animate-pulse">
            <Activity className="w-3.5 h-3.5 animate-spin" />
            <span>
              {selectedRun.status === 'queued' ? 'Audit Queued...' : `Auditing: ${selectedRun.progress_percent}%`}
            </span>
          </div>
        )}

        {/* Right Controls */}
        <div className="flex items-center gap-2.5">
          {/* Plain English (ELI5) vs Engineer Toggle */}
          <div className="flex items-center rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 p-0.5 text-xs">
            <button
              onClick={() => setAudienceMode('simple')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-all ${
                isSimple
                  ? 'bg-indigo-600 text-white shadow-sm'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200'
              }`}
              title="Explain Like I'm 5: Plain-English explanations for leaders and stakeholders"
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Plain English</span>
              <span className="sm:hidden">ELI5</span>
            </button>
            <button
              onClick={() => setAudienceMode('engineer')}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-lg font-medium transition-all ${
                !isSimple
                  ? 'bg-white dark:bg-zinc-800 text-indigo-600 dark:text-indigo-300 font-mono shadow-sm'
                  : 'text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 font-mono'
              }`}
              title="Engineer Mode: Full statistical formulas, p-values, and raw telemetry"
            >
              <Cpu className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Technical</span>
              <span className="sm:hidden">Stats</span>
            </button>
          </div>

          {/* Password Unlock Status Button (G1) */}
          <button
            onClick={() => setIsUnlockModalOpen(true)}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl border text-xs transition-colors ${
              isUnlocked
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-700 dark:text-emerald-300 hover:bg-emerald-500/20'
                : 'bg-zinc-100 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-200 dark:hover:bg-zinc-800/80'
            }`}
            title={isUnlocked ? 'Studio unlocked (write access enabled)' : 'Click to unlock full admin write access'}
          >
            {isUnlocked ? <Unlock className="w-3.5 h-3.5" /> : <Lock className="w-3.5 h-3.5" />}
            <span className="hidden md:inline font-mono">
              {isUnlocked ? 'Unlocked' : 'Read-Only'}
            </span>
          </button>

          {/* Daylight / Night theme toggle */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-xl bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-600 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-100 hover:bg-zinc-200 dark:hover:bg-zinc-800 transition-colors"
            title={`Switch to ${theme === 'dark' ? 'Daylight' : 'Dark'} mode`}
          >
            {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
        </div>
      </div>
    </header>
  );
};
