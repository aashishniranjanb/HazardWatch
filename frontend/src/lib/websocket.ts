import { NormalizedSensorReading } from './types';

export class WebSocketClient {
  private url: string;
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;
  private onReadingCallback: ((reading: NormalizedSensorReading) => void) | null = null;
  private onStatusChangeCallback: ((connected: boolean) => void) | null = null;
  private shouldConnect = false;

  constructor(url: string = 'ws://localhost:8000/ws/sensors') {
    this.url = url;
  }

  public setCallbacks(
    onReading: (reading: NormalizedSensorReading) => void,
    onStatusChange: (connected: boolean) => void
  ) {
    this.onReadingCallback = onReading;
    this.onStatusChangeCallback = onStatusChange;
  }

  public connect(customUrl?: string) {
    if (customUrl) this.url = customUrl;
    this.shouldConnect = true;

    try {
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        this.reconnectAttempts = 0;
        if (this.onStatusChangeCallback) this.onStatusChangeCallback(true);
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const reading: NormalizedSensorReading = {
            timestamp: data.timestamp ? (data.timestamp > 10000000000 ? data.timestamp : data.timestamp * 1000) : Date.now(),
            timeString: new Date().toLocaleTimeString(),
            source: 'HARDWARE',
            mq2_adc: data.mq2_adc ?? null,
            mq135_adc: data.mq135_adc ?? null,
            temperature: data.temperature ?? null,
            humidity: data.humidity ?? null,
            relay: Boolean(data.relay),
            pump: Boolean(data.pump),
            rawJson: event.data,
          };
          if (this.onReadingCallback) this.onReadingCallback(reading);
        } catch (e) {
          console.warn('Malformed websocket payload', event.data);
        }
      };

      this.ws.onclose = () => {
        if (this.onStatusChangeCallback) this.onStatusChangeCallback(false);
        if (this.shouldConnect && this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;
          setTimeout(() => this.connect(), this.reconnectDelay * this.reconnectAttempts);
        }
      };

      this.ws.onerror = (err) => {
        console.error('WebSocket error:', err);
      };
    } catch (err) {
      console.error('WS Connect error:', err);
      if (this.onStatusChangeCallback) this.onStatusChangeCallback(false);
    }
  }

  public disconnect() {
    this.shouldConnect = false;
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    if (this.onStatusChangeCallback) this.onStatusChangeCallback(false);
  }
}
