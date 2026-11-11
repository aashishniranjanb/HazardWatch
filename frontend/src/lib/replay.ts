import { NormalizedSensorReading } from './types';

export type ReplayCallback = (reading: NormalizedSensorReading, index: number, total: number) => void;

export class ReplayEngine {
  private readings: NormalizedSensorReading[] = [];
  private currentIndex: number = 0;
  private timer: NodeJS.Timeout | null = null;
  private speedMultiplier: number = 1.0;
  private isPlaying: boolean = false;
  private onTick: ReplayCallback | null = null;

  constructor(readings: NormalizedSensorReading[] = []) {
    this.readings = readings;
  }

  public load(readings: NormalizedSensorReading[]) {
    this.stop();
    this.readings = readings;
    this.currentIndex = 0;
  }

  public setCallback(callback: ReplayCallback) {
    this.onTick = callback;
  }

  public setSpeed(multiplier: number) {
    this.speedMultiplier = Math.max(0.1, multiplier);
    if (this.isPlaying) {
      this.pause();
      this.play();
    }
  }

  public play() {
    if (this.readings.length === 0 || this.isPlaying) return;
    this.isPlaying = true;

    const baseIntervalMs = 500; // Base rate between samples (500ms)
    const interval = Math.max(10, Math.floor(baseIntervalMs / this.speedMultiplier));

    this.timer = setInterval(() => {
      if (this.currentIndex >= this.readings.length) {
        this.stop();
        return;
      }

      const reading = this.readings[this.currentIndex];
      if (this.onTick) {
        this.onTick(reading, this.currentIndex, this.readings.length);
      }
      this.currentIndex++;
    }, interval);
  }

  public pause() {
    this.isPlaying = false;
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  public stop() {
    this.pause();
    this.currentIndex = 0;
  }

  public seek(index: number) {
    if (index >= 0 && index < this.readings.length) {
      this.currentIndex = index;
      if (this.onTick) {
        this.onTick(this.readings[this.currentIndex], this.currentIndex, this.readings.length);
      }
    }
  }

  public getStatus() {
    return {
      isPlaying: this.isPlaying,
      currentIndex: this.currentIndex,
      totalRows: this.readings.length,
      speed: this.speedMultiplier,
    };
  }
}
