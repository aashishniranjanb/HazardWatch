'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Header } from '@/components/Header';
import { SensorCards } from '@/components/SensorCards';
import { RiskAndVentilation } from '@/components/RiskAndVentilation';
import { SensorCharts } from '@/components/SensorCharts';
import { SerialManager } from '@/components/SerialManager';
import { DatasetManager } from '@/components/DatasetManager';
import { SyntheticSimulation } from '@/components/SyntheticSimulation';
import { EventLogTable } from '@/components/EventLogTable';
import { SettingsPanel } from '@/components/SettingsPanel';
import { FactoryZoneMonitor } from '@/components/FactoryZoneMonitor';
import { IncidentIntelligenceCard, IndustrialIncident } from '@/components/IncidentIntelligenceCard';
import { ScreenNavigation, ScreenId } from '@/components/ScreenNavigation';
import { ModelLaboratory } from '@/components/ModelLaboratory';
import { SystemDiagnostics } from '@/components/SystemDiagnostics';
import { HistoricalAnalytics } from '@/components/HistoricalAnalytics';
import { RiskEngine, DEFAULT_THRESHOLDS } from '@/lib/risk-engine';
import { ReplayEngine } from '@/lib/replay';
import { SyntheticScenario } from '@/lib/synthetic-scenarios';
import {
  OperatingMode,
  NormalizedSensorReading,
  RiskEvaluation,
  ThresholdConfig,
  RiskEvent,
  DatasetSummary,
  UnifiedSensorsMap,
} from '@/lib/types';

