'use client';

import React, { useState, useEffect } from 'react';
import { NormalizedSensorReading } from '@/lib/types';
import { Usb, RefreshCw, XCircle, Terminal, AlertTriangle, CheckCircle, Wifi, Play, Square } from 'lucide-react';

interface SerialManagerProps {
  onReading: (reading: NormalizedSensorReading) => void;
  onRawLog: (line: string) => void;
  isConnected: boolean;
  setIsConnected: (connected: boolean) => void;
}

export const SerialManager: React.FC<SerialManagerProps> = ({
  onReading,
  onRawLog,
  isConnected,
  setIsConnected,
}) => {
  const [backendSerial, setBackendSerial] = useState<any>(null);
  const [availablePorts, setAvailablePorts] = useState<any[]>([]);
  const [selectedPort, setSelectedPort] = useState<string>('COM4');
  const [baudRate, setBaudRate] = useState<number>(115200);
  const [statusMsg, setStatusMsg] = useState<string>('Polling backend serial status...');
  const [consoleLogs, setConsoleLogs] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);

  const fetchStatus = async () => {
    try {
      const [statusRes, portsRes] = await Promise.all([
        fetch('http://127.0.0.1:8000/api/v1/serial/status').catch(() => null),
        fetch('http://127.0.0.1:8000/api/v1/serial/ports').catch(() => null)
      ]);

      if (statusRes && statusRes.ok) {
        const s = await statusRes.json();
        setBackendSerial(s);
        setIsConnected(Boolean(s.connected));
        if (s.connected) {
          setStatusMsg(`Backend connected to ${s.port} at ${s.baud_rate} baud (${s.frames_received} frames received)`);
        } else if (s.last_error) {
          setStatusMsg(`Error: ${s.last_error}`);
        } else {
          setStatusMsg('Backend serial port closed/disconnected.');
        }
      }

      if (portsRes && portsRes.ok) {
        const p = await portsRes.json();
        setAvailablePorts(p.ports || []);
        if (p.ports && p.ports.length > 0 && !selectedPort) {
          setSelectedPort(p.ports[0].port);
        }
      }
    } catch (err: any) {
      setStatusMsg('Cannot reach backend on port 8000');
      setIsConnected(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleConnectBackend = async () => {
    setIsLoading(true);
    setStatusMsg(`Connecting backend to ${selectedPort}...`);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/serial/connect', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ port: selectedPort, baud_rate: baudRate })
      });
      if (res.ok) {
        const data = await res.json();
        setStatusMsg(`Backend successfully opened ${data.port}`);
        await fetchStatus();
      } else {
        const err = await res.json();
        setStatusMsg(`Connect failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e: any) {
      setStatusMsg(`Connection error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDisconnectBackend = async () => {
    setIsLoading(true);
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/serial/disconnect', {
        method: 'POST'
      });
      if (res.ok) {
        setStatusMsg('Backend serial disconnected.');
        await fetchStatus();
      }
    } catch (e: any) {
      setStatusMsg(`Disconnect error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="p-4 rounded-lg border border-zinc-800 bg-zinc-950/80 backdrop-blur space-y-3 font-mono">
      <div className="flex items-center justify-between pb-2 border-b border-zinc-900">
        <div className="flex items-center gap-2">
          <Usb className="w-4 h-4 text-amber-500" />
          <span className="text-xs font-bold tracking-wider uppercase text-zinc-200">
            Hardware Serial Link (FastAPI Sole-Owner Architecture)
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-[10px] px-2 py-0.5 rounded border ${
            isConnected
              ? 'bg-emerald-950/60 border-emerald-600 text-emerald-300 font-bold'
              : 'bg-zinc-900 border-zinc-800 text-zinc-500'
          }`}>
            {isConnected ? 'BACKEND PORT ACTIVE' : 'PORT CLOSED'}
          </span>
          <button
            onClick={fetchStatus}
            className="p-1 hover:bg-zinc-800 text-zinc-400 rounded"
            title="Refresh status"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Control bar */}
      <div className="flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 text-xs">
          <label className="text-zinc-400">Target Port:</label>
          <select
            value={selectedPort}
            onChange={(e) => setSelectedPort(e.target.value)}
            disabled={isConnected || isLoading}
            className="bg-zinc-900 border border-zinc-700 rounded px-2.5 py-1 text-zinc-200 disabled:opacity-50"
          >
            {availablePorts.length > 0 ? (
              availablePorts.map((p) => (
                <option key={p.port} value={p.port}>
                  {p.port} ({p.description})
                </option>
              ))
            ) : (
              <option value="COM4">COM4</option>
            )}
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <label className="text-zinc-400">Baud:</label>
          <select
            value={baudRate}
            onChange={(e) => setBaudRate(Number(e.target.value))}
            disabled={isConnected || isLoading}
            className="bg-zinc-900 border border-zinc-700 rounded px-2.5 py-1 text-zinc-200 disabled:opacity-50"
          >
            <option value={115200}>115200 (ESP32 Standard)</option>
            <option value={9600}>9600</option>
            <option value={921600}>921600</option>
          </select>
        </div>

        {!isConnected ? (
          <button
            onClick={handleConnectBackend}
            disabled={isLoading}
            className="px-4 py-1.5 rounded bg-emerald-600 hover:bg-emerald-500 text-zinc-950 text-xs font-bold flex items-center gap-2 shadow transition-all disabled:opacity-50"
          >
            <Play className="w-3.5 h-3.5 fill-current" />
            START BACKEND ACQUISITION
          </button>
        ) : (
          <button
            onClick={handleDisconnectBackend}
            disabled={isLoading}
            className="px-4 py-1.5 rounded bg-red-950/80 hover:bg-red-900 border border-red-600 text-red-200 text-xs font-bold flex items-center gap-2 transition-all disabled:opacity-50"
          >
            <Square className="w-3.5 h-3.5 fill-current" />
            STOP ACQUISITION
          </button>
        )}

        <div className="text-xs text-zinc-400 flex-1 truncate">
          Status: <span className="text-zinc-200">{statusMsg}</span>
        </div>
      </div>

      {/* Architectural Guarantee Note */}
      <div className="text-[11px] text-zinc-500 flex items-center gap-1.5 bg-zinc-900/50 p-2 rounded border border-zinc-800/80">
        <CheckCircle className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
        <span>
          FastAPI is the sole physical owner of {selectedPort}. Browser Web Serial direct-open is disabled to prevent port contention. Telemetry is streamed to SCADA via WebSocket.
        </span>
      </div>

      {/* Telemetry Stream Diagnostics */}
      {backendSerial && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 pt-1 text-[11px]">
          <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
            <span className="text-zinc-500 block">FRAMES CAPTURED</span>
            <span className="text-sm font-bold text-zinc-200">{backendSerial.frames_received ?? 0}</span>
          </div>
          <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
            <span className="text-zinc-500 block">LAST FRAME TIME</span>
            <span className="text-sm font-bold text-zinc-200">
              {backendSerial.last_frame_timestamp 
                ? new Date(backendSerial.last_frame_timestamp * 1000).toLocaleTimeString() 
                : '--'}
            </span>
          </div>
          <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
            <span className="text-zinc-500 block">ERROR COUNT</span>
            <span className={`text-sm font-bold ${backendSerial.last_error ? 'text-red-400' : 'text-emerald-400'}`}>
              {backendSerial.last_error ? 'FAULT' : '0 ERRORS'}
            </span>
          </div>
          <div className="p-2 bg-zinc-900/60 rounded border border-zinc-800">
            <span className="text-zinc-500 block">DATA PROVENANCE</span>
            <span className="text-sm font-bold text-amber-400">PHYSICAL_ESP32</span>
          </div>
        </div>
      )}
    </div>
  );
};
