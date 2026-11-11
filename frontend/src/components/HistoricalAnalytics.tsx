'use client';

import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, AlertTriangle, Activity, RefreshCw } from 'lucide-react';

export const HistoricalAnalytics: React.FC = () => {
  const [analytics, setAnalytics] = useState<any | null>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchAnalytics = async () => {
    setIsLoading(true);
    try {
      const [aRes, eRes] = await Promise.all([
        fetch('http://localhost:8000/api/v1/analytics').catch(() => null),
        fetch('http://localhost:8000/api/v1/events?limit=25').catch(() => null),
      ]);

      if (aRes && aRes.ok) setAnalytics(await aRes.json());
      if (eRes && eRes.ok) setEvents(await eRes.json());
    } catch {
      // Ignore
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  return (
    <div className="space-y-4 font-mono">
      <div className="border border-zinc-800 bg-zinc-950/80 rounded-lg p-4">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-amber-400" />
            <h2 className="text-sm font-bold text-zinc-100 uppercase tracking-wider">
              Factory Atmospheric Trends & Historical Analytics
            </h2>
          </div>
          <button
            onClick={fetchAnalytics}
            disabled={isLoading}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs rounded border border-zinc-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Analytics Summary KPI Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4">
          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <span className="text-[11px] text-zinc-400">Total Telemetry Windows:</span>
            <div className="text-lg font-bold text-zinc-100 mt-1">
              {analytics?.total_telemetry_records ?? 0}
            </div>
          </div>
          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <span className="text-[11px] text-zinc-400">Active Incidents:</span>
            <div className="text-lg font-bold text-red-400 mt-1">
              {analytics?.active_incidents ?? 0}
            </div>
          </div>
          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <span className="text-[11px] text-zinc-400">Acknowledged:</span>
            <div className="text-lg font-bold text-amber-400 mt-1">
              {analytics?.acknowledged_incidents ?? 0}
            </div>
          </div>
          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <span className="text-[11px] text-zinc-400">Resolved Incidents:</span>
            <div className="text-lg font-bold text-emerald-400 mt-1">
              {analytics?.resolved_incidents ?? 0}
            </div>
          </div>
        </div>

        {/* Audit Log Table */}
        <div className="mt-5">
          <h3 className="text-xs font-bold text-zinc-300 mb-2">Persistent System Audit Log:</h3>
          <div className="border border-zinc-800 rounded-md overflow-hidden">
            <table className="w-full text-left text-xs">
              <thead className="bg-zinc-900 text-zinc-400 border-b border-zinc-800">
                <tr>
                  <th className="p-2">Timestamp</th>
                  <th className="p-2">Type</th>
                  <th className="p-2">Source</th>
                  <th className="p-2">Severity</th>
                  <th className="p-2">Description</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 bg-zinc-950">
                {events.length > 0 ? (
                  events.map((e, idx) => (
                    <tr key={idx} className="hover:bg-zinc-900/40">
                      <td className="p-2 text-zinc-500 whitespace-nowrap">
                        {new Date(e.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="p-2 font-bold text-zinc-300">{e.event_type}</td>
                      <td className="p-2 text-zinc-400">{e.source}</td>
                      <td className="p-2">
                        <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                          e.severity === 'CRITICAL' ? 'bg-red-950 text-red-300' :
                          e.severity === 'WARNING' ? 'bg-amber-950 text-amber-300' :
                          'bg-zinc-800 text-zinc-400'
                        }`}>
                          {e.severity}
                        </span>
                      </td>
                      <td className="p-2 text-zinc-300">{e.description}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-4 text-center text-zinc-500">
                      No system events logged in database.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};
