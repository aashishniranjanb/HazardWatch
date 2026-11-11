'use client';

import React, { useState, useEffect } from 'react';
import { parseCSVDataset } from '@/lib/csv';
import { DatasetSummary, NormalizedSensorReading } from '@/lib/types';
import { FileSpreadsheet, Upload, Play, Pause, Square, FastForward, CheckCircle, AlertTriangle, Info } from 'lucide-react';

interface DatasetManagerProps {
  onDatasetLoaded: (summary: DatasetSummary, readings: NormalizedSensorReading[]) => void;
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
  onSpeedChange: (speed: number) => void;
  onSeek: (index: number) => void;
  isPlaying: boolean;
  currentIndex: number;
  totalRecords: number;
  speed: number;
  currentSummary: DatasetSummary | null;
}

export const DatasetManager: React.FC<DatasetManagerProps> = ({
  onDatasetLoaded,
  onPlay,
  onPause,
  onStop,
  onSpeedChange,
  onSeek,
  isPlaying,
  currentIndex,
  totalRecords,
  speed,
  currentSummary,
}) => {
  const [selectedPreset, setSelectedPreset] = useState<string>('multi_sensor_data.csv');
  const [loading, setLoading] = useState<boolean>(false);
  const [errorReport, setErrorReport] = useState<string[]>([]);

  const defaultDatasets = [
    { id: 'multi_sensor_data.csv', name: 'Multi-Sensor Labeled Dataset (812 rows, Labels 0-4)' },
    { id: 'multi_sensor_data_baseline.csv', name: 'Baseline Stability Dataset (12,175 rows, Label 0)' },
    { id: 'mq2_data.csv', name: 'MQ-2 High-Resolution Dataset (16,040 rows, with malformed test cases)' },
  ];

  const loadPreset = async (filename: string) => {
    try {
      setLoading(true);
      setErrorReport([]);
      const res = await fetch(`/datasets/${filename}`);
      if (!res.ok) throw new Error(`Failed to load dataset: ${res.statusText}`);
      const text = await res.text();
      const result = parseCSVDataset(text, filename);
      setErrorReport(result.errors);
      onDatasetLoaded(result.summary, result.readings);
    } catch (err: any) {
      setErrorReport([`Load error: ${err.message}`]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial auto-load of default primary dataset
    loadPreset('multi_sensor_data.csv');
  }, []);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setErrorReport([]);
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target?.result as string;
      const result = parseCSVDataset(text, file.name, `Custom: ${file.name}`);
      setErrorReport(result.errors);
      onDatasetLoaded(result.summary, result.readings);
      setLoading(false);
    };
    reader.onerror = () => {
      setErrorReport(['Failed to read local file']);
      setLoading(false);
    };
    reader.readAsText(file);
  };

  const progressPercent = totalRecords > 0 ? ((currentIndex / totalRecords) * 100).toFixed(1) : 0;

  return (
    <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur space-y-4">
      {/* Title */}
      <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <FileSpreadsheet className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
            Historical CSV Dataset Ingestion & Replay Engine
          </span>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
          PARSER: PAPAPARSE
        </span>
      </div>

      {/* Dataset Selection Toolbar */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        <div className="md:col-span-2 flex flex-wrap items-center gap-2">
          <select
            value={selectedPreset}
            onChange={(e) => {
              setSelectedPreset(e.target.value);
              loadPreset(e.target.value);
            }}
            className="flex-1 bg-zinc-900 border border-zinc-700 rounded px-2.5 py-1.5 text-xs text-zinc-200 font-mono"
          >
            {defaultDatasets.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>

          <label className="cursor-pointer px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-mono text-zinc-300 flex items-center gap-1.5">
            <Upload className="w-3.5 h-3.5 text-cyan-400" />
            <span>Upload Custom CSV</span>
            <input type="file" accept=".csv" onChange={handleFileUpload} className="hidden" />
          </label>
        </div>

        {/* Status / Loading */}
        <div className="flex items-center justify-end text-xs font-mono text-zinc-400">
          {loading ? (
            <span className="text-amber-400 animate-pulse">Parsing CSV records...</span>
          ) : currentSummary ? (
            <span className="flex items-center gap-1.5 text-emerald-400">
              <CheckCircle className="w-3.5 h-3.5" />
              {currentSummary.validRows} valid rows loaded
            </span>
          ) : (
            'No dataset active'
          )}
        </div>
      </div>

      {/* Metadata & Data Integrity Report Banner */}
      {currentSummary && (
        <div className="bg-zinc-900/60 border border-zinc-800/80 rounded p-3 text-xs font-mono grid grid-cols-2 md:grid-cols-4 gap-2">
          <div>
            <span className="text-zinc-500 block text-[10px]">TOTAL / SKIPPED ROWS</span>
            <span className="text-zinc-200 font-bold">{currentSummary.totalRows}</span>
            <span className="text-zinc-500"> / </span>
            <span className={currentSummary.skippedRows > 0 ? 'text-amber-400 font-bold' : 'text-zinc-400'}>
              {currentSummary.skippedRows} skipped
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px]">HARDWARE MISMATCH CHANNELS</span>
            <span className="text-zinc-300">
              MQ-7: <b className="text-purple-400">{currentSummary.hasMQ7 ? 'PRESENT (Replay only)' : 'NONE'}</b>
            </span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px]">DHT11 CLIMATIC DATA</span>
            <span className="text-zinc-400 font-bold">UNAVAILABLE (NOT IN DATASET)</span>
          </div>
          <div>
            <span className="text-zinc-500 block text-[10px]">DATASET LABELS</span>
            <span className="text-zinc-300 font-bold">
              {currentSummary.uniqueLabels.length > 0 ? currentSummary.uniqueLabels.join(', ') : 'None'}
            </span>
          </div>
        </div>
      )}

      {/* Validation / Skipped Row Warning */}
      {errorReport.length > 0 && (
        <div className="p-2 rounded bg-amber-950/20 border border-amber-900/50 text-[11px] font-mono text-amber-300 space-y-1">
          <div className="flex items-center gap-1 font-bold">
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>Malformed Row Handling Report ({errorReport.length} warnings reported):</span>
          </div>
          <div className="max-h-16 overflow-y-auto space-y-0.5 text-zinc-400">
            {errorReport.slice(0, 5).map((e, i) => (
              <div key={i}>• {e}</div>
            ))}
          </div>
        </div>
      )}

      {/* Replay Controls & Timeline Scrubber */}
      <div className="space-y-2 pt-2 border-t border-zinc-900">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            {!isPlaying ? (
              <button
                onClick={onPlay}
                disabled={totalRecords === 0}
                className="px-4 py-1.5 rounded bg-cyan-600 hover:bg-cyan-500 text-zinc-950 font-mono text-xs font-bold flex items-center gap-1.5 disabled:opacity-40"
              >
                <Play className="w-3.5 h-3.5 fill-current" />
                PLAY REPLAY
              </button>
            ) : (
              <button
                onClick={onPause}
                className="px-4 py-1.5 rounded bg-amber-600 hover:bg-amber-500 text-zinc-950 font-mono text-xs font-bold flex items-center gap-1.5"
              >
                <Pause className="w-3.5 h-3.5 fill-current" />
                PAUSE
              </button>
            )}

            <button
              onClick={onStop}
              disabled={totalRecords === 0}
              className="px-3 py-1.5 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-zinc-300 font-mono text-xs flex items-center gap-1.5 disabled:opacity-40"
            >
              <Square className="w-3.5 h-3.5 fill-current" />
              STOP / RESTART
            </button>
          </div>

          {/* Speed Selector */}
          <div className="flex items-center gap-1 text-xs font-mono">
            <span className="text-zinc-400 mr-1 flex items-center gap-1">
              <FastForward className="w-3.5 h-3.5 text-cyan-400" /> Speed:
            </span>
            {[0.5, 1, 2, 5, 10, 20].map((s) => (
              <button
                key={s}
                onClick={() => onSpeedChange(s)}
                className={`px-2 py-0.5 rounded border transition-colors ${
                  speed === s
                    ? 'bg-cyan-600/30 border-cyan-500 text-cyan-300 font-bold'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {s}x
              </button>
            ))}
          </div>

          <div className="text-xs font-mono text-zinc-400">
            Row: <span className="text-zinc-200 font-bold">{currentIndex}</span> / {totalRecords} ({progressPercent}%)
          </div>
        </div>

        {/* Timeline Slider */}
        <input
          type="range"
          min={0}
          max={Math.max(0, totalRecords - 1)}
          value={currentIndex}
          onChange={(e) => onSeek(Number(e.target.value))}
          disabled={totalRecords === 0}
          className="w-full h-1.5 bg-zinc-800 rounded-lg appearance-none cursor-pointer accent-cyan-500 disabled:opacity-30"
        />
      </div>
    </div>
  );
};
