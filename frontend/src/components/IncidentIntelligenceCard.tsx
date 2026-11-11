import React from 'react';
import { AlertCircle, CheckCircle, ShieldAlert, Wrench, Flame, Wind, HelpCircle } from 'lucide-react';

export interface IndustrialIncident {
  event_id: string;
  timestamp: number;
  operating_mode: string;
  zone_id: string;
  zone_name: string;
  sensor_state: string;
  severity: 'NORMAL' | 'ADVISORY' | 'WARNING' | 'CRITICAL' | 'SENSOR_FAULT' | 'UNKNOWN';
  trend: 'STABLE' | 'RISING' | 'FALLING' | 'UNKNOWN';
  pattern: string;
  industrial_context: string;
  evidence: string[];
  gas_identity: string;
  ml_confidence: number | null;
  recommended_action: string;
  incident_state: 'UNVERIFIED' | 'RESOLVED';
  relay_command: string;
  verification_steps: string[];
  emergency_procedure: string;
}

interface IncidentIntelligenceCardProps {
  incident: IndustrialIncident;
  onAcknowledge?: () => void;
  onResolve?: () => void;
}

export const IncidentIntelligenceCard: React.FC<IncidentIntelligenceCardProps> = ({
  incident,
  onAcknowledge,
  onResolve,
}) => {
  const isEmergency = incident.severity === 'CRITICAL' || incident.severity === 'SENSOR_FAULT';
  const isWarning = incident.severity === 'WARNING';

  return (
    <div className={`p-4 rounded-lg border backdrop-blur transition-all ${
      isEmergency
        ? 'bg-red-950/20 border-red-500 shadow-lg shadow-red-950/40'
        : isWarning
        ? 'bg-amber-950/20 border-amber-500 shadow-md shadow-amber-950/20'
        : 'bg-zinc-950/80 border-zinc-800'
    }`}>
      {/* Top Banner */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-2.5 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <ShieldAlert className={`w-5 h-5 ${
            isEmergency ? 'text-red-400 animate-pulse' : isWarning ? 'text-amber-400' : 'text-emerald-400'
          }`} />
          <div>
            <div className="text-xs font-mono font-bold uppercase text-zinc-100 flex items-center gap-2">
              <span>{incident.industrial_context.replace(/_/g, ' ')}</span>
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
                {incident.zone_id}
              </span>
            </div>
            <div className="text-[10px] font-mono text-zinc-500">
              Zone: {incident.zone_name} • Event ID: {incident.event_id}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className={`text-xs font-mono font-bold px-2.5 py-0.5 rounded border ${
            isEmergency ? 'bg-red-950/80 border-red-500 text-red-200' :
            isWarning ? 'bg-amber-950/80 border-amber-500 text-amber-200' :
            'bg-emerald-950/60 border-emerald-600 text-emerald-300'
          }`}>
            {incident.severity}
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-zinc-400">
            TREND: <b className={incident.trend === 'RISING' ? 'text-red-400' : 'text-zinc-200'}>{incident.trend}</b>
          </span>
        </div>
      </div>

      {/* Grid of Intelligence Details */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-3 text-xs font-mono">
        {/* ML Pattern & Gas Identity Status */}
        <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800">
          <span className="text-[10px] text-zinc-500 uppercase block font-semibold">Sensor Response Pattern</span>
          <div className="text-sm font-bold text-zinc-100 mt-1 flex items-center gap-1.5">
            {incident.pattern === 'SMOKE' && <Flame className="w-4 h-4 text-amber-500" />}
            {incident.pattern === 'VOC_RESPONSE' && <Wind className="w-4 h-4 text-cyan-400" />}
            <span>{incident.pattern}</span>
          </div>
          <div className="text-[11px] text-zinc-400 mt-1">
            Chemical Identity: <span className="text-amber-400 font-semibold">{incident.gas_identity}</span>
          </div>
          <div className="text-[10px] text-zinc-500 mt-1">
            Confidence: {incident.ml_confidence !== null ? `${(incident.ml_confidence * 100).toFixed(1)}% (Calibrated)` : 'Screening pattern'}
          </div>
        </div>

        {/* Evidence & Mathematical Observations */}
        <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800">
          <span className="text-[10px] text-zinc-500 uppercase block font-semibold">Supporting Evidence</span>
          <ul className="mt-1 space-y-0.5 text-[11px] text-zinc-300 list-disc list-inside">
            {incident.evidence.map((ev, i) => (
              <li key={i}>{ev.replace(/_/g, ' ')}</li>
            ))}
          </ul>
        </div>

        {/* Actionable Operator Procedure */}
        <div className="p-3 rounded bg-zinc-900/60 border border-zinc-800 flex flex-col justify-between">
          <div>
            <span className="text-[10px] text-zinc-500 uppercase block font-semibold">Recommended Procedure</span>
            <div className="text-[11px] font-bold text-amber-300 mt-1">
              {incident.recommended_action.replace(/_/g, ' ')}
            </div>
            {incident.verification_steps.length > 0 && (
              <div className="text-[10px] text-zinc-400 mt-1">
                Step 1: {incident.verification_steps[0]}
              </div>
            )}
          </div>

          <div className="mt-2 pt-2 border-t border-zinc-800 flex items-center justify-between text-[10px]">
            <span className="text-zinc-500">Relay Command: <b className="text-zinc-200">{incident.relay_command}</b></span>
            <span className="text-zinc-500">Incident State: <b className="text-zinc-300">{incident.incident_state}</b></span>
          </div>
        </div>
      </div>
    </div>
  );
};
