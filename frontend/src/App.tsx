import React from 'react';
import { AppProvider, useApp, type TabKey } from './lib/store';
import { Header } from './components/layout/Header';
import { Sidebar } from './components/layout/Sidebar';
import { OverviewTab } from './components/tabs/OverviewTab';
import { MapPhotosTab } from './components/tabs/MapPhotosTab';
import { WhatIfTab } from './components/tabs/WhatIfTab';
import { ExportsTab } from './components/tabs/ExportsTab';
import { UploadZipModal } from './components/upload/UploadZipModal';
import { RunCompareModal } from './components/compare/RunCompareModal';
import { UnlockModal } from './components/common/UnlockModal';
import {
  LayoutDashboard,
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
    { key: 'overview', label: '1. Overview & Action Plan', icon: <LayoutDashboard className="w-4 h-4" /> },
    { key: 'map', label: '2. 3D Map & Photos', icon: <Layers className="w-4 h-4" /> },
    { key: 'whatif', label: '3. What-If Simulator', icon: <Sliders className="w-4 h-4" />, badge: 'Simulator' },
    { key: 'exports', label: '4. Exports & Reports', icon: <FileSearch className="w-4 h-4" /> },
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
    <div className="min-h-screen bg-[#FAF8F5] dark:bg-[#181614] text-stone-900 dark:text-stone-100 flex flex-col antialiased selection:bg-amber-500/20 selection:text-amber-900 font-sans">
      {/* Top Header */}
      <Header />

      <div className="flex-1 flex overflow-hidden">
        {/* Collapsible Left Sidebar */}
        <Sidebar />

        {/* Main Content Workspace */}
        <main className="flex-1 flex flex-col overflow-y-auto bg-warm-grid">
          {/* Live Progress Banner for Active Audits */}
          {selectedRun && (selectedRun.status === 'running' || selectedRun.status === 'queued') && (
            <div className="bg-amber-500/10 border-b border-amber-500/30 p-3.5 px-6 flex items-center justify-between text-xs text-amber-900 dark:text-amber-200">
              <div className="flex items-center gap-3">
                <RotateCw className="w-4 h-4 text-amber-600 animate-spin shrink-0" />
                <span>
                  <strong>Run #{selectedRun.id.slice(0, 8)}:</strong> {selectedRun.status_message || 'Analyzing dataset integrity...'} ({selectedRun.progress_percent}%)
                </span>
              </div>
              <button
                onClick={handleCancelRun}
                className="px-3 py-1 rounded-xl bg-white dark:bg-stone-900 hover:bg-stone-100 dark:hover:bg-stone-800 text-stone-700 dark:text-stone-300 border border-stone-300 dark:border-stone-700 text-xs font-mono transition-colors"
              >
                Cancel Audit
              </button>
            </div>
          )}

          {/* 4 Focused Views Tab Navigation Bar */}
          <div className="border-b border-stone-200/80 dark:border-stone-800 bg-white/70 dark:bg-[#181614]/70 backdrop-blur-md px-6 pt-3 sticky top-0 z-30">
            <nav className="flex space-x-2 overflow-x-auto pb-px max-w-6xl mx-auto">
              {tabs.map(tab => {
                const isActive = activeTab === tab.key;
                return (
                  <button
                    key={tab.key}
                    onClick={() => setActiveTab(tab.key)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-t-2xl text-xs font-medium whitespace-nowrap transition-all border-b-2 ${
                      isActive
                        ? 'border-amber-600 text-stone-900 dark:text-white bg-white dark:bg-[#221F1D] shadow-warm-sm'
                        : 'border-transparent text-stone-500 dark:text-stone-400 hover:text-stone-900 dark:hover:text-stone-200 hover:bg-stone-100/60 dark:hover:bg-stone-800/40'
                    }`}
                  >
                    <span className={isActive ? 'text-amber-600' : 'text-stone-400'}>
                      {tab.icon}
                    </span>
                    <span>{tab.label}</span>
                    {tab.badge && (
                      <span className="text-[9px] font-mono uppercase px-2 py-0.5 rounded-full bg-amber-500/10 text-amber-700 dark:text-amber-300 border border-amber-500/30">
                        {tab.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Active Tab Screen */}
          <div className="flex-1 p-6 md:p-8 max-w-6xl w-full mx-auto">
            {activeTab === 'overview' && <OverviewTab />}
            {activeTab === 'map' && <MapPhotosTab />}
            {activeTab === 'whatif' && <WhatIfTab />}
            {activeTab === 'exports' && <ExportsTab />}
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
