export type OperatingMode = 'LIVE_HARDWARE' | 'CSV_REPLAY' | 'SYNTHETIC_SIMULATION';

export type RiskLevel = 'NORMAL' | 'WARNING' | 'CRITICAL';

export type SensorStatus = 'ONLINE' | 'OFFLINE' | 'DEGRADED' | 'UNAVAILABLE' | 'SIMULATED';

export interface NormalizedSensorReading {
  timestamp: number; // Unix timestamp in ms
  timeString: string; // HH:mm:ss or ISO
  source: 'HARDWARE' | 'HISTORICAL_REPLAY' | 'SYNTHETIC';
  
  // Primary gas sensors
  mq2_adc: number | null;
  mq2_voltage?: number | null;
  mq2_rs?: number | null;
  mq2_ratio?: number | null;
  mq2_ppm?: number | null; // Note: Educational indicator only, uncalibrated

  mq135_adc: number | null;
  mq135_rs?: number | null;
  mq135_ratio?: number | null;
  mq135_ppm?: number | null;

  // Historical-only channel (Not on physical prototype)
  mq7_adc?: number | null;
  mq7_rs?: number | null;
  mq7_ratio?: number | null;
  mq7_ppm?: number | null;

  // Environment (Only on hardware/synthetic; null in historical datasets)
  temperature: number | null; // °C
  humidity: number | null;    // %RH

  // Actuation status
  relay: boolean;
  pump: boolean;
  
  // Fault status
  fault?: boolean;

  // Historical label if present
  label?: string | number | null;
  rawJson?: string;
}

export interface ThresholdConfig {
  mq2_warning_adc: number;
  mq2_critical_adc: number;
  mq135_warning_adc: number;
  mq135_critical_adc: number;
  hysteresis_adc: number; // ADC delta required to release state
  sustained_duration_ms: number; // Duration reading must remain high before triggering
}

export interface RiskEvaluation {
  level: RiskLevel;
  activeAlerts: string[];
  reasons: string[];
  suggestedVentilation: boolean;
  timestamp: number;
}

export interface RiskEvent {
  id: string;
  timestamp: number;
  timeString: string;
  type: 'RISK_TRANSITION' | 'THRESHOLD_CROSSING' | 'VENTILATION' | 'COMMUNICATION' | 'DATASET';
  severity: 'INFO' | 'WARNING' | 'CRITICAL';
  title: string;
  description: string;
  mode: OperatingMode;
}

export interface DatasetSummary {
  id: string;
  name: string;
  filename: string;
  totalRows: number;
  validRows: number;
  skippedRows: number;
  columns: string[];
  hasMQ7: boolean;
  hasDHT11: boolean;
  uniqueLabels: Array<string | number>;
  timeRange?: {
    start: string;
    end: string;
  };
  sampleRows: Record<string, string | number>[];
}

export interface SerialConnectionStatus {
  connected: boolean;
  portInfo: string | null;
  baudRate: number;
  dataRateBps: number;
  messagesReceived: number;
  parsingErrors: number;
  lastMessageTime: number | null;
}

export interface VentilationState {
  relay: boolean;
  pump: boolean;
  mode: 'AUTO' | 'MANUAL';
  isVirtual: boolean; // True in Replay / Synthetic; False in validated Hardware mode
  lastActivationTime: number | null;
  activationCount: number;
}

// -------------------------------------------------------------
// UNIFIED SENSOR 5-STATE VALUE MODEL (M5.3.1)
// -------------------------------------------------------------
export type SensorAvailabilityState = 'LIVE' | 'LAST_KNOWN' | 'REFERENCE' | 'UNAVAILABLE' | 'FAULT';

export interface UnifiedSensorRecord {
  sensor_id: string;
  sensor_name: string;
  gpio_pin: number;
  live_value: number | null;
  last_known_value: number | null;
  last_known_timestamp: number | null;
  reference_value: number | null;
  reference_source: string;
  reference_timestamp: number | null;
  availability: SensorAvailabilityState;
  calibration_status: 'MEASURED_CALIBRATION' | 'CALIBRATED_BENCHMARK' | 'FACTORY_NOMINAL' | 'NOT_CALIBRATED' | string;
  unit: string;
}

export type UnifiedSensorsMap = Record<string, UnifiedSensorRecord>;

