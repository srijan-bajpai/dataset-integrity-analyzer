import React from 'react';
import { AppProvider, useApp, type TabKey } from './lib/store';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { OverviewTab } from './components/tabs/OverviewTab';
import { DimensionsTab } from './components/tabs/DimensionsTab';
import { ConfoundsTab } from './components/tabs/ConfoundsTab';
import { WhatIfTab } from './components/tabs/WhatIfTab';
import { TriageTab } from './components/tabs/TriageTab';
import { UploadZipModal } from './components/upload/UploadZipModal';
import { RunCompareModal } from './components/compare/RunCompareModal';
import { UnlockModal } from './components/common/UnlockModal';
import {
  LayoutDashboard,
  Activity,
  Layers,
  Sliders,
  FileSearch,
  RotateCw,
} from 'lucide-react';
import { api } from './lib/api';

const MainLayout: React.FC = () => {
  const {
    activeTab,
    setActiveTab,
    selectedRun,
    password,
    refreshRuns,
  } = useApp();

  const tabs: { key: TabKey; label: string; icon: React.ReactNode; badge?: string }[] = [
    { key: 'overview', label: '1. Overview & Readiness', icon: <LayoutDashboard className="w-4 h-4" /> },
    { key: 'dimensions', label: '2. 6 Dimensions', icon: <Activity className="w-4 h-4" /> },
    { key: 'confounds', label: '3. Hidden Confounds (C1)', icon: <Layers className="w-4 h-4" />, badge: 'Novel' },
    { key: 'whatif', label: '4. What-If & Impact (C2)', icon: <Sliders className="w-4 h-4" />, badge: 'Simulator' },
    { key: 'triage', label: '5. Sample Triage & Exports', icon: <FileSearch className="w-4 h-4" /> },
  ];

  const handleCancelRun = async () => {
    if (!selectedRun) return;
    try {
      await api.cancelRun(selectedRun.id, password);
      await refreshRuns();
    } catch (err: unknown) {
      alert(`Cancel failed: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-100 flex flex-col antialiased selection:bg-indigo-500/30 selection:text-indigo-200">
      {/* Top Header */}
      <Header />

      <div className="flex-1 flex overflow-hidden">
        {/* Collapsible Left Sidebar */}
        <Sidebar />

        {/* Main Content Workspace */}
        <main className="flex-1 flex flex-col overflow-y-auto bg-telemetry-grid">
          {/* Live Progress Banner for Active Audits */}
          {selectedRun && (selectedRun.status === 'running' || selectedRun.status === 'queued') && (
            <div className="bg-indigo-500/10 dark:bg-indigo-950/80 border-b border-indigo-500/30 p-3 px-6 flex items-center justify-between text-xs text-indigo-700 dark:text-indigo-200">
              <div className="flex items-center gap-3">
                <RotateCw className="w-4 h-4 text-indigo-500 dark:text-indigo-400 animate-spin shrink-0" />
                <span>
                  <strong>Run #{selectedRun.id.slice(0, 8)}:</strong> {selectedRun.status_message || 'Analyzing dataset integrity...'} ({selectedRun.progress_percent}%)
                </span>
              </div>
              <button
                onClick={handleCancelRun}
                className="px-2.5 py-1 rounded-lg bg-white dark:bg-zinc-900 hover:bg-zinc-100 dark:hover:bg-zinc-800 text-zinc-700 dark:text-zinc-300 border border-zinc-300 dark:border-zinc-700 text-xs font-mono transition-colors"
              >
                Cancel Audit
              </button>
            </div>
          )}

          {/* Studio Tab Navigation Bar */}
          <div className="border-b border-zinc-200 dark:border-zinc-800/80 bg-white/70 dark:bg-zinc-950/70 backdrop-blur-md px-4 sm:px-6 pt-3">
            <nav className="flex space-x-1 sm:space-x-2 overflow-x-auto pb-px">
              {tabs.map(tab => {
                const isActive = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center gap-2 px-3.5 py-2.5 rounded-t-xl text-xs font-medium whitespace-nowrap transition-all border-b-2 ${
                      isActive
                        ? 'border-indigo-500 text-zinc-900 dark:text-white bg-white/90 dark:bg-zinc-900/90 shadow-sm'
                        : 'border-transparent text-zinc-500 dark:text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-900/40'
                    }`}
                  >
                    <span className={isActive ? 'text-indigo-600 dark:text-indigo-400' : 'text-zinc-400 dark:text-zinc-500'}>
                      {tab.icon}
                    </span>
                    <span>{tab.label}</span>
                    {tab.badge && (
                      <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Active Tab Screen */}
          <div className="flex-1 p-4 sm:p-6 md:p-8 max-w-7xl w-full mx-auto">
            {activeTab === 'overview' && <OverviewTab />}
            {activeTab === 'dimensions' && <DimensionsTab />}
            {activeTab === 'confounds' && <ConfoundsTab />}
            {activeTab === 'whatif' && <WhatIfTab />}
            {activeTab === 'triage' && <TriageTab />}
          </div>
        </main>
      </div>

      {/* Global Modals */}
      <UploadZipModal />
      <RunCompareModal />
      <UnlockModal />
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AppProvider>
      <MainLayout />
    </AppProvider>
  );
};

export default App;
