'use client';

import React, { useState } from 'react';
import { RiskEvent } from '@/lib/types';
import { History, Download, Filter, AlertTriangle, Info, ShieldAlert } from 'lucide-react';

interface EventLogTableProps {
  events: RiskEvent[];
  onClear: () => void;
}

export const EventLogTable: React.FC<EventLogTableProps> = ({ events, onClear }) => {
  const [filter, setFilter] = useState<string>('ALL');

  const filteredEvents = events.filter((e) => {
    if (filter === 'ALL') return true;
    if (filter === 'WARNING') return e.severity === 'WARNING';
    if (filter === 'CRITICAL') return e.severity === 'CRITICAL';
    if (filter === 'VENTILATION') return e.type === 'VENTILATION';
    if (filter === 'COMMUNICATION') return e.type === 'COMMUNICATION';
    return true;
  });

  const exportEventsCSV = () => {
    if (events.length === 0) return;
    const header = ['timestamp', 'time', 'type', 'severity', 'title', 'description', 'mode'];
    const rows = events.map(e => [
      e.timestamp,
      `"${e.timeString}"`,
      e.type,
      e.severity,
      `"${e.title.replace(/"/g, '""')}"`,
      `"${e.description.replace(/"/g, '""')}"`,
      e.mode,
    ]);

    const csv = 'data:text/csv;charset=utf-8,' + [header.join(','), ...rows.map(r => r.join(','))].join('\n');
    const encoded = encodeURI(csv);
    const link = document.createElement('a');
    link.href = encoded;
    link.download = `event_audit_log_${Date.now()}.csv`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3 pb-2 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-amber-500" />
          <span className="text-xs font-mono font-bold tracking-wider uppercase text-zinc-200">
            Audit Event Logging & Sequence of Events (SOE)
          </span>
          <span className="text-[10px] font-mono text-zinc-500">
            ({filteredEvents.length} events logged)
          </span>
        </div>

        <div className="flex items-center gap-2">
          {/* Filters */}
          <div className="flex items-center gap-1">
            {['ALL', 'CRITICAL', 'WARNING', 'VENTILATION', 'COMMUNICATION'].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-2 py-0.5 text-[10px] font-mono rounded border transition-colors ${
                  filter === f
                    ? 'bg-zinc-700 border-zinc-500 text-zinc-100 font-bold'
                    : 'bg-zinc-900 border-zinc-800 text-zinc-400 hover:text-zinc-200'
                }`}
              >
                {f}
              </button>
            ))}
          </div>

          <button
            onClick={exportEventsCSV}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-700 text-xs font-mono text-zinc-300 flex items-center gap-1"
          >
            <Download className="w-3 h-3" /> Export Logs
          </button>

          <button
            onClick={onClear}
            className="px-2.5 py-1 rounded bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-xs font-mono text-zinc-400 hover:text-zinc-200"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-56 overflow-y-auto border border-zinc-900 rounded">
        <table className="w-full text-left font-mono text-[11px] text-zinc-300">
          <thead className="bg-zinc-900/90 text-zinc-400 uppercase text-[10px] sticky top-0">
            <tr>
              <th className="py-2 px-3">Timestamp</th>
              <th className="py-2 px-2">Severity</th>
              <th className="py-2 px-2">Type</th>
              <th className="py-2 px-3">Event Title</th>
              <th className="py-2 px-3">Details</th>
              <th className="py-2 px-2">Mode</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-900">
            {filteredEvents.length === 0 ? (
              <tr>
                <td colSpan={6} className="py-6 text-center text-zinc-600 italic">
                  No log entries recorded matching criteria.
                </td>
              </tr>
            ) : (
              filteredEvents.map((evt) => (
                <tr key={evt.id} className="hover:bg-zinc-900/40">
                  <td className="py-1.5 px-3 text-zinc-500 whitespace-nowrap">{evt.timeString}</td>
                  <td className="py-1.5 px-2">
                    <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                      evt.severity === 'CRITICAL' ? 'bg-red-950 text-red-300 border border-red-700' :
                      evt.severity === 'WARNING' ? 'bg-amber-950 text-amber-300 border border-amber-700' :
                      'bg-zinc-900 text-zinc-400 border border-zinc-800'
                    }`}>
                      {evt.severity}
                    </span>
                  </td>
                  <td className="py-1.5 px-2 text-zinc-400">{evt.type}</td>
                  <td className="py-1.5 px-3 font-semibold text-zinc-200">{evt.title}</td>
                  <td className="py-1.5 px-3 text-zinc-400 max-w-xs truncate">{evt.description}</td>
                  <td className="py-1.5 px-2 text-zinc-500 text-[10px]">{evt.mode}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
