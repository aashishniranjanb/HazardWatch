'use client';

import React, { useState } from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
  ReferenceLine,
} from 'recharts';
import { NormalizedSensorReading, ThresholdConfig, UnifiedSensorsMap } from '@/lib/types';
import { Play, Pause, Trash2, Download } from 'lucide-react';

interface SensorChartsProps {
  history: NormalizedSensorReading[];
  thresholds: ThresholdConfig;
  onClear: () => void;
  hasMQ7: boolean;
  unifiedSensors?: UnifiedSensorsMap | null;
}

export const SensorCharts: React.FC<SensorChartsProps> = ({
  history,
  thresholds,
  onClear,
  hasMQ7,
  unifiedSensors = null,
}) => {
  const [isPaused, setIsPaused] = useState(false);
  const [windowSize, setWindowSize] = useState<number>(50);

  const displayData = isPaused ? history.slice(-windowSize) : history.slice(-windowSize);

  // Baselines for benchmark dashed reference lines
  const mq2Baseline = unifiedSensors?.mq2?.reference_value ?? 338;
  const mq135Baseline = unifiedSensors?.mq135?.reference_value ?? 1523;

  const exportCSV = () => {
    if (history.length === 0) return;
    const header = ['timestamp', 'time', 'mq2_adc', 'mq135_adc', 'mq7_adc', 'temperature', 'humidity', 'relay', 'pump', 'label'];
    const rows = history.map(h => [
      h.timestamp,
      h.timeString,
      h.mq2_adc ?? '',
      h.mq135_adc ?? '',
      h.mq7_adc ?? '',
      h.temperature ?? '',
      h.humidity ?? '',
      h.relay ? 1 : 0,
      h.pump ? 1 : 0,
      h.label ?? '',
    ]);

    const csvContent = 'data:text/csv;charset=utf-8,' + [header.join(','), ...rows.map(e => e.join(','))].join('\n');
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', `sensor_export_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-3">
      {/* Chart Control Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono font-bold text-zinc-300 uppercase">
            Telemetry Graphs ({history.length} records buffered)
          </span>
          <div className="flex items-center gap-1">
            {[30, 50, 100, 200].map(sz => (
              <button
                key={sz}
                onClick={() => setWindowSize(sz)}
                className={`px-2 py-0.5 text-[11px] font-mono rounded border transition-colors ${
                  windowSize === sz
                    ? 'bg-zinc-700 border-zinc-500 text-zinc-100 font-bold'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {sz} pts
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsPaused(!isPaused)}
            className={`px-3 py-1 rounded text-xs font-mono font-bold border flex items-center gap-1.5 transition-colors ${
              isPaused
                ? 'bg-amber-950/80 border-amber-600 text-amber-200'
                : 'bg-zinc-900 hover:bg-zinc-800 border-zinc-700 text-zinc-300'
            }`}
          >
            {isPaused ? <Play className="w-3.5 h-3.5" /> : <Pause className="w-3.5 h-3.5" />}
            {isPaused ? 'RESUME STREAM' : 'PAUSE VIEW'}
          </button>

          <button
            onClick={onClear}
            className="px-3 py-1 rounded text-xs font-mono border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 flex items-center gap-1.5"
          >
            <Trash2 className="w-3.5 h-3.5" />
            CLEAR
          </button>

          <button
            onClick={exportCSV}
            className="px-3 py-1 rounded text-xs font-mono border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 flex items-center gap-1.5"
          >
            <Download className="w-3.5 h-3.5" />
            EXPORT CSV
          </button>
        </div>
      </div>

      {/* Grid of Two Split Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
        {/* Gas Sensors (ADC) */}
        <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/90 backdrop-blur">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-zinc-300 uppercase">
              Gas Sensor ADC Response (MQ-2 / MQ-135 {hasMQ7 && '/ MQ-7'})
            </span>
            <div className="flex items-center gap-2 text-[10px] font-mono">
              <span className="text-amber-400 font-semibold">— Live MQ-2</span>
              <span className="text-cyan-400 font-semibold">— Live MQ-135</span>
              <span className="text-cyan-600 font-semibold">--- Ref Baselines</span>
            </div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={displayData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="timeString" stroke="#71717a" tick={{ fontSize: 10 }} />
                <YAxis stroke="#71717a" domain={[0, 4095]} tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />

                {/* Reference Baseline Lines (Dashed Benchmarks, never fake live data) */}
                <ReferenceLine
                  y={mq2Baseline}
                  stroke="#d97706"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                  label={{ value: `MQ-2 Ref (${mq2Baseline})`, fill: '#d97706', fontSize: 10, position: 'right' }}
                />
                <ReferenceLine
                  y={mq135Baseline}
                  stroke="#0891b2"
                  strokeDasharray="4 4"
                  strokeWidth={1}
                  label={{ value: `MQ-135 Ref (${mq135Baseline})`, fill: '#0891b2', fontSize: 10, position: 'right' }}
                />

                <Line
                  type="monotone"
                  dataKey="mq2_adc"
                  name="MQ-2 (Combustible)"
                  stroke="#f59e0b"
                  dot={false}
                  strokeWidth={2}
                  connectNulls={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="mq135_adc"
                  name="MQ-135 (Air Quality)"
                  stroke="#06b6d4"
                  dot={false}
                  strokeWidth={2}
                  connectNulls={false}
                  isAnimationActive={false}
                />
                {hasMQ7 && (
                  <Line
                    type="monotone"
                    dataKey="mq7_adc"
                    name="MQ-7 (Replay Only)"
                    stroke="#a855f7"
                    dot={false}
                    strokeWidth={1.5}
                    strokeDasharray="4 4"
                    connectNulls={false}
                    isAnimationActive={false}
                  />
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Climatic (DHT11) */}
        <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/90 backdrop-blur">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-mono font-bold text-zinc-300 uppercase">
              Ambient Climatic Conditions (DHT11 Temp & Humidity)
            </span>
            <div className="flex items-center gap-2 text-[10px] font-mono">
              <span className="text-emerald-400 font-semibold">— Live Temp</span>
              <span className="text-blue-400 font-semibold">— Live Humidity</span>
              <span className="text-zinc-500 font-semibold">--- Nominal Ambient</span>
            </div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={displayData} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#27272a" />
                <XAxis dataKey="timeString" stroke="#71717a" tick={{ fontSize: 10 }} />
                <YAxis stroke="#71717a" domain={[0, 100]} tick={{ fontSize: 10 }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#09090b', borderColor: '#27272a', borderRadius: '4px', fontSize: '11px', fontFamily: 'monospace' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />

                {/* Reference Nominal Ambient Lines */}
                <ReferenceLine
                  y={25.0}
                  stroke="#059669"
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  label={{ value: 'Ref Temp (25°C)', fill: '#059669', fontSize: 10, position: 'right' }}
                />
                <ReferenceLine
                  y={50.0}
                  stroke="#2563eb"
                  strokeDasharray="3 3"
                  strokeWidth={1}
                  label={{ value: 'Ref Humidity (50%)', fill: '#2563eb', fontSize: 10, position: 'right' }}
                />

                <Line
                  type="monotone"
                  dataKey="temperature"
                  name="Temperature (°C)"
                  stroke="#10b981"
                  dot={false}
                  strokeWidth={2}
                  connectNulls={false}
                  isAnimationActive={false}
                />
                <Line
                  type="monotone"
                  dataKey="humidity"
                  name="Humidity (%RH)"
                  stroke="#3b82f6"
                  dot={false}
                  strokeWidth={2}
                  connectNulls={false}
                  isAnimationActive={false}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
};
