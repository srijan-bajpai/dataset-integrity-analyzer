import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import type { Dataset, AnalysisRun, ReportData } from './types';
import { api, ApiError } from './api';

export type AudienceMode = 'simple' | 'engineer';
export type TabKey = 'overview' | 'map' | 'whatif' | 'exports';

interface AppContextValue {
  theme: 'dark' | 'light';
  toggleTheme: () => void;
  audienceMode: AudienceMode;
  setAudienceMode: (m: AudienceMode) => void;
  password: string | null;
  setPassword: (pwd: string | null) => void;
  isUnlocked: boolean;
  
  // Datasets
  datasets: Dataset[];
  selectedDataset: Dataset | null;
  setSelectedDataset: (d: Dataset | null) => void;
  datasetsError: string | null;
  refreshDatasets: () => Promise<void>;
  
  // Runs
  runs: AnalysisRun[];
  selectedRun: AnalysisRun | null;
  setSelectedRun: (r: AnalysisRun | null) => void;
  refreshRuns: () => Promise<void>;
  
  // Report data for selected run
  report: ReportData | null;
  isLoadingReport: boolean;
  reportError: string | null;
  refreshReport: () => Promise<void>;

  // Navigation
  activeTab: TabKey;
  setActiveTab: (tab: TabKey) => void;

  // Modals
  isUploadOpen: boolean;
  setIsUploadOpen: (open: boolean) => void;
  isCompareOpen: boolean;
  setIsCompareOpen: (open: boolean) => void;
  isUnlockModalOpen: boolean;
  setIsUnlockModalOpen: (open: boolean) => void;
}

