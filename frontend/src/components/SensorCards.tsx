import React from 'react';
import { NormalizedSensorReading, RiskEvaluation, ThresholdConfig, OperatingMode, UnifiedSensorsMap, UnifiedSensorRecord, SensorAvailabilityState } from '@/lib/types';
import { Flame, Wind, Thermometer, Activity, AlertTriangle, CheckCircle, Clock, Bookmark, HelpCircle } from 'lucide-react';

export type SystemMonitoringState = 
  | 'DISCONNECTED'
  | 'INITIALIZING'
  | 'BASELINE_MODE'
  | 'LIVE_MONITORING'
  | 'SENSOR_FAULT'
  | 'INSUFFICIENT_DATA';

interface SensorCardsProps {
  reading: NormalizedSensorReading | null;
  risk: RiskEvaluation;
  thresholds: ThresholdConfig;
  mode: OperatingMode;
  systemState?: SystemMonitoringState;
  hasHardwareBaseline?: boolean;
  unifiedSensors?: UnifiedSensorsMap | null;
}

const renderAvailabilityBadge = (availability: SensorAvailabilityState, calibrationStatus?: string) => {
  switch (availability) {
    case 'LIVE':
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 border border-emerald-600/80 text-emerald-300 font-bold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          LIVE
        </span>
      );
    case 'LAST_KNOWN':
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-amber-950/80 border border-amber-600/80 text-amber-300 font-bold">
          <Clock className="w-2.5 h-2.5 text-amber-400" />
          LAST-KNOWN
        </span>
      );
    case 'REFERENCE':
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-950/80 border border-cyan-500/80 text-cyan-300 font-bold border-dashed">
          <Bookmark className="w-2.5 h-2.5 text-cyan-400" />
          REFERENCE BASELINE
        </span>
      );
    case 'FAULT':
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-red-950/90 border border-red-500 text-red-300 font-bold">
          <AlertTriangle className="w-2.5 h-2.5 text-red-400" />
          SENSOR FAULT
        </span>
      );
    case 'UNAVAILABLE':
    default:
      return (
        <span className="flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded bg-zinc-900 border border-zinc-700 text-zinc-400 font-bold">
          <HelpCircle className="w-2.5 h-2.5 text-zinc-500" />
          UNAVAILABLE
        </span>
      );
  }
};

const renderCalibrationBadge = (status?: string) => {
  if (!status) return null;
  const isUncalibrated = status === 'NOT_CALIBRATED';
  const isMeasured = status === 'MEASURED_CALIBRATION';
  return (
    <span className={`text-[9px] font-mono px-1.5 py-0.2 rounded border ${
      isUncalibrated
        ? 'bg-amber-950/40 border-amber-700/60 text-amber-300'
        : isMeasured
        ? 'bg-emerald-950/40 border-emerald-700/60 text-emerald-300'
        : 'bg-zinc-900 border-zinc-800 text-zinc-400'
    }`}>
      {isUncalibrated ? 'NOT CALIBRATED' : status.replace('_', ' ')}
    </span>
  );
};

