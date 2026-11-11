import React from 'react';
import { OperatingMode, RiskLevel } from '@/lib/types';
import { ShieldAlert, Activity, Cpu, HardDrive, Radio, AlertTriangle } from 'lucide-react';

interface HeaderProps {
  mode: OperatingMode;
  onModeChange: (mode: OperatingMode) => void;
  riskLevel: RiskLevel;
  serialConnected: boolean;
  wsConnected: boolean;
  currentTime: string;
}

export const Header: React.FC<HeaderProps> = ({
  mode,
  onModeChange,
  riskLevel,
  serialConnected,
  wsConnected,
  currentTime,
}) => {
  const getRiskBadge = () => {
    switch (riskLevel) {
      case 'CRITICAL':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded bg-red-950/80 border border-red-500 text-red-300 text-xs font-mono font-bold animate-pulse">
            <AlertTriangle className="w-3.5 h-3.5 text-red-400" />
            CRITICAL LEAKAGE
          </span>
        );
      case 'WARNING':
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded bg-amber-950/80 border border-amber-500 text-amber-300 text-xs font-mono font-bold">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
            ELEVATED RISK
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded bg-emerald-950/60 border border-emerald-600/50 text-emerald-300 text-xs font-mono">
            <Activity className="w-3.5 h-3.5 text-emerald-400" />
            SYSTEM NOMINAL
          </span>
        );
    }
  };

  return (
    <header className="border-b border-zinc-800 bg-zinc-950/90 backdrop-blur px-4 py-3 flex flex-wrap items-center justify-between gap-4 select-none">
      <div className="flex items-center gap-3">
        <div className="p-2 rounded bg-zinc-900 border border-zinc-700/60 text-amber-500">
          <ShieldAlert className="w-5 h-5" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-sm font-bold tracking-wider text-zinc-100 uppercase font-mono">
              Industrial Gas Monitoring & Ventilation SCADA
            </h1>
            <span className="text-[10px] bg-zinc-800 px-1.5 py-0.5 rounded text-zinc-400 font-mono">
              v1.0-EXP
            </span>
          </div>
          <p className="text-xs text-zinc-400 font-mono">
            ESP32 / MQ-2 / MQ-135 / DHT11 Prototype Telemetry
          </p>
        </div>
      </div>

      {/* Mode Switcher */}
      <div className="flex items-center gap-2 bg-zinc-900/90 border border-zinc-800 rounded p-1">
        <button
          onClick={() => onModeChange('LIVE_HARDWARE')}
          className={`px-3 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition-all ${
            mode === 'LIVE_HARDWARE'
              ? 'bg-amber-500/20 text-amber-400 border border-amber-500/50 font-semibold'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Cpu className="w-3.5 h-3.5" />
          LIVE HARDWARE
        </button>
        <button
          onClick={() => onModeChange('CSV_REPLAY')}
          className={`px-3 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition-all ${
            mode === 'CSV_REPLAY'
              ? 'bg-cyan-500/20 text-cyan-400 border border-cyan-500/50 font-semibold'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <HardDrive className="w-3.5 h-3.5" />
          CSV REPLAY
        </button>
        <button
          onClick={() => onModeChange('SYNTHETIC_SIMULATION')}
          className={`px-3 py-1 text-xs font-mono rounded flex items-center gap-1.5 transition-all ${
            mode === 'SYNTHETIC_SIMULATION'
              ? 'bg-purple-500/20 text-purple-400 border border-purple-500/50 font-semibold'
              : 'text-zinc-400 hover:text-zinc-200'
          }`}
        >
          <Radio className="w-3.5 h-3.5" />
          SYNTHETIC SIM
        </button>
      </div>

      {/* Status & Clock */}
      <div className="flex items-center gap-3">
        {getRiskBadge()}

        {/* Telemetry Indicator */}
        <div className="flex items-center gap-2 text-xs font-mono bg-zinc-900 border border-zinc-800 px-2.5 py-1 rounded">
          <span className="text-zinc-500">COM:</span>
          {serialConnected ? (
            <span className="flex items-center gap-1 text-emerald-400 font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping" />
              USB ACTIVE
            </span>
          ) : (
            <span className="text-zinc-500">DISCONNECTED</span>
          )}
        </div>

        <div className="text-xs font-mono text-zinc-400 bg-zinc-900 border border-zinc-800 px-2.5 py-1 rounded">
          {currentTime || '--:--:--'}
        </div>
      </div>
    </header>
  );
};
