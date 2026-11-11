import { NormalizedSensorReading } from './types';

export interface SerialParserCallbacks {
  onReading: (reading: NormalizedSensorReading) => void;
  onRawLine: (line: string) => void;
  onError: (error: string) => void;
  onStatusChange: (status: { connected: boolean; baudRate: number }) => void;
}

export class WebSerialManager {
  private port: any = null;
  private reader: any = null;
  private keepReading: boolean = false;
  private callbacks: SerialParserCallbacks;
  private buffer: string = '';
  private baudRate: number = 115200;

  constructor(callbacks: SerialParserCallbacks) {
    this.callbacks = callbacks;
  }

  public isSupported(): boolean {
    return typeof navigator !== 'undefined' && 'serial' in navigator;
  }

  public async connect(baudRate: number = 115200): Promise<void> {
    if (!this.isSupported()) {
      throw new Error('Web Serial API is not supported in this browser. Please use Google Chrome or Microsoft Edge.');
    }

    this.baudRate = baudRate;

    try {
      // Request a port and open a connection.
      // Filter can be added, or allow any serial device (CP210x, CH340, FTDI, etc.)
      // @ts-ignore
      this.port = await navigator.serial.requestPort();
      await this.port.open({ baudRate: this.baudRate });

      this.keepReading = true;
      this.callbacks.onStatusChange({ connected: true, baudRate: this.baudRate });
      this.readLoop();
    } catch (err: any) {
      this.callbacks.onError(err.message || 'Failed to open serial port');
      throw err;
    }
  }

  private async readLoop() {
    // @ts-ignore
    const textDecoder = new TextDecoderStream();
    const readableStreamClosed = this.port.readable.pipeTo(textDecoder.writable);
    this.reader = textDecoder.readable.getReader();

    try {
      while (this.keepReading) {
        const { value, done } = await this.reader.read();
        if (done) {
          break;
        }
        if (value) {
          this.processChunk(value);
        }
      }
    } catch (err: any) {
      if (this.keepReading) {
        this.callbacks.onError(`Serial read error: ${err.message || err}`);
      }
    } finally {
      this.reader.releaseLock();
    }
  }

  public processChunk(chunk: string) {
    this.buffer += chunk;
    const lines = this.buffer.split(/\r?\n/);
    // Keep the remainder (incomplete chunk) in buffer
    this.buffer = lines.pop() || '';

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed) continue;

      this.callbacks.onRawLine(trimmed);
      this.parseLine(trimmed);
    }
  }

  public parseLine(line: string) {
    try {
      const data = JSON.parse(line);
      // Validate expected ESP32 schema
      // Example: {"device":"ESP32_GAS_MONITOR","timestamp":1730000000,"mq2_adc":380,"mq135_adc":1520,"temperature":29.5,"humidity":65.0,"relay":false,"pump":false}
      const mq2_adc = typeof data.mq2_adc === 'number' ? data.mq2_adc : (typeof data.mq2 === 'number' ? data.mq2 : null);
      const mq135_adc = typeof data.mq135_adc === 'number' ? data.mq135_adc : (typeof data.mq135 === 'number' ? data.mq135 : null);
      const temperature = typeof data.temperature === 'number' ? data.temperature : (typeof data.temp === 'number' ? data.temp : null);
      const humidity = typeof data.humidity === 'number' ? data.humidity : (typeof data.hum === 'number' ? data.hum : null);
      const relay = Boolean(data.relay);
      const pump = Boolean(data.pump);

      const timestamp = typeof data.timestamp === 'number' 
        ? (data.timestamp > 10000000000 ? data.timestamp : data.timestamp * 1000) 
        : Date.now();

      const reading: NormalizedSensorReading = {
        timestamp,
        timeString: new Date(timestamp).toLocaleTimeString(),
        source: 'HARDWARE',
        mq2_adc,
        mq135_adc,
        temperature,
        humidity,
        relay,
        pump,
        rawJson: line,
      };

      this.callbacks.onReading(reading);
    } catch (err: any) {
      // Malformed JSON chunk or incomplete log line
      this.callbacks.onError(`Malformed JSON line skipped: ${line.substring(0, 50)}...`);
    }
  }

  public async disconnect(): Promise<void> {
    this.keepReading = false;
    try {
      if (this.reader) {
        await this.reader.cancel();
      }
      if (this.port) {
        await this.port.close();
      }
    } catch (err) {
      console.warn('Error during serial close', err);
    } finally {
      this.port = null;
      this.reader = null;
      this.callbacks.onStatusChange({ connected: false, baudRate: this.baudRate });
    }
  }
}
