import { NormalizedSensorReading } from './types';

export interface SyntheticScenario {
  id: string;
  name: string;
  description: string;
  generateReading: (step: number, prev: NormalizedSensorReading) => NormalizedSensorReading;
}

export const SYNTHETIC_SCENARIOS: SyntheticScenario[] = [
  {
    id: 'normal',
    name: 'Normal Clean Industrial Ambient',
    description: 'Sensors remain at low nominal baselines with slight realistic ADC jitter.',
    generateReading: (step, prev) => {
      const mq2 = Math.floor(350 + Math.random() * 40);
      const mq135 = Math.floor(1400 + Math.random() * 50);
      return {
        timestamp: Date.now(),
        timeString: new Date().toLocaleTimeString(),
        source: 'SYNTHETIC',
        mq2_adc: mq2,
        mq135_adc: mq135,
        temperature: 25.2 + Math.sin(step / 10) * 0.4,
        humidity: 55 + Math.cos(step / 10) * 1.5,
        relay: false,
        pump: false,
      };
    },
  },
  {
    id: 'gas_spike',
    name: 'Sudden Flammable Gas Spike (MQ-2)',
    description: 'Rapid elevation of MQ-2 ADC simulating LPG/methane canister breach.',
    generateReading: (step, prev) => {
      // Step goes from baseline up to 1800 ADC quickly
      const progress = Math.min(step / 15, 1);
      const mq2 = Math.floor(380 + progress * 1450 + (Math.random() * 60 - 30));
      const mq135 = Math.floor(1450 + progress * 400 + (Math.random() * 30));
      return {
        timestamp: Date.now(),
        timeString: new Date().toLocaleTimeString(),
        source: 'SYNTHETIC',
        mq2_adc: mq2,
        mq135_adc: mq135,
        temperature: 26.0 + progress * 1.5,
        humidity: 53 - progress * 4,
        relay: mq2 > 600,
        pump: mq2 > 600,
      };
    },
  },
  {
    id: 'air_quality_degradation',
    name: 'Gradual Air Contamination (MQ-135)',
    description: 'Slow accumulation of harmful airborne gases (ammonia/benzene/smoke).',
    generateReading: (step, prev) => {
      const progress = Math.min(step / 30, 1);
      const mq135 = Math.floor(1500 + progress * 1300 + (Math.random() * 40 - 20));
      const mq2 = Math.floor(400 + progress * 300 + (Math.random() * 30));
      return {
        timestamp: Date.now(),
        timeString: new Date().toLocaleTimeString(),
        source: 'SYNTHETIC',
        mq2_adc: mq2,
        mq135_adc: mq135,
        temperature: 27.1,
        humidity: 62.0,
        relay: mq135 > 1600,
        pump: mq135 > 1600,
      };
    },
  },
  {
    id: 'gas_recovery',
    name: 'Ventilation Clearing & Recovery',
    description: 'Simulates active air pump ventilation bringing gas levels back below threshold.',
    generateReading: (step, prev) => {
      const decay = Math.exp(-step / 12);
      const mq2 = Math.floor(360 + decay * 1100 + (Math.random() * 20));
      const mq135 = Math.floor(1450 + decay * 900 + (Math.random() * 20));
      return {
        timestamp: Date.now(),
        timeString: new Date().toLocaleTimeString(),
        source: 'SYNTHETIC',
        mq2_adc: mq2,
        mq135_adc: mq135,
        temperature: 25.5,
        humidity: 56.0,
        relay: mq2 > 600 || mq135 > 1600,
        pump: mq2 > 600 || mq135 > 1600,
      };
    },
  },
];
