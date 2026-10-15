import React, { useState } from 'react';
import {
  FolderPlus,
  FolderTree,
  ChevronDown,
  ChevronRight,
  GitCompare,
  Plus,
  Trash2,
  Play,
  RotateCw,
  Clock,
  CheckCircle2,
  XCircle,
  Database,
  PanelLeftClose,
  PanelLeftOpen,
} from 'lucide-react';
import { useApp } from '../../lib/store';
import { api } from '../../lib/api';
import type { Dataset, AnalysisRun } from '../../lib/types';

export const Sidebar: React.FC = () => {
  const {
    datasets,
    selectedDataset,
    setSelectedDataset,
    runs,
    selectedRun,
    setSelectedRun,
    refreshDatasets,
    refreshRuns,
    setIsUploadOpen,
    setIsCompareOpen,
    isUnlocked,
    setIsUnlockModalOpen,
    password,
  } = useApp();

  const [isCollapsed, setIsCollapsed] = useState(false);
  const [expandedDatasets, setExpandedDatasets] = useState<Record<string, boolean>>({});
  const [isDeleting, setIsDeleting] = useState<string | null>(null);

  const toggleExpand = (id: string) => {
    setExpandedDatasets(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const handleDelete = async (e: React.MouseEvent, dataset: Dataset) => {
    e.stopPropagation();
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }
    if (!confirm(`Are you sure you want to delete dataset "${dataset.name}" and all its audit runs?`)) {
      return;
    }
    setIsDeleting(dataset.id);
    try {
      await api.deleteDataset(dataset.id, password);
      await refreshDatasets();
    } catch (err: unknown) {
      alert(`Delete failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setIsDeleting(null);
    }
  };

  const handleStartAudit = async (e: React.MouseEvent, datasetId: string) => {
    e.stopPropagation();
    if (!isUnlocked) {
      setIsUnlockModalOpen(true);
      return;
    }
    try {
      await api.createRun(datasetId, { predict_impact: true, estimate_attributes: true }, password);
      await refreshRuns();
    } catch (err: unknown) {
      alert(`Failed to launch audit: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const getStatusIcon = (status: AnalysisRun['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />;
      case 'running':
        return <RotateCw className="w-3.5 h-3.5 text-indigo-400 animate-spin" />;
      case 'queued':
        return <Clock className="w-3.5 h-3.5 text-amber-400" />;
      case 'failed':
      case 'cancelled':
        return <XCircle className="w-3.5 h-3.5 text-rose-400" />;
    }
  };

  if (isCollapsed) {
    return (
      <aside className="w-14 border-r border-zinc-800 bg-zinc-950/70 p-2 flex flex-col items-center gap-3 shrink-0">
        <button
          onClick={() => setIsCollapsed(false)}
          className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          title="Expand workspace sidebar"
        >
          <PanelLeftOpen className="w-5 h-5" />
        </button>
        <button
          onClick={() => {
            if (!isUnlocked) setIsUnlockModalOpen(true);
            else setIsUploadOpen(true);
          }}
          className="p-2 rounded-xl bg-indigo-600/20 text-indigo-400 hover:bg-indigo-600 hover:text-white transition-colors"
          title="Upload dataset ZIP"
        >
          <Plus className="w-5 h-5" />
        </button>
        <button
          onClick={() => setIsCompareOpen(true)}
          className="p-2 rounded-xl text-zinc-400 hover:text-white hover:bg-zinc-800 transition-colors"
          title="Diff two audits"
        >
          <GitCompare className="w-5 h-5" />
        </button>
      </aside>
    );
  }

  return (
    <aside className="w-64 md:w-72 border-r border-zinc-800/80 bg-zinc-950/70 backdrop-blur-md flex flex-col shrink-0 h-[calc(100vh-4rem)]">
      {/* Top Sidebar Action */}
      <div className="p-3.5 border-b border-zinc-800/80 flex items-center justify-between gap-2">
        <button
          onClick={() => {
            if (!isUnlocked) setIsUnlockModalOpen(true);
            else setIsUploadOpen(true);
          }}
          className="flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs shadow-lg shadow-indigo-950/60 transition-all hover:scale-[1.02] active:scale-[0.98]"
        >
          <FolderPlus className="w-4 h-4" />
          <span>Upload Dataset ZIP</span>
        </button>
        <button
          onClick={() => setIsCollapsed(true)}
          className="p-2 rounded-xl text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/60 transition-colors"
          title="Collapse sidebar"
        >
          <PanelLeftClose className="w-4 h-4" />
        </button>
      </div>

      {/* Dataset Tree & History List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-4">
        <div>
          <div className="flex items-center justify-between text-xs font-semibold text-zinc-400 uppercase tracking-wider px-2 mb-2 font-mono">
            <span className="flex items-center gap-1.5">
              <FolderTree className="w-3.5 h-3.5 text-zinc-500" />
              <span>Datasets ({datasets.length})</span>
            </span>
            <button
              onClick={() => refreshDatasets()}
              className="text-zinc-500 hover:text-zinc-300"
              title="Refresh datasets"
            >
              <RotateCw className="w-3 h-3" />
            </button>
          </div>

          {datasets.length === 0 ? (
            <div className="p-4 text-center rounded-xl bg-zinc-900/40 border border-dashed border-zinc-800 text-zinc-500 text-xs">
              <Database className="w-6 h-6 mx-auto mb-1.5 opacity-50" />
              <span>No datasets yet</span>
            </div>
          ) : (
            <div className="space-y-1">
              {datasets.map(dataset => {
                const isSelected = selectedDataset?.id === dataset.id;
                const isExpanded = expandedDatasets[dataset.id] !== false; // default open
                return (
                  <div key={dataset.id} className="rounded-xl overflow-hidden border border-transparent transition-colors">
                    {/* Dataset Item Header */}
                    <div
                      onClick={() => {
                        setSelectedDataset(dataset);
                        toggleExpand(dataset.id);
                      }}
                      className={`group flex items-center justify-between p-2 rounded-xl cursor-pointer text-xs font-medium transition-all ${
                        isSelected
                          ? 'bg-zinc-800 text-white border-zinc-700/80 shadow-sm'
                          : 'text-zinc-300 hover:bg-zinc-900 hover:text-white'
                      }`}
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        {isExpanded ? (
                          <ChevronDown className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                        ) : (
                          <ChevronRight className="w-3.5 h-3.5 text-zinc-500 shrink-0" />
                        )}
                        <span className="truncate">{dataset.name}</span>
                      </div>
                      <div className="flex items-center gap-1 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button
                          onClick={e => handleStartAudit(e, dataset.id)}
                          className="p-1 rounded text-zinc-400 hover:text-indigo-400 hover:bg-zinc-700"
                          title="Run new audit"
                        >
                          <Play className="w-3 h-3" />
                        </button>
                        <button
                          onClick={e => handleDelete(e, dataset)}
                          disabled={isDeleting === dataset.id}
                          className="p-1 rounded text-zinc-400 hover:text-rose-400 hover:bg-zinc-700 disabled:opacity-50"
                          title="Delete dataset"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    </div>

                    {/* Nested Runs List for Selected Dataset */}
                    {isSelected && isExpanded && (
                      <div className="pl-6 pr-1 py-1 space-y-1 border-l border-zinc-800/80 ml-3.5 my-1">
                        <div className="text-[10px] font-mono text-zinc-500 uppercase tracking-wider py-0.5">
                          Audit Runs ({runs.length})
                        </div>
                        {runs.length === 0 ? (
                          <div className="text-[11px] text-zinc-500 italic py-1 flex items-center justify-between">
                            <span>No audits run yet</span>
                            <button
                              onClick={e => handleStartAudit(e, dataset.id)}
                              className="text-indigo-400 hover:underline flex items-center gap-1"
                            >
                              <Play className="w-2.5 h-2.5" /> Start
                            </button>
                          </div>
                        ) : (
                          runs.map(run => {
                            const isRunSelected = selectedRun?.id === run.id;
                            return (
                              <button
                                key={run.id}
                                onClick={() => setSelectedRun(run)}
                                className={`w-full text-left flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-colors ${
                                  isRunSelected
                                    ? 'bg-indigo-600/20 text-indigo-300 font-semibold border border-indigo-500/30'
                                    : 'text-zinc-400 hover:bg-zinc-900 hover:text-zinc-200'
                                }`}
                              >
                                <div className="flex items-center gap-2 truncate">
                                  {getStatusIcon(run.status)}
                                  <span className="truncate">#{run.id.slice(0, 8)}</span>
                                </div>
                                {run.status === 'running' && (
                                  <span className="text-[10px] text-indigo-400 font-sans">
                                    {run.progress_percent}%
                                  </span>
                                )}
                              </button>
                            );
                          })
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Bottom Footer Action: Diff Two Audits (F1) */}
      <div className="p-3 border-t border-zinc-800/80 bg-zinc-950/90 space-y-2">
        <button
          onClick={() => setIsCompareOpen(true)}
          className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-xl border border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800/80 text-zinc-300 hover:text-white text-xs font-medium transition-colors"
        >
          <GitCompare className="w-4 h-4 text-indigo-400" />
          <span>Compare Two Audits (Diff)</span>
        </button>

        <div className="flex items-center justify-between text-[11px] text-zinc-500 px-1 font-mono">
          <span>Mode: {isUnlocked ? 'Admin Unlocked' : 'Read-Only'}</span>
          {!isUnlocked && (
            <button
              onClick={() => setIsUnlockModalOpen(true)}
              className="text-indigo-400 hover:underline"
            >
              Unlock
            </button>
          )}
        </div>
      </div>
    </aside>
  );
};
