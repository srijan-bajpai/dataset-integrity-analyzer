import React, { useState, useRef } from 'react';
import { useApp } from '../../lib/store';
import { api } from '../../lib/api';
import {
  UploadCloud,
  X,
  FileArchive,
  AlertCircle,
  RotateCw,
} from 'lucide-react';

export const UploadZipModal: React.FC = () => {
  const { isUploadOpen, setIsUploadOpen, refreshDatasets, refreshRuns, password } = useApp();

  const [file, setFile] = useState<File | null>(null);
  const [name, setName] = useState<string>('');
  const [samplingRate, setSamplingRate] = useState<number>(1.0);
  const [predictImpact, setPredictImpact] = useState<boolean>(true);
  const [estimateAttributes, setEstimateAttributes] = useState<boolean>(true);

  const [isUploading, setIsUploading] = useState<boolean>(false);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isUploadOpen) return null;

  const handleFileChange = (selectedFile: File | null) => {
    setError(null);
    if (!selectedFile) {
      setFile(null);
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith('.zip')) {
      setError('Please select a valid .ZIP archive containing image folders or manifest.');
      return;
    }
    // 200MB limit check
    if (selectedFile.size > 200 * 1024 * 1024) {
      setError('File exceeds maximum upload size of 200 MB.');
      return;
    }
    setFile(selectedFile);
    if (!name) {
      setName(selectedFile.name.replace(/\.[^/.]+$/, ''));
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileChange(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) {
      setError('Please select a ZIP file to upload.');
      return;
    }

    setIsUploading(true);
    setUploadProgress(20);
    setError(null);

    try {
      setUploadProgress(40);
      const dataset = await api.uploadDataset(file, name.trim() || undefined, password);
      setUploadProgress(70);

      // Immediately queue an audit run
      await api.createRun(
        dataset.id,
        {
          sampling_rate: samplingRate,
          predict_impact: predictImpact,
          estimate_attributes: estimateAttributes,
        },
        password
      );

      setUploadProgress(100);
      await refreshDatasets();
      await refreshRuns();

      setIsUploadOpen(false);
      setFile(null);
      setName('');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Upload failed');
    } finally {
      setIsUploading(false);
      setUploadProgress(0);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
      <div className="relative w-full max-w-lg rounded-2xl glass-panel border border-zinc-200 dark:border-zinc-700 bg-white dark:bg-zinc-900 shadow-2xl p-6 text-zinc-900 dark:text-zinc-100">
        <button
          onClick={() => setIsUploadOpen(false)}
          className="absolute top-4 right-4 p-1.5 rounded-xl text-zinc-400 hover:text-zinc-900 dark:hover:text-white hover:bg-zinc-100 dark:hover:bg-zinc-800 transition-colors"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="flex items-center gap-2.5 mb-4">
          <div className="p-2 rounded-xl bg-indigo-500/20 text-indigo-500 dark:text-indigo-400">
            <UploadCloud className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-base font-bold text-zinc-900 dark:text-white">Upload Dataset ZIP Archive</h3>
            <p className="text-xs text-zinc-600 dark:text-zinc-400">
              Drag-and-drop an image classification dataset (.zip) with folder-per-class or manifest layout.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Drag & Drop Zone */}
          <div
            onDragOver={e => e.preventDefault()}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-2xl p-6 text-center cursor-pointer transition-colors ${
              file
                ? 'border-emerald-500/50 bg-emerald-500/5'
                : 'border-zinc-300 dark:border-zinc-700 hover:border-indigo-500/60 bg-zinc-50 dark:bg-zinc-950/60'
            }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip"
              className="hidden"
              onChange={e => handleFileChange(e.target.files ? e.target.files[0] : null)}
            />

            {file ? (
              <div className="flex items-center justify-center gap-3 text-emerald-700 dark:text-emerald-300">
                <FileArchive className="w-8 h-8 text-emerald-600 dark:text-emerald-400" />
                <div className="text-left">
                  <div className="text-xs font-mono font-bold truncate max-w-xs">{file.name}</div>
                  <div className="text-[11px] text-zinc-500 dark:text-zinc-400">
                    {(file.size / (1024 * 1024)).toFixed(2)} MB • Ready to ingest
                  </div>
                </div>
              </div>
            ) : (
              <div>
                <UploadCloud className="w-10 h-10 text-zinc-400 dark:text-zinc-500 mx-auto mb-2" />
                <span className="text-xs font-semibold text-zinc-800 dark:text-zinc-200 block">
                  Click to browse or drop ZIP file here
                </span>
                <span className="text-[11px] text-zinc-500 mt-0.5 block">
                  Supports up to 200 MB archives
                </span>
              </div>
            )}
          </div>

          {/* Dataset Name */}
          <div>
            <label className="block text-xs font-mono font-medium text-zinc-600 dark:text-zinc-400 mb-1">
              Dataset Name
            </label>
            <input
              type="text"
              value={name}
              onChange={e => setName(e.target.value)}
              placeholder="e.g. Industrial-Defects-v2"
              className="w-full py-2 px-3 rounded-xl bg-zinc-50 dark:bg-zinc-950 border border-zinc-300 dark:border-zinc-700 text-xs font-mono text-zinc-900 dark:text-zinc-100 focus:outline-none focus:border-indigo-500"
            />
          </div>

          {/* Audit Options */}
          <div className="p-3.5 rounded-xl bg-zinc-100 dark:bg-zinc-950/60 border border-zinc-200 dark:border-zinc-800/80 space-y-3">
            <div className="flex items-center justify-between text-xs font-mono">
              <span className="text-zinc-700 dark:text-zinc-300">Sampling Rate</span>
              <span className="text-indigo-600 dark:text-indigo-400 font-bold">{(samplingRate * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.1"
              max="1.0"
              step="0.05"
              value={samplingRate}
              onChange={e => setSamplingRate(Number(e.target.value))}
              className="w-full accent-indigo-500 cursor-pointer"
            />

            <div className="flex items-center justify-between pt-1">
              <label className="text-xs text-zinc-700 dark:text-zinc-300 flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={predictImpact}
                  onChange={e => setPredictImpact(e.target.checked)}
                  className="rounded border-zinc-300 dark:border-zinc-700 text-indigo-600 focus:ring-0 accent-indigo-500"
                />
                <span>Predict Downstream Accuracy Impact (C2)</span>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <label className="text-xs text-zinc-700 dark:text-zinc-300 flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={estimateAttributes}
                  onChange={e => setEstimateAttributes(e.target.checked)}
                  className="rounded border-zinc-300 dark:border-zinc-700 text-indigo-600 focus:ring-0 accent-indigo-500"
                />
                <span>Infer Metadata & Demographic Attributes</span>
              </label>
            </div>
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-700 dark:text-rose-300">
              <AlertCircle className="w-4 h-4 shrink-0 text-rose-600 dark:text-rose-400" />
              <span>{error}</span>
            </div>
          )}

          {isUploading && (
            <div className="space-y-1">
              <div className="flex justify-between text-[11px] font-mono text-zinc-500 dark:text-zinc-400">
                <span>Ingesting & Unpacking...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-zinc-200 dark:bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-indigo-500 h-full rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex gap-2 pt-2">
            <button
              type="button"
              onClick={() => setIsUploadOpen(false)}
              disabled={isUploading}
              className="flex-1 py-2 text-xs font-medium rounded-xl bg-zinc-100 dark:bg-zinc-800 hover:bg-zinc-200 dark:hover:bg-zinc-700 text-zinc-700 dark:text-zinc-300 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isUploading || !file}
              className="flex-1 py-2 text-xs font-semibold rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-950/60 transition-colors flex items-center justify-center gap-1.5 disabled:opacity-50"
            >
              {isUploading ? (
                <>
                  <RotateCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Processing...</span>
                </>
              ) : (
                <span>Upload & Start Audit</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
