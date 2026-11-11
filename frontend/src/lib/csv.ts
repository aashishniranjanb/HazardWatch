import Papa from 'papaparse';
import { NormalizedSensorReading, DatasetSummary } from './types';

export interface CSVParseResult {
  summary: DatasetSummary;
  readings: NormalizedSensorReading[];
  errors: string[];
}

export function parseCSVDataset(
  csvText: string,
  filename: string,
  displayName?: string
): CSVParseResult {
  const parsed = Papa.parse<Record<string, string>>(csvText, {
    header: true,
    skipEmptyLines: 'greedy',
    dynamicTyping: false, // Keep string for custom robust parsing
  });

  const columns = parsed.meta.fields || [];
  const errors: string[] = [];
  const readings: NormalizedSensorReading[] = [];
  const uniqueLabels = new Set<string | number>();
  let skippedRows = 0;

  // Detect dataset structure
  const lowerCols = columns.map(c => c.trim().toLowerCase());
  const hasMQ7 = lowerCols.some(c => c.includes('mq7'));
  const hasDHT11 = lowerCols.some(c => c.includes('temp') || c.includes('hum'));

  // Normalize column lookup
  const getCol = (row: Record<string, string>, ...aliases: string[]): string | undefined => {
    for (const alias of aliases) {
      const foundKey = Object.keys(row).find(k => k.trim().toLowerCase() === alias.toLowerCase());
      if (foundKey && row[foundKey] !== undefined && row[foundKey] !== null) {
        return row[foundKey].trim();
      }
    }
    return undefined;
  };

  const parseNum = (val: string | undefined): number | null => {
    if (!val || val === '' || val === 'null' || val === 'NaN') return null;
    const n = Number(val);
    return isNaN(n) ? null : n;
  };

  parsed.data.forEach((row, idx) => {
    // Basic validation: check date/time and primary ADC
    const dateStr = getCol(row, 'date', 'Date');
    const timeStr = getCol(row, 'time', 'Time');
    const mq2Val = parseNum(getCol(row, 'mq2_adc', 'adc', 'ADC', 'mq2'));
    const mq135Val = parseNum(getCol(row, 'mq135_adc', 'mq135'));
    const mq7Val = parseNum(getCol(row, 'mq7_adc', 'mq7'));

    // If row doesn't have at least one valid gas sensor ADC, treat as malformed
    if (mq2Val === null && mq135Val === null && mq7Val === null) {
      skippedRows++;
      if (errors.length < 10) {
        errors.push(`Row ${idx + 1}: Missing numerical sensor values (${JSON.stringify(row)})`);
      }
      return;
    }

    // Parse timestamp
    let timestamp = Date.now();
    let displayTime = timeStr || new Date().toLocaleTimeString();

    if (dateStr && timeStr) {
      const parsedTs = Date.parse(`${dateStr}T${timeStr}`);
      if (!isNaN(parsedTs)) {
        timestamp = parsedTs;
      }
    } else if (timeStr) {
      // If only time, combine with dummy reference date
      const parsedTs = Date.parse(`2026-01-01T${timeStr}`);
      if (!isNaN(parsedTs)) {
        timestamp = parsedTs;
      }
    }

    // Label handling
    const rawLabel = getCol(row, 'label', 'Label', 'class');
    if (rawLabel !== undefined && rawLabel !== '') {
      uniqueLabels.add(rawLabel);
    }

    // Secondary metrics
    const mq2_voltage = parseNum(getCol(row, 'voltage', 'Voltage', 'mq2_volt'));
    const mq2_rs = parseNum(getCol(row, 'mq2_rs', 'rs', 'Rs'));
    const mq2_ratio = parseNum(getCol(row, 'mq2_ratio', 'ratio', 'Ratio'));
    const mq2_ppm = parseNum(getCol(row, 'mq2_ppm', 'ppm', 'PPM'));

    const mq135_rs = parseNum(getCol(row, 'mq135_rs'));
    const mq135_ratio = parseNum(getCol(row, 'mq135_ratio'));
    const mq135_ppm = parseNum(getCol(row, 'mq135_ppm'));

    const mq7_rs = parseNum(getCol(row, 'mq7_rs'));
    const mq7_ratio = parseNum(getCol(row, 'mq7_ratio'));
    const mq7_ppm = parseNum(getCol(row, 'mq7_ppm'));

    readings.push({
      timestamp,
      timeString: displayTime,
      source: 'HISTORICAL_REPLAY',
      mq2_adc: mq2Val,
      mq2_voltage,
      mq2_rs,
      mq2_ratio,
      mq2_ppm,
      mq135_adc: mq135Val,
      mq135_rs,
      mq135_ratio,
      mq135_ppm,
      mq7_adc: mq7Val,
      mq7_rs,
      mq7_ratio,
      mq7_ppm,
      temperature: null, // Historical datasets do NOT have DHT11
      humidity: null,    // Do not fabricate measurements!
      relay: false,
      pump: false,
      label: rawLabel !== undefined ? rawLabel : null,
    });
  });

  // Sort readings chronologically if valid timestamps exist
  readings.sort((a, b) => a.timestamp - b.timestamp);

  const sampleRows: Record<string, string | number>[] = readings.slice(0, 10).map(r => ({
    time: r.timeString,
    mq2_adc: r.mq2_adc ?? '-',
    mq135_adc: r.mq135_adc ?? '-',
    mq7_adc: r.mq7_adc ?? '-',
    temp: r.temperature ?? 'N/A',
    humidity: r.humidity ?? 'N/A',
    label: r.label ?? '-',
  }));

  const summary: DatasetSummary = {
    id: filename.replace(/\.[^/.]+$/, ''),
    name: displayName || filename,
    filename,
    totalRows: parsed.data.length,
    validRows: readings.length,
    skippedRows,
    columns,
    hasMQ7,
    hasDHT11: false, // Explicitly false for all historical datasets
    uniqueLabels: Array.from(uniqueLabels).sort(),
    timeRange: readings.length > 0 ? {
      start: readings[0].timeString,
      end: readings[readings.length - 1].timeString,
    } : undefined,
    sampleRows,
  };

  return {
    summary,
    readings,
    errors,
  };
}