const AppContext = createContext<AppContextValue | null>(null);

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<'dark' | 'light'>(() => {
    return (localStorage.getItem('dia_theme') as 'dark' | 'light') || 'light';
  });
  
  const [audienceMode, setAudienceModeState] = useState<AudienceMode>(() => {
    return (localStorage.getItem('dia_audience_mode') as AudienceMode) || 'simple';
  });

  const [password, setPasswordState] = useState<string | null>(() => {
    return sessionStorage.getItem('dia_password') || null;
  });

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [runs, setRuns] = useState<AnalysisRun[]>([]);
  const [selectedRun, setSelectedRun] = useState<AnalysisRun | null>(null);
  const [report, setReport] = useState<ReportData | null>(null);
  const [isLoadingReport, setIsLoadingReport] = useState<boolean>(false);
  const [reportError, setReportError] = useState<string | null>(null);

  const [activeTab, setActiveTab] = useState<TabKey>('overview');
  const [isUploadOpen, setIsUploadOpen] = useState<boolean>(false);
  const [isCompareOpen, setIsCompareOpen] = useState<boolean>(false);
  const [isUnlockModalOpen, setIsUnlockModalOpen] = useState<boolean>(false);

  const [datasetsError, setDatasetsError] = useState<string | null>(null);

  // Sync theme
  useEffect(() => {
    localStorage.setItem('dia_theme', theme);
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
    } else {
      root.classList.remove('dark');
      root.classList.add('light');
    }
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prev => (prev === 'dark' ? 'light' : 'dark'));
  };

  const setAudienceMode = (mode: AudienceMode) => {
    setAudienceModeState(mode);
    localStorage.setItem('dia_audience_mode', mode);
  };

  const setPassword = (pwd: string | null) => {
    setPasswordState(pwd);
    if (pwd) {
      sessionStorage.setItem('dia_password', pwd);
    } else {
      sessionStorage.removeItem('dia_password');
    }
  };

  const isUnlocked = Boolean(password && password.trim().length > 0);

  // Refresh datasets
  const refreshDatasets = useCallback(async () => {
    setDatasetsError(null);
    try {
      const data = await api.getDatasets(password);
      setDatasets(data);
      setSelectedDataset(prev => {
        if (data.length === 0) return null;
        if (!prev || !data.some(d => d.id === prev.id)) {
          return data[0];
        }
        return data.find(d => d.id === prev.id) || prev;
      });
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch datasets';
      setDatasetsError(msg);
      if (err instanceof ApiError && err.status === 401) {
        setIsUnlockModalOpen(true);
      }
    }
  }, [password]);

  // Refresh runs when dataset changes
  const refreshRuns = useCallback(async () => {
    if (!selectedDataset) {
      setRuns([]);
      setSelectedRun(null);
      return;
    }
    try {
      const datasetDetail = await api.getDataset(selectedDataset.id, password);
      const runSummaries = datasetDetail.runs || [];
      const detailedRuns: AnalysisRun[] = await Promise.all(
        runSummaries.map(async r => {
          try {
            return await api.getRun(r.id, password);
          } catch {
            return {
              id: r.id,
              dataset_id: selectedDataset.id,
              status: r.status as AnalysisRun['status'],
              created_at: r.created_at || null,
              started_at: null,
              completed_at: null,
              progress_percent: 0,
              status_message: r.status,
              duration_seconds: null,
              error_message: null,
              report_url: null,
            };
          }
        })
      );
      setRuns(detailedRuns);
      if (detailedRuns.length > 0) {
        setSelectedRun(prev => {
          if (prev && detailedRuns.some(r => r.id === prev.id)) {
            return detailedRuns.find(r => r.id === prev.id) || prev;
          }
          const latestCompleted = detailedRuns.find(r => r.status === 'completed');
          return latestCompleted || detailedRuns[0];
        });
      } else {
        setSelectedRun(null);
      }
    } catch {
      setRuns([]);
      setSelectedRun(null);
    }
  }, [selectedDataset?.id, password]); // eslint-disable-line react-hooks/exhaustive-deps

  // Refresh report for selected run
  const refreshReport = useCallback(async () => {
    if (!selectedRun) {
      setReport(null);
      setReportError(null);
      return;
    }
    if (selectedRun.status !== 'completed') {
      setReport(null);
      setReportError(null);
      return;
    }
    setIsLoadingReport(true);
    setReportError(null);
    try {
      const rep = await api.getReport(selectedRun.id, password);
      setReport(rep);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch report';
      setReportError(msg);
      setReport(null);
    } finally {
      setIsLoadingReport(false);
    }
  }, [selectedRun?.id, selectedRun?.status, password]);

  // Initial load
  useEffect(() => {
    refreshDatasets();
  }, [refreshDatasets]);

  // Load runs on dataset change
  useEffect(() => {
    refreshRuns();
  }, [refreshRuns]);

  // Load report on run change
  useEffect(() => {
    refreshReport();
  }, [refreshReport]);

  // Poll running jobs
  useEffect(() => {
    if (!selectedRun || (selectedRun.status !== 'running' && selectedRun.status !== 'queued')) {
      return;
    }
    const interval = setInterval(async () => {
      try {
        const updated = await api.getRun(selectedRun.id, password);
        setSelectedRun(updated);
        setRuns(prev => prev.map(r => (r.id === updated.id ? updated : r)));
      } catch {
        // ignore polling errors
      }
    }, 2000);
    return () => clearInterval(interval);
  }, [selectedRun?.id, selectedRun?.status, password]);

  return (
    <AppContext.Provider
      value={{
        theme,
        toggleTheme,
        audienceMode,
        setAudienceMode,
        password,
        setPassword,
        isUnlocked,
        datasets,
        selectedDataset,
        setSelectedDataset,
        datasetsError,
        refreshDatasets,
        runs,
        selectedRun,
        setSelectedRun,
        refreshRuns,
        report,
        isLoadingReport,
        reportError,
        refreshReport,
        activeTab,
        setActiveTab,
        isUploadOpen,
        setIsUploadOpen,
        isCompareOpen,
        setIsCompareOpen,
        isUnlockModalOpen,
        setIsUnlockModalOpen,
      }}
    >
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
};
