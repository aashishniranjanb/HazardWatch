import React from 'react';
import { RiskEvaluation, ThresholdConfig, OperatingMode } from '@/lib/types';
import { ShieldAlert, AlertTriangle, CheckCircle, Fan, Power, Info } from 'lucide-react';

interface RiskAndVentilationProps {
  risk: RiskEvaluation;
  thresholds: ThresholdConfig;
  mode: OperatingMode;
  relayActive: boolean;
  pumpActive: boolean;
  onManualVentilationToggle?: () => void;
  ventilationMode: 'AUTO' | 'MANUAL';
  onVentilationModeToggle?: () => void;
}

export const RiskAndVentilation: React.FC<RiskAndVentilationProps> = ({
  risk,
  thresholds,
  mode,
  relayActive,
  pumpActive,
  onManualVentilationToggle,
  ventilationMode,
  onVentilationModeToggle,
}) => {
  const isVirtual = mode !== 'LIVE_HARDWARE';

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
      {/* Industrial Risk Monitor - 2 Cols */}
      <div className={`p-4 rounded-lg border backdrop-blur lg:col-span-2 flex flex-col justify-between transition-all ${
        risk.level === 'CRITICAL'
          ? 'bg-red-950/20 border-red-500/80'
          : risk.level === 'WARNING'
          ? 'bg-amber-950/20 border-amber-500/80'
          : 'bg-zinc-950/80 border-zinc-800'
      }`}>
        <div>
          <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
            <div className="flex items-center gap-2">
              <ShieldAlert className={`w-5 h-5 ${
                risk.level === 'CRITICAL' ? 'text-red-400 animate-pulse' :
                risk.level === 'WARNING' ? 'text-amber-400' : 'text-emerald-400'
              }`} />
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
                INDUSTRIAL RISK ASSESSMENT & THRESHOLD STATE
              </span>
            </div>
            <span className={`text-xs font-mono font-bold px-2 py-0.5 rounded border ${
              risk.level === 'CRITICAL' ? 'bg-red-900/60 border-red-500 text-red-200' :
              risk.level === 'WARNING' ? 'bg-amber-900/60 border-amber-500 text-amber-200' :
              'bg-emerald-950/60 border-emerald-600 text-emerald-300'
            }`}>
              {risk.level}
            </span>
          </div>

          {/* Active Alerts */}
          <div className="mt-3 space-y-1.5">
            {risk.activeAlerts.length > 0 ? (
              risk.activeAlerts.map((alert, idx) => (
                <div key={idx} className="flex items-start gap-2 text-xs font-mono text-red-300 bg-red-950/40 p-2 rounded border border-red-900/50">
                  <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
                  <span>{alert}</span>
                </div>
              ))
            ) : (
              <div className="flex items-center gap-2 text-xs font-mono text-emerald-400/90 bg-emerald-950/20 p-2 rounded border border-emerald-900/30">
                <CheckCircle className="w-4 h-4 text-emerald-500 shrink-0" />
                <span>Atmosphere normal. All gas levels below configured alert boundaries.</span>
              </div>
            )}
          </div>

          {/* Alert Root Cause Explanation */}
          <div className="mt-3 text-xs font-mono text-zinc-400 bg-zinc-900/70 p-2.5 rounded border border-zinc-800/80">
            <div className="text-[10px] text-zinc-500 uppercase font-semibold mb-1">Diagnosis / Assessment</div>
            <ul className="list-disc list-inside space-y-0.5">
              {risk.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          </div>
        </div>

        <div className="mt-4 pt-2 border-t border-zinc-900 flex flex-wrap items-center justify-between text-[11px] font-mono text-zinc-500">
          <span>Hysteresis Buffer: <span className="text-zinc-300">{thresholds.hysteresis_adc} ADC</span></span>
          <span>Sustained Duration: <span className="text-zinc-300">{thresholds.sustained_duration_ms}ms</span></span>
          <span className="text-zinc-600">*Prototype safety thresholds, non-certified.</span>
        </div>
      </div>

      {/* Ventilation & Relay Control Status - 1 Col */}
      <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur flex flex-col justify-between">
        <div>
          <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
            <div className="flex items-center gap-2">
              <Fan className={`w-5 h-5 ${pumpActive ? 'text-cyan-400 animate-spin' : 'text-zinc-500'}`} />
              <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
                VENTILATION SYSTEM
              </span>
            </div>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${
              isVirtual
                ? 'bg-purple-950/60 border-purple-700 text-purple-300'
                : 'bg-emerald-950/60 border-emerald-700 text-emerald-300'
            }`}>
              {isVirtual ? 'VIRTUAL ACTUATION' : 'PHYSICAL HARDWARE'}
            </span>
          </div>

          {/* Relay & Pump Status */}
          <div className="grid grid-cols-2 gap-2 mt-3">
            <div className={`p-3 rounded border text-center transition-all ${
              relayActive
                ? 'bg-amber-950/40 border-amber-500 text-amber-200'
                : 'bg-zinc-900 border-zinc-800 text-zinc-500'
            }`}>
              <div className="text-[10px] font-mono text-zinc-400">RELAY COIL</div>
              <div className="text-lg font-mono font-bold mt-1">
                {relayActive ? 'CLOSED (ON)' : 'OPEN (OFF)'}
              </div>
            </div>

            <div className={`p-3 rounded border text-center transition-all ${
              pumpActive
                ? 'bg-cyan-950/40 border-cyan-500 text-cyan-200 shadow-md shadow-cyan-950/50'
                : 'bg-zinc-900 border-zinc-800 text-zinc-500'
            }`}>
              <div className="text-[10px] font-mono text-zinc-400">AIR PUMP</div>
              <div className="text-lg font-mono font-bold mt-1 flex items-center justify-center gap-1">
                {pumpActive ? 'EXTRACTING' : 'IDLE'}
              </div>
            </div>
          </div>

          {/* Mode Switch and Controls */}
          <div className="mt-3 flex items-center justify-between p-2 rounded bg-zinc-900 border border-zinc-800 text-xs font-mono">
            <span className="text-zinc-400">Control Mode:</span>
            <button
              onClick={onVentilationModeToggle}
              className="px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 border border-zinc-700 font-bold transition-colors"
            >
              {ventilationMode === 'AUTO' ? 'AUTOMATIC (Threshold Driven)' : 'MANUAL OVERRIDE'}
            </button>
          </div>

          {isVirtual && (
            <div className="mt-2 flex items-start gap-1.5 p-2 rounded bg-purple-950/20 border border-purple-900/40 text-[10px] font-mono text-purple-300">
              <Info className="w-3.5 h-3.5 shrink-0 mt-0.5 text-purple-400" />
              <span>In replay/simulation mode, relay and pump are simulated purely in software.</span>
            </div>
          )}
        </div>

        <div className="mt-3 pt-2 border-t border-zinc-900 text-right">
          <button
            onClick={onManualVentilationToggle}
            disabled={ventilationMode === 'AUTO' || mode === 'LIVE_HARDWARE'}
            className={`w-full py-2 px-3 rounded text-xs font-mono font-bold flex items-center justify-center gap-2 border transition-all ${
              ventilationMode === 'AUTO' || mode === 'LIVE_HARDWARE'
                ? 'opacity-40 cursor-not-allowed bg-zinc-900 border-zinc-800 text-zinc-500'
                : pumpActive
                ? 'bg-red-950/70 hover:bg-red-900 border-red-600 text-red-200'
                : 'bg-emerald-950/70 hover:bg-emerald-900 border-emerald-600 text-emerald-200'
            }`}
          >
            <Power className="w-3.5 h-3.5" />
            {pumpActive ? 'FORCE SHUTDOWN PUMP' : 'FORCE ENGAGE VENTILATION'}
          </button>
        </div>
      </div>
    </div>
  );
};