export const SensorCards: React.FC<SensorCardsProps> = ({
  reading,
  thresholds,
  mode,
  systemState = 'LIVE_MONITORING',
  hasHardwareBaseline = false,
  unifiedSensors = null,
}) => {
  // Read from unifiedSensors or construct fallback from reading
  const mq2Record: Partial<UnifiedSensorRecord> = unifiedSensors?.mq2 || {
    sensor_id: 'mq2',
    sensor_name: 'MQ-2 Combustible/Smoke',
    gpio_pin: 34,
    live_value: reading?.mq2_adc ?? null,
    reference_value: 338,
    reference_source: 'M2.7 Factory Benchmark',
    availability: reading?.mq2_adc !== null && reading?.mq2_adc !== undefined ? 'LIVE' : (mode === 'LIVE_HARDWARE' ? 'FAULT' : 'REFERENCE'),
    calibration_status: 'CALIBRATED_BENCHMARK',
    unit: 'ADC'
  };

  const mq135Record: Partial<UnifiedSensorRecord> = unifiedSensors?.mq135 || {
    sensor_id: 'mq135',
    sensor_name: 'MQ-135 Hazardous/Air Quality',
    gpio_pin: 35,
    live_value: reading?.mq135_adc ?? null,
    reference_value: 1523,
    reference_source: 'M2.7 Factory Benchmark',
    availability: reading?.mq135_adc !== null && reading?.mq135_adc !== undefined ? 'LIVE' : (mode === 'LIVE_HARDWARE' ? 'FAULT' : 'REFERENCE'),
    calibration_status: 'NOT_CALIBRATED',
    unit: 'ADC'
  };

  const tempRecord: Partial<UnifiedSensorRecord> = unifiedSensors?.temperature || {
    sensor_id: 'temperature',
    sensor_name: 'DHT11 Ambient Temperature',
    gpio_pin: 4,
    live_value: reading?.temperature ?? null,
    reference_value: 25.0,
    reference_source: 'Standard Industrial Ambient',
    availability: reading?.temperature !== null && reading?.temperature !== undefined ? 'LIVE' : (mode === 'LIVE_HARDWARE' ? 'FAULT' : 'REFERENCE'),
    calibration_status: 'FACTORY_NOMINAL',
    unit: '°C'
  };

  const humRecord: Partial<UnifiedSensorRecord> = unifiedSensors?.humidity || {
    sensor_id: 'humidity',
    sensor_name: 'DHT11 Relative Humidity',
    gpio_pin: 4,
    live_value: reading?.humidity ?? null,
    reference_value: 50.0,
    reference_source: 'Standard Industrial Ambient',
    availability: reading?.humidity !== null && reading?.humidity !== undefined ? 'LIVE' : (mode === 'LIVE_HARDWARE' ? 'FAULT' : 'REFERENCE'),
    calibration_status: 'FACTORY_NOMINAL',
    unit: '%RH'
  };

  const isMQ2Warn = mq2Record.live_value !== null && mq2Record.live_value !== undefined && mq2Record.live_value >= thresholds.mq2_warning_adc;
  const isMQ2Crit = mq2Record.live_value !== null && mq2Record.live_value !== undefined && mq2Record.live_value >= thresholds.mq2_critical_adc;

  const isMQ135Warn = mq135Record.live_value !== null && mq135Record.live_value !== undefined && mq135Record.live_value >= thresholds.mq135_warning_adc;
  const isMQ135Crit = mq135Record.live_value !== null && mq135Record.live_value !== undefined && mq135Record.live_value >= thresholds.mq135_critical_adc;

  const isAnyFault = mq135Record.availability === 'FAULT' || tempRecord.availability === 'FAULT' || systemState === 'SENSOR_FAULT' || Boolean(reading?.fault);

  return (
    <div className="space-y-2">
      {/* State banner if in baseline or fault mode */}
      {isAnyFault && (
        <div className="p-3 rounded-lg bg-red-950/80 border border-red-500 flex flex-wrap items-center justify-between gap-2 text-xs font-mono text-red-200">
          <div className="flex items-center gap-2 min-w-0">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0" />
            <span className="font-bold tracking-wide">SENSOR HARDWARE DISCONNECT / FAULT:</span>
            <span className="truncate">MQ-135 (GPIO35) and DHT11 (GPIO4) missing physical connection. Real-world readings remain null. Reference baselines displayed below for context only.</span>
          </div>
          <span className="text-[10px] bg-red-900 px-2.5 py-1 rounded border border-red-700 whitespace-nowrap font-bold shrink-0">
            VENTILATION INTERLOCK SAFE-OFF
          </span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* MQ-2 Card */}
        <div className={`p-4 rounded-lg border bg-zinc-950/80 backdrop-blur transition-all ${
          isMQ2Crit
            ? 'border-red-500 shadow-lg shadow-red-950/50'
            : isMQ2Warn
            ? 'border-amber-500 shadow-md shadow-amber-950/30'
            : mq2Record.availability === 'LIVE'
            ? 'border-emerald-800/80 shadow-sm shadow-emerald-950/30'
            : 'border-zinc-800'
        }`}>
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <div className="flex items-center gap-1.5 text-xs font-mono font-medium">
              <Flame className="w-4 h-4 text-amber-500" />
              <span>MQ-2 (Combustible/Smoke)</span>
            </div>
            {renderAvailabilityBadge(mq2Record.availability || 'UNAVAILABLE', mq2Record.calibration_status)}
          </div>

          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-500">BASELINE REF</span>
                {renderCalibrationBadge(mq2Record.calibration_status)}
              </div>
              <div className="text-xl font-mono font-bold text-cyan-300 mt-1">
                {mq2Record.reference_value ?? '--'} <span className="text-[10px] font-normal text-zinc-500">{mq2Record.unit}</span>
              </div>
              <span className="text-[9px] font-mono text-zinc-500 block truncate mt-0.5">{mq2Record.reference_source || 'Benchmark'}</span>
            </div>

            <div className={`p-2 rounded border ${
              mq2Record.availability === 'LIVE' ? 'bg-emerald-950/20 border-emerald-800/60' : 'bg-zinc-900/60 border-zinc-800'
            }`}>
              <span className="text-[10px] font-mono text-zinc-500 block">LIVE READING (GPIO{mq2Record.gpio_pin})</span>
              <div className="text-xl font-mono font-bold text-zinc-100 mt-1">
                {mq2Record.live_value !== null && mq2Record.live_value !== undefined ? (
                  <>
                    {mq2Record.live_value} <span className="text-[10px] font-normal text-zinc-500">{mq2Record.unit}</span>
                  </>
                ) : (
                  <span className="text-zinc-500 text-sm font-semibold">--</span>
                )}
              </div>
              <span className="text-[9px] font-mono text-emerald-400 block mt-0.5">
                {mq2Record.availability === 'LIVE' ? 'Physical Stream Active' : 'No Live Value'}
              </span>
            </div>
          </div>

          {/* Deviation & Secondary Metrics */}
          <div className="mt-3 pt-2 border-t border-zinc-900 flex items-center justify-between text-[11px] font-mono">
            <span className="text-zinc-500">Live vs Baseline:</span>
            {mq2Record.live_value !== null && mq2Record.live_value !== undefined && mq2Record.reference_value !== null && mq2Record.reference_value !== undefined ? (
              <span className={`font-bold ${(mq2Record.live_value - mq2Record.reference_value) > 0 ? 'text-amber-400' : 'text-emerald-400'}`}>
                {(mq2Record.live_value - mq2Record.reference_value) >= 0 ? `+${(mq2Record.live_value - mq2Record.reference_value).toFixed(0)}` : (mq2Record.live_value - mq2Record.reference_value).toFixed(0)} ADC
              </span>
            ) : (
              <span className="text-zinc-600">-- (No Math on Unconnected)</span>
            )}
          </div>
        </div>

        {/* MQ-135 Card */}
        <div className={`p-4 rounded-lg border bg-zinc-950/80 backdrop-blur transition-all ${
          mq135Record.availability === 'FAULT'
            ? 'border-red-900/80 bg-red-950/10'
            : 'border-zinc-800'
        }`}>
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <div className="flex items-center gap-1.5 text-xs font-mono font-medium">
              <Wind className="w-4 h-4 text-cyan-400" />
              <span>MQ-135 (Hazardous/Air Quality)</span>
            </div>
            {renderAvailabilityBadge(mq135Record.availability || 'FAULT', mq135Record.calibration_status)}
          </div>

          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="p-2 rounded bg-zinc-900/60 border border-cyan-900/50">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono text-zinc-400">REFERENCE REF</span>
                {renderCalibrationBadge(mq135Record.calibration_status)}
              </div>
              <div className="text-xl font-mono font-bold text-cyan-300 mt-1">
                {mq135Record.reference_value ?? '--'} <span className="text-[10px] font-normal text-zinc-500">{mq135Record.unit}</span>
              </div>
              <span className="text-[9px] font-mono text-cyan-500 block truncate mt-0.5">{mq135Record.reference_source || 'Benchmark'}</span>
            </div>

            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <span className="text-[10px] font-mono text-zinc-500 block">LIVE READING (GPIO{mq135Record.gpio_pin})</span>
              <div className="text-xl font-mono font-bold text-zinc-500 mt-1">
                {mq135Record.live_value !== null && mq135Record.live_value !== undefined ? (
                  <>
                    {mq135Record.live_value} <span className="text-[10px] font-normal text-zinc-500">{mq135Record.unit}</span>
                  </>
                ) : (
                  <span className="text-red-400 text-sm font-semibold">NULL (DISCONNECTED)</span>
                )}
              </div>
              <span className="text-[9px] font-mono text-zinc-500 block mt-0.5">Physical wire open</span>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-zinc-900 flex items-center justify-between text-[11px] font-mono">
            <span className="text-zinc-500">Calibration State:</span>
            <span className="text-amber-400 font-bold">NOT CALIBRATED (M2.7 Ref Only)</span>
          </div>
        </div>

        {/* DHT11 Card */}
        <div className={`p-4 rounded-lg border bg-zinc-950/80 backdrop-blur ${
          tempRecord.availability === 'FAULT' ? 'border-red-900/80 bg-red-950/10' : 'border-zinc-800'
        }`}>
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <div className="flex items-center gap-1.5 text-xs font-mono font-medium">
              <Thermometer className="w-4 h-4 text-emerald-400" />
              <span>DHT11 (Climatic Ambient)</span>
            </div>
            {renderAvailabilityBadge(tempRecord.availability || 'FAULT', tempRecord.calibration_status)}
          </div>

          <div className="grid grid-cols-2 gap-2 mt-2">
            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <span className="text-[10px] font-mono text-zinc-500 block">TEMPERATURE (GPIO{tempRecord.gpio_pin})</span>
              <div className="text-xl font-mono font-bold text-zinc-100 flex items-baseline mt-1">
                {tempRecord.live_value !== null && tempRecord.live_value !== undefined ? (
                  `${Number(tempRecord.live_value).toFixed(1)} °C`
                ) : (
                  <span className="text-zinc-500 text-sm font-mono">-- <span className="text-[10px] text-cyan-400">(Ref: {tempRecord.reference_value}°C)</span></span>
                )}
              </div>
              <span className="text-[9px] font-mono text-zinc-500 block mt-0.5">
                {tempRecord.live_value !== null ? 'Live Active' : 'Disconnected'}
              </span>
            </div>

            <div className="p-2 rounded bg-zinc-900/60 border border-zinc-800">
              <span className="text-[10px] font-mono text-zinc-500 block">HUMIDITY (GPIO{humRecord.gpio_pin})</span>
              <div className="text-xl font-mono font-bold text-zinc-100 flex items-baseline mt-1">
                {humRecord.live_value !== null && humRecord.live_value !== undefined ? (
                  `${Number(humRecord.live_value).toFixed(1)} %RH`
                ) : (
                  <span className="text-zinc-500 text-sm font-mono">-- <span className="text-[10px] text-cyan-400">(Ref: {humRecord.reference_value}%)</span></span>
                )}
              </div>
              <span className="text-[9px] font-mono text-zinc-500 block mt-0.5">
                {humRecord.live_value !== null ? 'Live Active' : 'Disconnected'}
              </span>
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-zinc-900 text-[10px] font-mono text-zinc-500 flex items-center justify-between">
            <span>Ref Ambient: <span className="text-cyan-300">25.0°C / 50.0%RH</span></span>
            <span className="text-amber-400 font-bold">{tempRecord.live_value !== null ? 'ONLINE' : 'UNPLUGGED'}</span>
          </div>
        </div>

        {/* AI & Edge Inference Card */}
        <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <div className="flex items-center gap-1.5 text-xs font-mono font-medium">
              <Activity className="w-4 h-4 text-purple-400" />
              <span>Edge AI & Classification</span>
            </div>
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-900 border border-zinc-800 text-purple-300">
              TFLITE MICRO
            </span>
          </div>

          <div className="mt-1">
            <div className="text-xs font-mono font-bold text-zinc-200">
              Hazard Inference:
            </div>
            <div className="text-sm font-mono mt-1">
              {mq2Record.live_value !== null && mq135Record.live_value !== null ? (
                <span className="text-emerald-400 font-bold">EVALUATING WINDOW...</span>
              ) : (
                <span className="text-amber-400 font-semibold">UNKNOWN (SENSOR_FAULT)</span>
              )}
            </div>
            <div className="text-[11px] font-mono text-zinc-500 mt-1">
              {mq2Record.live_value !== null && mq135Record.live_value !== null 
                ? 'Sliding window accumulating features' 
                : 'Inference suspended: physical gas channel missing.'}
            </div>
          </div>

          <div className="mt-3 pt-2 border-t border-zinc-900 text-[10px] font-mono text-zinc-500 flex items-center justify-between">
            <span>Model: <span className="text-zinc-300">M2_COMPACT_MLP</span></span>
            <span>Relay Safe: <span className="text-emerald-400">HARDWARE LOCKED</span></span>
          </div>
        </div>
      </div>
    </div>
  );
};
