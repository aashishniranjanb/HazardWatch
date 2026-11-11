import { NormalizedSensorReading, ThresholdConfig, RiskEvaluation } from './types';

export const DEFAULT_THRESHOLDS: ThresholdConfig = {
  mq2_warning_adc: 600,
  mq2_critical_adc: 1200,
  mq135_warning_adc: 1600,
  mq135_critical_adc: 2400,
  hysteresis_adc: 50,
  sustained_duration_ms: 1000,
};

export class RiskEngine {
  private config: ThresholdConfig;
  private currentRisk: 'NORMAL' | 'WARNING' | 'CRITICAL' = 'NORMAL';
  private elevatedSince: number | null = null;

  constructor(config: Partial<ThresholdConfig> = {}) {
    this.config = { ...DEFAULT_THRESHOLDS, ...config };
  }

  public updateConfig(config: Partial<ThresholdConfig>) {
    this.config = { ...this.config, ...config };
  }

  public getConfig(): ThresholdConfig {
    return { ...this.config };
  }

  public evaluate(reading: NormalizedSensorReading): RiskEvaluation {
    const alerts: string[] = [];
    const reasons: string[] = [];

    const mq2 = reading.mq2_adc ?? 0;
    const mq135 = reading.mq135_adc ?? 0;

    // Check critical limits
    const mq2Critical = mq2 >= this.config.mq2_critical_adc;
    const mq135Critical = mq135 >= this.config.mq135_critical_adc;

    // Check warning limits
    const mq2Warning = mq2 >= this.config.mq2_warning_adc;
    const mq135Warning = mq135 >= this.config.mq135_warning_adc;

    let targetLevel: 'NORMAL' | 'WARNING' | 'CRITICAL' = 'NORMAL';

    if (mq2Critical || mq135Critical) {
      targetLevel = 'CRITICAL';
      if (mq2Critical) {
        alerts.push(`MQ-2 CRITICAL: ADC ${mq2} >= ${this.config.mq2_critical_adc}`);
        reasons.push(`Combustible gas/smoke response elevated beyond threshold`);
      }
      if (mq135Critical) {
        alerts.push(`MQ-135 CRITICAL: ADC ${mq135} >= ${this.config.mq135_critical_adc}`);
        reasons.push(`Air quality/hazardous gas response elevated beyond threshold`);
      }
    } else if (mq2Warning || mq135Warning) {
      targetLevel = 'WARNING';
      if (mq2Warning) {
        alerts.push(`MQ-2 WARNING: ADC ${mq2} >= ${this.config.mq2_warning_adc}`);
        reasons.push(`Combustible gas level approaching alert boundary`);
      }
      if (mq135Warning) {
        alerts.push(`MQ-135 WARNING: ADC ${mq135} >= ${this.config.mq135_warning_adc}`);
        reasons.push(`Air contaminants approaching alert boundary`);
      }
    }

    // Apply Hysteresis for de-escalation:
    // To drop from CRITICAL to WARNING: reading must drop below (critical - hysteresis)
    // To drop from WARNING to NORMAL: reading must drop below (warning - hysteresis)
    if (this.currentRisk === 'CRITICAL' && targetLevel !== 'CRITICAL') {
      const mq2Relieved = mq2 < (this.config.mq2_critical_adc - this.config.hysteresis_adc);
      const mq135Relieved = mq135 < (this.config.mq135_critical_adc - this.config.hysteresis_adc);
      if (!mq2Relieved || !mq135Relieved) {
        targetLevel = 'CRITICAL'; // Retain critical until hysteresis margin cleared
        alerts.push(`Holding CRITICAL state due to hysteresis buffer (${this.config.hysteresis_adc} ADC)`);
      }
    } else if (this.currentRisk === 'WARNING' && targetLevel === 'NORMAL') {
      const mq2Relieved = mq2 < (this.config.mq2_warning_adc - this.config.hysteresis_adc);
      const mq135Relieved = mq135 < (this.config.mq135_warning_adc - this.config.hysteresis_adc);
      if (!mq2Relieved || !mq135Relieved) {
        targetLevel = 'WARNING'; // Retain warning until hysteresis margin cleared
        alerts.push(`Holding WARNING state due to hysteresis buffer (${this.config.hysteresis_adc} ADC)`);
      }
    }

    this.currentRisk = targetLevel;
    const suggestedVentilation = targetLevel === 'CRITICAL' || targetLevel === 'WARNING';

    return {
      level: targetLevel,
      activeAlerts: alerts,
      reasons: reasons.length > 0 ? reasons : ['All sensor levels within configured baseline limits'],
      suggestedVentilation,
      timestamp: reading.timestamp,
    };
  }
}
