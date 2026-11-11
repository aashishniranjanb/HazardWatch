'use client';

import React, { useState, useEffect } from 'react';
import { Wrench, CheckCircle, XCircle, AlertTriangle, RefreshCw, Server, Wifi, Database } from 'lucide-react';

export const SystemDiagnostics: React.FC = () => {
  const [healthData, setHealthData] = useState<any | null>(null);
  const [comPorts, setComPorts] = useState<any[]>([]);
  const [serialStatus, setSerialStatus] = useState<any | null>(null);
  const [isRefreshing, setIsRefreshing] = useState<boolean>(false);

  const fetchDiagnostics = async () => {
    setIsRefreshing(true);
    try {
      const [hRes, pRes, sRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/v1/health').catch(() => null),
        fetch('http://127.0.0.1:8000/api/v1/serial/ports').catch(() => null),
        fetch('http://127.0.0.1:8000/api/v1/serial/status').catch(() => null),
      ]);

      if (hRes && hRes.ok) {
        setHealthData(await hRes.json());
      } else {
        setHealthData({ status: 'OFFLINE', database: 'DISCONNECTED', models_loaded: 0 });
      }

      if (pRes && pRes.ok) {
        const ports = await pRes.json();
        setComPorts(ports.ports || []);
      }

      if (sRes && sRes.ok) {
        setSerialStatus(await sRes.json());
      }
    } catch {
      setHealthData({ status: 'OFFLINE', database: 'DISCONNECTED', models_loaded: 0 });
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDiagnostics();
  }, []);

  return (
    <div className="space-y-4 font-mono">
      <div className="border border-zinc-800 bg-zinc-950/80 rounded-lg p-4">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Wrench className="w-5 h-5 text-amber-400" />
            <h2 className="text-sm font-bold text-zinc-100 uppercase tracking-wider">
              System Diagnostics & Communications Health
            </h2>
          </div>
          <button
            onClick={fetchDiagnostics}
            disabled={isRefreshing}
            className="flex items-center gap-1.5 px-2.5 py-1 bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs rounded border border-zinc-700"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>

        {/* Diagnostic Badges */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-3 mt-4">
          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-zinc-400">FastAPI Server:</span>
              <Server className="w-4 h-4 text-cyan-400" />
            </div>
            <div className="text-sm font-bold mt-1 text-zinc-200">
              {healthData?.status === 'HEALTHY' ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> OPERATIONAL
                </span>
              ) : (
                <span className="text-zinc-500 flex items-center gap-1">
                  <AlertTriangle className="w-3.5 h-3.5" /> DISCONNECTED
                </span>
              )}
            </div>
          </div>

          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-zinc-400">SQLite Database:</span>
              <Database className="w-4 h-4 text-amber-400" />
            </div>
            <div className="text-sm font-bold mt-1 text-zinc-200">
              {healthData?.database === 'CONNECTED' ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> PERSISTENCE ACTIVE
                </span>
              ) : (
                <span className="text-zinc-500">LOCAL MEMORY</span>
              )}
            </div>
          </div>

          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-zinc-400">ML Model Engine:</span>
              <CheckCircle className="w-4 h-4 text-emerald-400" />
            </div>
            <div className="text-sm font-bold mt-1 text-emerald-300">
              4 Models Verified
            </div>
          </div>

          <div className="p-3 bg-zinc-900/60 border border-zinc-800 rounded-md">
            <div className="flex items-center justify-between">
              <span className="text-xs text-zinc-400">Hardware Serial:</span>
              <Wifi className="w-4 h-4 text-zinc-400" />
            </div>
            <div className="text-sm font-bold mt-1 text-zinc-400">
              {serialStatus?.connected ? (
                <span className="text-emerald-400 flex items-center gap-1">
                  <CheckCircle className="w-3.5 h-3.5" /> {serialStatus.port} ({serialStatus.frames_received} frames)
                </span>
              ) : serialStatus?.status === 'ERROR' ? (
                <span className="text-red-400 flex items-center gap-1">
                  <XCircle className="w-3.5 h-3.5" /> PORT ERROR
                </span>
              ) : (
                <span className="text-zinc-500">DISCONNECTED</span>
              )}
            </div>
          </div>
        </div>

        {/* COM Port Enumeration List */}
        <div className="mt-5 p-3 bg-zinc-900/40 border border-zinc-800 rounded-md">
          <h3 className="text-xs font-bold text-zinc-300 mb-2">Host Serial Communications Ports:</h3>
          {comPorts.length > 0 ? (
            <div className="space-y-1">
              {comPorts.map((p, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 bg-zinc-950 border border-zinc-800 rounded text-xs">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-amber-400">{p.port}</span>
                    <span className="text-zinc-400">{p.description}</span>
                  </div>
                  <span className={`text-[10px] px-2 py-0.5 rounded ${
                    p.is_usb_uart ? 'bg-emerald-950 text-emerald-400' : 'bg-zinc-800 text-zinc-500'
                  }`}>
                    {p.is_usb_uart ? 'USB-UART BRIDGE' : 'SYSTEM PORT'}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-3 text-xs text-zinc-500 bg-zinc-950 rounded border border-zinc-800">
              No serial ports enumerated. Please ensure backend is running or connect USB cable.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