export default function Dashboard() {
  const [activeScreen, setActiveScreen] = useState<ScreenId>('OVERVIEW');
  const [mode, setMode] = useState<OperatingMode>('CSV_REPLAY');
  const [currentReading, setCurrentReading] = useState<NormalizedSensorReading | null>(null);
  const [history, setHistory] = useState<NormalizedSensorReading[]>([]);
  const [thresholds, setThresholds] = useState<ThresholdConfig>(DEFAULT_THRESHOLDS);
  const [events, setEvents] = useState<RiskEvent[]>([]);
  const [unifiedSensors, setUnifiedSensors] = useState<UnifiedSensorsMap | null>(null);
  
  // Factory Zone Selection
  const [selectedZone, setSelectedZone] = useState<string>('Z03');

  // Active Incident State
  const [currentIncident, setCurrentIncident] = useState<IndustrialIncident>({
    event_id: 'EVT-0001',
    timestamp: Date.now(),
    operating_mode: 'CSV_REPLAY',
    zone_id: 'Z03',
    zone_name: 'Painting and Coating Section',
    sensor_state: 'VALID',
    severity: 'NORMAL',
    trend: 'STABLE',
    pattern: 'NORMAL_BASELINE',
    industrial_context: 'ATMOSPHERE_NOMINAL',
    evidence: ['Sensor baseline stability maintained'],
    gas_identity: 'NOT_CONFIRMED',
    ml_confidence: 0.98,
    recommended_action: 'CONTINUE_ROUTINE_MONITORING',
    incident_state: 'RESOLVED',
    relay_command: 'OFF',
    verification_steps: ['Observe extraction flow indicators'],
    emergency_procedure: 'Initiate standard zone ventilation protocol',
  });

  // Ventilation states
  const [ventilationMode, setVentilationMode] = useState<'AUTO' | 'MANUAL'>('AUTO');
  const [manualRelayOverride, setManualRelayOverride] = useState<boolean>(false);
  const [manualPumpOverride, setManualPumpOverride] = useState<boolean>(false);

  // Connection states
  const [serialConnected, setSerialConnected] = useState<boolean>(false);
  const [wsConnected, setWsConnected] = useState<boolean>(false);
  const [currentTime, setCurrentTime] = useState<string>('');

  // Replay state
  const replayEngineRef = useRef<ReplayEngine>(new ReplayEngine([]));
  const [isPlayingReplay, setIsPlayingReplay] = useState<boolean>(false);
  const [replayIndex, setReplayIndex] = useState<number>(0);
  const [totalDatasetRows, setTotalDatasetRows] = useState<number>(0);
  const [replaySpeed, setReplaySpeed] = useState<number>(1);
  const [datasetSummary, setDatasetSummary] = useState<DatasetSummary | null>(null);

  // Synthetic Simulation state
  const [activeScenarioId, setActiveScenarioId] = useState<string | null>(null);
  const syntheticTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Risk Engine Ref
  const riskEngineRef = useRef<RiskEngine>(new RiskEngine(DEFAULT_THRESHOLDS));

  // Clock
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toLocaleTimeString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const addEvent = useCallback((event: Omit<RiskEvent, 'id' | 'timestamp' | 'timeString'>) => {
    const newEvt: RiskEvent = {
      ...event,
      id: Math.random().toString(36).substring(2, 9),
      timestamp: Date.now(),
      timeString: new Date().toLocaleTimeString(),
    };
    setEvents(prev => [newEvt, ...prev].slice(0, 100));
  }, []);

  const handleUpdateThresholds = (newThresholds: ThresholdConfig) => {
    setThresholds(newThresholds);
    riskEngineRef.current = new RiskEngine(newThresholds);
    addEvent({
      type: 'THRESHOLD_CROSSING',
      severity: 'WARNING',
      title: 'Safety Thresholds Reconfigured',
      description: 'Operator adjusted dynamic baseline risk thresholds.',
      mode,
    });
  };

  const processNewReading = useCallback((reading: NormalizedSensorReading) => {
    setCurrentReading(reading);
    setHistory(prev => [...prev.slice(-120), reading]);

    const evalResult: RiskEvaluation = riskEngineRef.current.evaluate(reading);

    const isHazard = evalResult.level === 'CRITICAL' || evalResult.level === 'WARNING';
    if (isHazard && currentIncident.severity === 'NORMAL') {
      const isCombustible = (reading.mq2_adc ?? 0) > 500;
      setCurrentIncident({
        event_id: `EVT-${Date.now()}`,
        timestamp: Date.now(),
        operating_mode: mode,
        zone_id: selectedZone,
        zone_name: 'Industrial Zone Monitoring Section',
        sensor_state: reading.fault ? 'FAULT' : 'VALID',
        severity: evalResult.level,
        trend: 'RISING',
        pattern: isCombustible ? 'COMBUSTIBLE_RESPONSE_PATTERN' : 'VOC_RESPONSE',
        industrial_context: 'HAZARD_THRESHOLD_EXCEEDED',
        evidence: evalResult.reasons.length > 0 ? evalResult.reasons : ['Threshold exceeded'],
        gas_identity: 'NOT_CONFIRMED',
        ml_confidence: 0.94,
        recommended_action: 'OPERATOR_VERIFICATION_REQUIRED',
        incident_state: 'UNVERIFIED',
        relay_command: reading.fault ? 'OFF' : 'ON',
        verification_steps: ['Check zone extraction ducts', 'Confirm sensor wiring'],
        emergency_procedure: 'Evacuate non-essential personnel if verified',
      });
    }
  }, [mode, selectedZone, currentIncident.severity]);

  // Poll backend serial connection and live telemetry
  useEffect(() => {
    let active = true;

    const checkBackendStatus = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8000/api/v1/serial/status');
        if (res.ok && active) {
          const s = await res.json();
          setSerialConnected(Boolean(s.connected));
        } else if (active) {
          setSerialConnected(false);
        }
      } catch {
        if (active) setSerialConnected(false);
      }
    };

    const pollLiveTelemetry = async () => {
      if (mode !== 'LIVE_HARDWARE') return;
      try {
        const [resLive, resUnified] = await Promise.all([
          fetch('http://127.0.0.1:8000/api/v1/telemetry/live'),
          fetch('http://127.0.0.1:8000/api/v1/sensors/unified')
        ]);
        if (resUnified.ok && active) {
          const uData = await resUnified.json();
          if (uData.sensors) {
            setUnifiedSensors(uData.sensors);
          }
        }
        if (resLive.ok && active) {
          const json = await resLive.json();
          if (json.data) {
            const raw = json.data;
            const sensors = raw.sensors || raw;
            const mq2 = sensors.mq2_adc ?? null;
            const mq135 = sensors.mq135_adc ?? null;
            const temp = sensors.temperature_c ?? sensors.temperature ?? null;
            const hum = sensors.humidity_percent ?? sensors.humidity ?? null;
            const isFault = raw.monitoring_state === 'SENSOR_FAULT' || raw.hazard_state === 'SENSOR_FAULT' || raw.fault_detected;

            const reading: NormalizedSensorReading = {
              timestamp: raw.timestamp_ms ? raw.timestamp_ms : (raw.timestamp || Date.now()),
              timeString: new Date().toLocaleTimeString(),
              source: 'HARDWARE',
              mq2_adc: mq2,
              mq135_adc: mq135,
              temperature: temp,
              humidity: hum,
              relay: Boolean(raw.actual_relay_state || (raw.relay && raw.relay.command === 'ENABLED')),
              pump: false,
              fault: isFault,
              rawJson: JSON.stringify(raw),
            };
            processNewReading(reading);
          }
        }
      } catch {
        // Disconnected or backend offline
      }
    };

    checkBackendStatus();
    const statusInterval = setInterval(checkBackendStatus, 3000);
    const telemetryInterval = setInterval(pollLiveTelemetry, 1000);

    return () => {
      active = false;
      clearInterval(statusInterval);
      clearInterval(telemetryInterval);
    };
  }, [mode, processNewReading]);

  const currentRisk: RiskEvaluation = currentReading
    ? riskEngineRef.current.evaluate(currentReading)
    : {
        level: 'NORMAL',
        activeAlerts: [],
        reasons: ['Baseline clean air monitoring nominal'],
        suggestedVentilation: false,
        timestamp: Date.now(),
      };

  const effectiveRelay =
    ventilationMode === 'MANUAL'
      ? manualRelayOverride
      : (currentReading?.fault ? false : currentRisk.suggestedVentilation);

  const effectivePump =
    ventilationMode === 'MANUAL'
      ? manualPumpOverride
      : (currentReading?.fault ? false : currentRisk.suggestedVentilation);

  const handleDatasetLoaded = (summary: DatasetSummary, readings: NormalizedSensorReading[]) => {
    const engine = new ReplayEngine(readings);
    engine.setCallback((reading, idx) => {
      setReplayIndex(idx);
      processNewReading(reading);
    });
    replayEngineRef.current = engine;
    setDatasetSummary(summary);
    setTotalDatasetRows(summary.totalRows);
    setReplayIndex(0);
    setHistory([]);
    addEvent({
      type: 'DATASET',
      severity: 'INFO',
      title: 'Historical Dataset Loaded',
      description: `Loaded ${summary.name} (${summary.totalRows} records)`,
      mode: 'CSV_REPLAY',
    });
  };

  const handlePlayReplay = () => setIsPlayingReplay(true);
  const handlePauseReplay = () => setIsPlayingReplay(false);
  const handleStopReplay = () => {
    setIsPlayingReplay(false);
    setReplayIndex(0);
  };
  const handleSpeedChange = (spd: number) => setReplaySpeed(spd);
  const handleSeek = (idx: number) => {
    setReplayIndex(idx);
    replayEngineRef.current.seek(idx);
  };

  const handleSelectScenario = (scenario: SyntheticScenario) => {
    setActiveScenarioId(scenario.id);
    if (syntheticTimerRef.current) clearInterval(syntheticTimerRef.current);
    let stepCount = 0;
    syntheticTimerRef.current = setInterval(() => {
      stepCount++;
      const prevReading = currentReading || {
        timestamp: Date.now(),
        timeString: new Date().toLocaleTimeString(),
        source: 'SYNTHETIC' as const,
        mq2_adc: 338,
        mq135_adc: 1523,
        temperature: 25.0,
        humidity: 50.0,
        relay: false,
        pump: false,
      };
      const reading = scenario.generateReading(stepCount, prevReading);
      processNewReading(reading);
    }, 600);
  };

  const handleStopScenario = () => {
    if (syntheticTimerRef.current) {
      clearInterval(syntheticTimerRef.current);
      syntheticTimerRef.current = null;
    }
    setActiveScenarioId(null);
  };

  return (
    <div className="min-h-screen bg-black text-zinc-100 flex flex-col font-sans">
      <Header
        mode={mode}
        onModeChange={(m) => {
          setMode(m);
          if (m !== 'CSV_REPLAY' && isPlayingReplay) handlePauseReplay();
          if (m !== 'SYNTHETIC_SIMULATION' && activeScenarioId) handleStopScenario();
        }}
        riskLevel={currentRisk.level}
        serialConnected={serialConnected}
        wsConnected={wsConnected}
        currentTime={currentTime}
      />

      <main className="flex-1 p-4 max-w-7xl mx-auto w-full space-y-4">
        {/* Navigation Bar Across All 11 SCADA Screens */}
        <ScreenNavigation
          activeScreen={activeScreen}
          onSelectScreen={setActiveScreen}
          activeIncidentsCount={currentIncident.severity !== 'NORMAL' ? 1 : 0}
        />

        {/* SCREEN 1: PLANT OVERVIEW */}
        {activeScreen === 'OVERVIEW' && (
          <div className="space-y-4">
            <FactoryZoneMonitor
              selectedZone={selectedZone}
              onSelectZone={setSelectedZone}
              activeSeverity={currentIncident.severity}
            />
            <IncidentIntelligenceCard incident={currentIncident} />
            <SensorCards
              reading={currentReading}
              risk={currentRisk}
              thresholds={thresholds}
              mode={mode}
              systemState={mode === 'LIVE_HARDWARE' && !serialConnected ? 'DISCONNECTED' : 'LIVE_MONITORING'}
              unifiedSensors={unifiedSensors}
            />
            <RiskAndVentilation
              risk={currentRisk}
              thresholds={thresholds}
              mode={mode}
              relayActive={effectiveRelay}
              pumpActive={effectivePump}
              ventilationMode={ventilationMode}
              onVentilationModeToggle={() =>
                setVentilationMode(prev => (prev === 'AUTO' ? 'MANUAL' : 'AUTO'))
              }
              onManualVentilationToggle={() => {
                const next = !manualPumpOverride;
                setManualPumpOverride(next);
                setManualRelayOverride(next);
              }}
            />
          </div>
        )}

        {/* SCREEN 2: FACTORY ZONES */}
        {activeScreen === 'ZONES' && (
          <FactoryZoneMonitor
            selectedZone={selectedZone}
            onSelectZone={setSelectedZone}
            activeSeverity={currentIncident.severity}
          />
        )}

        {/* SCREEN 3: LIVE SENSOR MONITOR */}
        {activeScreen === 'LIVE_MONITOR' && (
          <div className="space-y-4">
            <SensorCards
              reading={currentReading}
              risk={currentRisk}
              thresholds={thresholds}
              mode={mode}
              systemState={mode === 'LIVE_HARDWARE' && !serialConnected ? 'DISCONNECTED' : 'LIVE_MONITORING'}
              unifiedSensors={unifiedSensors}
            />
            <SensorCharts
              history={history}
              thresholds={thresholds}
              onClear={() => setHistory([])}
              hasMQ7={Boolean(datasetSummary?.hasMQ7)}
              unifiedSensors={unifiedSensors}
            />
          </div>
        )}

        {/* SCREEN 4: AI HAZARD INTELLIGENCE */}
        {activeScreen === 'AI_INTELLIGENCE' && (
          <IncidentIntelligenceCard incident={currentIncident} />
        )}

        {/* SCREEN 5: INCIDENT MANAGEMENT */}
        {activeScreen === 'INCIDENTS' && (
          <div className="space-y-4">
            <IncidentIntelligenceCard incident={currentIncident} />
            <EventLogTable events={events} onClear={() => setEvents([])} />
          </div>
        )}

        {/* SCREEN 6: VENTILATION & RELAY */}
        {activeScreen === 'VENTILATION' && (
          <RiskAndVentilation
            risk={currentRisk}
            thresholds={thresholds}
            mode={mode}
            relayActive={effectiveRelay}
            pumpActive={effectivePump}
            ventilationMode={ventilationMode}
            onVentilationModeToggle={() =>
              setVentilationMode(prev => (prev === 'AUTO' ? 'MANUAL' : 'AUTO'))
            }
            onManualVentilationToggle={() => {
              const next = !manualPumpOverride;
              setManualPumpOverride(next);
              setManualRelayOverride(next);
            }}
          />
        )}

        {/* SCREEN 7: TRENDS & ANALYTICS */}
        {activeScreen === 'ANALYTICS' && (
          <div className="space-y-4">
            <HistoricalAnalytics />
            <SensorCharts
              history={history}
              thresholds={thresholds}
              onClear={() => setHistory([])}
              hasMQ7={Boolean(datasetSummary?.hasMQ7)}
              unifiedSensors={unifiedSensors}
            />
          </div>
        )}

        {/* SCREEN 8: SIMULATION LAB */}
        {activeScreen === 'SIMULATION_LAB' && (
          <SyntheticSimulation
            activeScenarioId={activeScenarioId}
            onSelectScenario={handleSelectScenario}
            onStopScenario={handleStopScenario}
            isSimulating={Boolean(activeScenarioId)}
          />
        )}

        {/* SCREEN 9: DATASET EXPLORER */}
        {activeScreen === 'DATASET_EXPLORER' && (
          <DatasetManager
            onDatasetLoaded={handleDatasetLoaded}
            onPlay={handlePlayReplay}
            onPause={handlePauseReplay}
            onStop={handleStopReplay}
            onSpeedChange={handleSpeedChange}
            onSeek={handleSeek}
            isPlaying={isPlayingReplay}
            currentIndex={replayIndex}
            totalRecords={totalDatasetRows}
            speed={replaySpeed}
            currentSummary={datasetSummary}
          />
        )}

        {/* SCREEN 10: MODEL LABORATORY */}
        {activeScreen === 'MODEL_LAB' && (
          <ModelLaboratory currentReading={currentReading || undefined} />
        )}

        {/* SCREEN 11: SYSTEM DIAGNOSTICS */}
        {activeScreen === 'DIAGNOSTICS' && (
          <div className="space-y-4">
            <SystemDiagnostics />
            {mode === 'LIVE_HARDWARE' && (
              <SerialManager
                onReading={processNewReading}
                onRawLog={() => {}}
                isConnected={serialConnected}
                setIsConnected={setSerialConnected}
              />
            )}
            <SettingsPanel thresholds={thresholds} onUpdate={handleUpdateThresholds} />
          </div>
        )}
      </main>
    </div>
  );
}
