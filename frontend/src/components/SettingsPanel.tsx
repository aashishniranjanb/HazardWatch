'use client';

import React from 'react';
import { ThresholdConfig } from '@/lib/types';
import { Sliders, Save, RotateCcw } from 'lucide-react';
import { DEFAULT_THRESHOLDS } from '@/lib/risk-engine';

interface SettingsPanelProps {
  thresholds: ThresholdConfig;
  onUpdate: (updated: ThresholdConfig) => void;
}

export const SettingsPanel: React.FC<SettingsPanelProps> = ({ thresholds, onUpdate }) => {
  const [local, setLocal] = React.useState<ThresholdConfig>(thresholds);
  const [savedMsg, setSavedMsg] = React.useState(false);

  const handleChange = (key: keyof ThresholdConfig, val: number) => {
    setLocal(prev => ({ ...prev, [key]: val }));
  };

  const handleSave = () => {
    onUpdate(local);
    setSavedMsg(true);
    setTimeout(() => setSavedMsg(false), 2000);
  };

  const handleReset = () => {
    setLocal(DEFAULT_THRESHOLDS);
    onUpdate(DEFAULT_THRESHOLDS);
  };

  return (
    <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur space-y-4">
      <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
            SCADA Configurable Safety Thresholds & Hysteresis
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleReset}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-mono text-zinc-400 flex items-center gap-1"
          >
            <RotateCcw className="w-3 h-3" /> Reset Defaults
          </button>
          <button
            onClick={handleSave}
            className="px-3 py-1 rounded bg-cyan-600 hover:bg-cyan-500 text-zinc-950 font-mono text-xs font-bold flex items-center gap-1"
          >
            <Save className="w-3 h-3" /> Save Changes
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 text-xs font-mono">
        <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800">
          <label className="text-zinc-400 block mb-1">MQ-2 Warning Threshold (ADC)</label>
          <input
            type="number"
            value={local.mq2_warning_adc}
            onChange={(e) => handleChange('mq2_warning_adc', Number(e.target.value))}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-zinc-200"
          />
        </div>

        <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800">
          <label className="text-zinc-400 block mb-1">MQ-2 Critical Threshold (ADC)</label>
          <input
            type="number"
            value={local.mq2_critical_adc}
            onChange={(e) => handleChange('mq2_critical_adc', Number(e.target.value))}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-zinc-200"
          />
        </div>

        <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800">
          <label className="text-zinc-400 block mb-1">MQ-135 Warning Threshold (ADC)</label>
          <input
            type="number"
            value={local.mq135_warning_adc}
            onChange={(e) => handleChange('mq135_warning_adc', Number(e.target.value))}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-zinc-200"
          />
        </div>

        <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800">
          <label className="text-zinc-400 block mb-1">MQ-135 Critical Threshold (ADC)</label>
          <input
            type="number"
            value={local.mq135_critical_adc}
            onChange={(e) => handleChange('mq135_critical_adc', Number(e.target.value))}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-zinc-200"
          />
        </div>

        <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800">
          <label className="text-zinc-400 block mb-1">Hysteresis Buffer (ADC)</label>
          <input
            type="number"
            value={local.hysteresis_adc}
            onChange={(e) => handleChange('hysteresis_adc', Number(e.target.value))}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-zinc-200"
          />
          <span className="text-[10px] text-zinc-500 mt-1 block">Prevents relay chatter at boundaries</span>
        </div>

        <div className="p-2.5 rounded bg-zinc-900/60 border border-zinc-800">
          <label className="text-zinc-400 block mb-1">Sustained Duration (ms)</label>
          <input
            type="number"
            value={local.sustained_duration_ms}
            onChange={(e) => handleChange('sustained_duration_ms', Number(e.target.value))}
            className="w-full bg-zinc-950 border border-zinc-700 rounded px-2 py-1 text-zinc-200"
          />
          <span className="text-[10px] text-zinc-500 mt-1 block">Minimum hold time for filter stability</span>
        </div>
      </div>

      {savedMsg && (
        <div className="text-xs font-mono text-emerald-400 text-right animate-pulse">
          ✓ Parameters updated successfully.
        </div>
      )}
    </div>
  );
};
