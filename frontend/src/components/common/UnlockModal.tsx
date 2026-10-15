import React, { useState } from 'react';
import { Lock, KeyRound, X, CheckCircle2, ShieldAlert, RotateCw } from 'lucide-react';
import { useApp } from '../../lib/store';
import { api } from '../../lib/api';

export const UnlockModal: React.FC = () => {
  const { isUnlockModalOpen, setIsUnlockModalOpen, setPassword, isUnlocked, refreshDatasets } = useApp();
  const [inputVal, setInputVal] = useState('');
  const [isVerifying, setIsVerifying] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isUnlockModalOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const candidate = inputVal.trim();
    if (!candidate) {
      setError('Please enter a password');
      return;
    }
    setIsVerifying(true);
    setError(null);
    try {
      const isValid = await api.verifyPassword(candidate);
      if (!isValid) {
        setError('Incorrect password. Access was rejected by the server.');
        setIsVerifying(false);
        return;
      }
      setPassword(candidate);
      setIsUnlockModalOpen(false);
      setInputVal('');
      await refreshDatasets();
    } catch {
      setError('Network error while validating password.');
    } finally {
      setIsVerifying(false);
    }
  };

  const handleLock = () => {
    setPassword(null);
    setIsUnlockModalOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/70 backdrop-blur-md">
      <div className="relative w-full max-w-md rounded-2xl glass-panel border border-zinc-200 dark:border-zinc-700/60 shadow-2xl p-6 bg-white dark:bg-zinc-900/90 text-zinc-900 dark:text-zinc-100">
        <button
          onClick={() => setIsUnlockModalOpen(false)}
          className="absolute top-4 right-4 p-1 rounded-lg text-zinc-400 hover:text-zinc-900 dark:hover:text-zinc-200 hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-3 mb-4">
          <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-500 dark:text-indigo-400 border border-indigo-500/30">
            {isUnlocked ? <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" /> : <Lock className="w-5 h-5" />}
          </div>
          <div>
            <h3 className="text-base font-semibold text-zinc-900 dark:text-white">
              {isUnlocked ? 'Studio Unlocked' : 'Unlock Audit Studio'}
            </h3>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              {isUnlocked
                ? 'You have write permissions to run audits, upload datasets, and delete data.'
                : 'Enter the shared DIA password to upload datasets or launch audits.'}
            </p>
          </div>
        </div>

        {isUnlocked ? (
          <div className="space-y-4 pt-2">
            <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-xs text-emerald-800 dark:text-emerald-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>Full administrator access is currently active for this browser session.</span>
            </div>
            <button
              onClick={handleLock}
              className="w-full py-2.5 px-4 text-xs font-semibold rounded-xl bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-300 transition-colors border border-zinc-200 dark:border-zinc-700"
            >
              Lock Studio (Switch to Read-Only Demo)
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4 pt-2">
            <div>
              <label className="block text-xs font-medium text-zinc-700 dark:text-zinc-300 mb-1.5">
                Shared DIA Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-zinc-400 dark:text-zinc-500">
                  <KeyRound className="w-4 h-4" />
                </div>
                <input
                  type="password"
                  value={inputVal}
                  onChange={e => {
                    setInputVal(e.target.value);
                    if (error) setError(null);
                  }}
                  placeholder="Enter DIA password..."
                  className="w-full pl-9 pr-3 py-2 text-sm rounded-xl bg-zinc-50 dark:bg-zinc-950/80 border border-zinc-300 dark:border-zinc-700/80 text-zinc-900 dark:text-zinc-100 placeholder-zinc-400 dark:placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500"
                  autoFocus
                />
              </div>
              {error && (
                <div className="mt-1.5 flex items-center gap-1.5 text-xs text-rose-600 dark:text-rose-400">
                  <ShieldAlert className="w-3.5 h-3.5 shrink-0" />
                  <span>{error}</span>
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-2">
              <button
                type="button"
                onClick={() => setIsUnlockModalOpen(false)}
                className="flex-1 py-2 text-xs font-medium rounded-xl bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isVerifying}
                className="flex-1 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-950/60 transition-colors flex items-center justify-center gap-1.5 disabled:opacity-60"
              >
                {isVerifying ? (
                  <>
                    <RotateCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Verifying...</span>
                  </>
                ) : (
                  <span>Unlock Studio</span>
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
};
