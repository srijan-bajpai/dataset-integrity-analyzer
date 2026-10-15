import React from 'react';
import { AlertCircle, RefreshCw, FolderSearch, HelpCircle } from 'lucide-react';
import { cn } from '../../lib/utils';

export type ViewState = 'ideal' | 'loading' | 'empty' | 'error' | 'partial';

interface StateViewProps {
  state: ViewState;
  loadingSkeleton?: React.ReactNode;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: {
    label: string;
    onClick: () => void;
  };
  errorMessage?: string | null;
  onRetry?: () => void;
  partialNotice?: string;
  children: React.ReactNode;
  className?: string;
}

export const StateView: React.FC<StateViewProps> = ({
  state,
  loadingSkeleton,
  emptyTitle = 'No data available',
  emptyDescription = 'There is currently no information to display.',
  emptyAction,
  errorMessage,
  onRetry,
  partialNotice,
  children,
  className,
}) => {
  if (state === 'loading') {
    if (loadingSkeleton) return <div className={className}>{loadingSkeleton}</div>;
    return (
      <div className={cn('p-8 space-y-4 animate-pulse', className)}>
        <div className="h-8 bg-zinc-200 dark:bg-zinc-800/60 rounded-xl w-1/3" />
        <div className="h-32 bg-zinc-200 dark:bg-zinc-800/40 rounded-2xl w-full" />
        <div className="grid grid-cols-3 gap-4">
          <div className="h-24 bg-zinc-200 dark:bg-zinc-800/40 rounded-xl" />
          <div className="h-24 bg-zinc-200 dark:bg-zinc-800/40 rounded-xl" />
          <div className="h-24 bg-zinc-200 dark:bg-zinc-800/40 rounded-xl" />
        </div>
      </div>
    );
  }

  if (state === 'error') {
    return (
      <div className={cn('p-12 text-center rounded-2xl border border-rose-500/20 bg-rose-500/5 glass-panel', className)}>
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-rose-500/20 text-rose-500 dark:text-rose-400 mb-4">
          <AlertCircle className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">Unable to load telemetry</h3>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1 max-w-md mx-auto">
          {errorMessage || 'A network error occurred while communicating with the audit service.'}
        </p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-5 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-rose-600 hover:bg-rose-500 rounded-xl transition-colors shadow-lg shadow-rose-950/50"
          >
            <RefreshCw className="w-4 h-4" />
            <span>Retry Operation</span>
          </button>
        )}
      </div>
    );
  }

  if (state === 'empty') {
    return (
      <div className={cn('p-12 text-center rounded-2xl border border-zinc-200 dark:border-zinc-800 glass-panel', className)}>
        <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-zinc-100 dark:bg-zinc-800 text-zinc-600 dark:text-zinc-400 mb-4">
          <FolderSearch className="w-6 h-6" />
        </div>
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">{emptyTitle}</h3>
        <p className="text-sm text-zinc-600 dark:text-zinc-400 mt-1 max-w-md mx-auto">{emptyDescription}</p>
        {emptyAction && (
          <button
            onClick={emptyAction.onClick}
            className="mt-5 inline-flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-500 rounded-xl transition-colors shadow-lg shadow-indigo-950/50"
          >
            <span>{emptyAction.label}</span>
          </button>
        )}
      </div>
    );
  }

  return (
    <div className={cn('space-y-4', className)}>
      {state === 'partial' && partialNotice && (
        <div className="flex items-center gap-2 p-3 text-xs rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-300">
          <HelpCircle className="w-4 h-4 shrink-0" />
          <span>{partialNotice}</span>
        </div>
      )}
      {children}
    </div>
  );
};
